"""CP-SAT maintenance scheduling service."""

from datetime import datetime, timedelta, timezone
from math import ceil
import time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import (
    AVAILABILITY_REWARD_WEIGHT,
    CRITICAL_DEADLINE_HOURS,
    CRITICAL_DAY_WINDOW,
    CRITICAL_DAY_WINDOW_PENALTY,
    CREW_IDLE_REWARD_WEIGHT,
    EARLY_SERVICE_WEIGHT,
    MAINTENANCE_COST_PENALTY_WEIGHT,
    NIGHT_WINDOW_END_HOUR,
    NIGHT_WINDOW_START_HOUR,
    NO_ALTERNATE_TRACK_PENALTY,
    PEAK_OVERLAP_PENALTY_WEIGHT,
    PEAK_PASSENGER_WINDOWS,
    PRIORITY_REWARD_WEIGHT,
    TRAIN_DELAY_PENALTY_WEIGHT,
)
from backend.app.core.model_registry import ModelBundle
from backend.app.database.models import (
    AuditLog,
    MaintenanceRequest,
    OptimizedSchedule,
    OptimizationRun,
    PredictionRecord,
)
from backend.app.database.schemas import (
    AssetCreate,
    OptimizationMetrics,
    OptimizationRequest,
    OptimizationResult,
    ScheduleItem,
)
from backend.app.services.asset_service import upsert_asset
from backend.app.services.prediction_service import predict_priority_values


def _planning_start(requested_start: datetime | None) -> datetime:
    if requested_start is None:
        now = datetime.now(timezone.utc)
        start = now.replace(minute=0, second=0, microsecond=0)
        return start if start == now else start + timedelta(hours=1)
    if requested_start.tzinfo is None:
        requested_start = requested_start.replace(tzinfo=timezone.utc)
    return requested_start.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


def _inside_night_window(value: datetime) -> bool:
    return value.hour >= NIGHT_WINDOW_START_HOUR or value.hour < NIGHT_WINDOW_END_HOUR


def _inside_critical_window(value: datetime) -> bool:
    start_hour, end_hour = CRITICAL_DAY_WINDOW
    return start_hour <= value.hour < end_hour


def _window_candidates(
    plan_start: datetime,
    duration_hours: int,
    horizon_hours: int,
    is_critical: bool,
) -> dict[int, tuple[int, int]]:
    """Map feasible start offsets to (peak-overlap hours, daytime-window flag)."""
    candidates: dict[int, tuple[int, int]] = {}
    peak_start_hours = tuple(PEAK_PASSENGER_WINDOWS)
    for start_offset in range(max(0, horizon_hours - duration_hours + 1)):
        occupied = [
            plan_start + timedelta(hours=offset)
            for offset in range(start_offset, start_offset + duration_hours)
        ]
        if all(_inside_night_window(hour) for hour in occupied):
            daytime_window = 0
        elif is_critical and all(_inside_critical_window(hour) for hour in occupied):
            daytime_window = 1
        else:
            continue
        peak_overlap = sum(
            any(begin <= hour.hour < end for begin, end in peak_start_hours)
            for hour in occupied
        )
        candidates[start_offset] = (peak_overlap, daytime_window)
    return candidates


def optimize_maintenance(
    db: Session,
    request: OptimizationRequest,
    bundle: ModelBundle,
) -> OptimizationResult:
    """Predict request priorities, solve the CP-SAT plan, and persist the run."""
    try:
        from ortools.sat.python import cp_model
    except (ImportError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OR-Tools CP-SAT is unavailable in this runtime.",
        ) from exc

    assets: list[AssetCreate] = request.assets
    predictions = predict_priority_values(assets, bundle)
    plan_start = _planning_start(request.planning_start)
    horizon_hours = request.horizon_days * 24
    threshold = request.priority_threshold
    critical_threshold = request.critical_priority_threshold
    eligible = [
        (asset, priority)
        for asset, priority in zip(assets, predictions, strict=True)
        if priority > threshold
    ]

    if critical_threshold < threshold:
        raise HTTPException(
            status_code=422,
            detail="critical_priority_threshold must be greater than or equal to priority_threshold.",
        )

    solve_started = time.perf_counter()
    solver_status_name = "NO_REQUESTS"
    solver_score = 0.0
    task_states: list[dict[str, Any]] = []
    solver_seconds = 0.0

    if eligible:
        model = cp_model.CpModel()
        unassigned_start = horizon_hours + 1
        intervals = []
        demands = []
        track_intervals: dict[str, list[Any]] = {}
        objective_terms = []

        for task_index, (asset, priority_score) in enumerate(eligible):
            duration = max(1, ceil(asset.maintenance_duration))
            critical = priority_score >= critical_threshold
            candidate_metadata = _window_candidates(
                plan_start, duration, horizon_hours, critical
            )
            start_values = sorted(candidate_metadata)
            start = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(sorted({unassigned_start, *start_values})),
                f"start_{task_index}",
            )
            end = model.NewIntVar(0, horizon_hours, f"end_{task_index}")
            scheduled = model.NewBoolVar(f"scheduled_{task_index}")
            peak_hours = model.NewIntVar(0, duration, f"peak_hours_{task_index}")
            daytime_window = model.NewBoolVar(f"daytime_window_{task_index}")
            allowed_tuples = {(unassigned_start, 0, 0)}
            allowed_tuples.update(
                (offset, peak_count, daytime)
                for offset, (peak_count, daytime) in candidate_metadata.items()
            )
            model.AddAllowedAssignments(
                [start, peak_hours, daytime_window], sorted(allowed_tuples)
            )

            interval = model.NewOptionalIntervalVar(
                start, duration, end, scheduled, f"maintenance_{task_index}"
            )
            intervals.append(interval)
            demands.append(1)
            track_group = asset.track_id or asset.station
            track_intervals.setdefault(track_group, []).append(interval)
            model.Add(start == unassigned_start).OnlyEnforceIf(scheduled.Not())
            model.Add(end == 0).OnlyEnforceIf(scheduled.Not())
            model.Add(peak_hours == 0).OnlyEnforceIf(scheduled.Not())
            model.Add(daytime_window == 0).OnlyEnforceIf(scheduled.Not())
            if critical:
                model.Add(scheduled == 1)
                model.Add(start < CRITICAL_DEADLINE_HOURS)
            if asset.crew_available == 0:
                model.Add(scheduled == 0)

            alternate_available = asset.nearby_alternate_track
            estimated_train_impacts = ceil(asset.train_frequency * duration / 24)
            passenger_peak_multiplier = 2 if asset.passenger_peak else 1
            objective_terms.extend(
                [
                    AVAILABILITY_REWARD_WEIGHT * scheduled,
                    PRIORITY_REWARD_WEIGHT * int(round(priority_score)) * scheduled,
                    EARLY_SERVICE_WEIGHT
                    * int(round(priority_score))
                    * (horizon_hours * scheduled - end),
                    CREW_IDLE_REWARD_WEIGHT * duration * scheduled,
                    -TRAIN_DELAY_PENALTY_WEIGHT * estimated_train_impacts * scheduled,
                    -MAINTENANCE_COST_PENALTY_WEIGHT * duration * scheduled,
                    -(0 if alternate_available else NO_ALTERNATE_TRACK_PENALTY)
                    * scheduled,
                    -PEAK_OVERLAP_PENALTY_WEIGHT
                    * passenger_peak_multiplier
                    * peak_hours,
                    -CRITICAL_DAY_WINDOW_PENALTY * daytime_window,
                ]
            )
            task_states.append(
                {
                    "asset": asset,
                    "priority": float(priority_score),
                    "duration": duration,
                    "estimated_train_impacts": int(estimated_train_impacts),
                    "scheduled": scheduled,
                    "start": start,
                    "end": end,
                    "peak_hours": peak_hours,
                    "daytime_window": daytime_window,
                }
            )

        for intervals_for_track in track_intervals.values():
            if len(intervals_for_track) > 1:
                model.AddNoOverlap(intervals_for_track)
        model.AddCumulative(intervals, demands, request.available_crews)
        model.Maximize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = settings.solver_time_limit_seconds
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 42
        solver_status = solver.Solve(model)
        solver_seconds = time.perf_counter() - solve_started
        solver_status_name = solver.StatusName(solver_status)
        if solver_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            if solver_status == cp_model.INFEASIBLE:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "No feasible plan satisfies critical deadlines, track access, "
                        "crew capacity, and maintenance windows. Review operational settings."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"CP-SAT did not find a feasible plan before the time limit "
                    f"(status: {solver_status_name})."
                ),
            )
        solver_score = float(solver.ObjectiveValue())

        for task in task_states:
            task["is_scheduled"] = solver.Value(task["scheduled"]) == 1
            if task["is_scheduled"]:
                task["start_offset"] = solver.Value(task["start"])
                task["end_offset"] = solver.Value(task["end"])
                task["peak_overlap"] = solver.Value(task["peak_hours"])
                task["daytime_window"] = solver.Value(task["daytime_window"])
            else:
                task.update(
                    start_offset=None,
                    end_offset=None,
                    peak_overlap=0,
                    daytime_window=0,
                )
    else:
        solver_seconds = time.perf_counter() - solve_started

    scheduled_tasks = sorted(
        (task for task in task_states if task["is_scheduled"]),
        key=lambda task: (task["start_offset"], -task["priority"], task["asset"].asset_id),
    )
    crew_free_at = [0] * request.available_crews
    for task in scheduled_tasks:
        available = [
            crew_index
            for crew_index, free_at in enumerate(crew_free_at)
            if free_at <= task["start_offset"]
        ]
        if not available:
            raise RuntimeError("CP-SAT crew capacity could not be mapped to crew identifiers.")
        crew_index = available[0]
        crew_free_at[crew_index] = task["end_offset"]
        task["assigned_crew"] = f"Crew-{crew_index + 1:02d}"

    schedule_items: list[ScheduleItem] = []
    for task in task_states:
        asset = task["asset"]
        scheduled = task["is_scheduled"]
        if scheduled:
            start_time = plan_start + timedelta(hours=task["start_offset"])
            end_time = plan_start + timedelta(hours=task["end_offset"])
            priority_int = int(round(task["priority"]))
            score = (
                AVAILABILITY_REWARD_WEIGHT
                + PRIORITY_REWARD_WEIGHT * priority_int
                + EARLY_SERVICE_WEIGHT * priority_int * (horizon_hours - task["end_offset"])
                + (CREW_IDLE_REWARD_WEIGHT - MAINTENANCE_COST_PENALTY_WEIGHT)
                * task["duration"]
                - TRAIN_DELAY_PENALTY_WEIGHT * task["estimated_train_impacts"]
                - (0 if asset.nearby_alternate_track else NO_ALTERNATE_TRACK_PENALTY)
                - PEAK_OVERLAP_PENALTY_WEIGHT
                * (2 if asset.passenger_peak else 1)
                * task["peak_overlap"]
                - CRITICAL_DAY_WINDOW_PENALTY * task["daytime_window"]
            )
            status_text = "Scheduled"
            assigned_crew = task["assigned_crew"]
        else:
            start_time = None
            end_time = None
            score = 0
            status_text = "Not scheduled within horizon/constraints"
            assigned_crew = None
        schedule_items.append(
            ScheduleItem(
                maintenance_id=f"MNT-{asset.asset_id}",
                asset_id=asset.asset_id,
                asset_type=asset.asset_type,
                station=asset.station,
                track_id=asset.track_id,
                start_time=start_time,
                end_time=end_time,
                assigned_crew=assigned_crew,
                predicted_priority_score=task["priority"],
                optimization_score=int(score),
                status=status_text,
                duration_hours=task["duration"],
            )
        )

    request_count = len(eligible)
    scheduled_count = len(scheduled_tasks)
    scheduled_hours = sum(task["duration"] for task in scheduled_tasks)
    average_delay = (
        sum(task["start_offset"] for task in scheduled_tasks) / scheduled_count
        if scheduled_count
        else 0.0
    )
    total_assets = len(assets)
    asset_availability = (
        100.0 * (1.0 - scheduled_hours / (total_assets * horizon_hours))
        if total_assets and horizon_hours
        else 0.0
    )
    crew_utilization = (
        100.0 * scheduled_hours / (request.available_crews * horizon_hours)
        if request.available_crews and horizon_hours
        else 0.0
    )
    completion_rate = 100.0 * scheduled_count / request_count if request_count else 0.0
    train_impacts = sum(task["estimated_train_impacts"] for task in scheduled_tasks)

    run = OptimizationRun(
        solver_status=solver_status_name,
        objective_score=solver_score,
        request_count=request_count,
        scheduled_count=scheduled_count,
        solver_seconds=solver_seconds,
    )
    try:
        for asset, priority in zip(assets, predictions, strict=True):
            upsert_asset(db, asset)
            db.add(
                PredictionRecord(
                    asset_id=asset.asset_id,
                    predicted_priority_score=priority,
                    predicted_failure_probability=asset.predicted_failure_probability,
                    model_version=bundle.model_version,
                )
            )
        db.add(run)
        db.flush()
        requests_by_asset = {}
        for task in task_states:
            asset = task["asset"]
            maintenance_request = MaintenanceRequest(
                asset_id=asset.asset_id,
                priority=task["priority"],
                predicted_failure_probability=asset.predicted_failure_probability,
                maintenance_duration=asset.maintenance_duration,
                preferred_window=(
                    "Overnight 20:00-08:00; critical daytime 00:00-12:00 allowed"
                    if task["priority"] >= critical_threshold
                    else "Overnight 20:00-08:00"
                ),
                crew_required=1,
                status="scheduled" if task["is_scheduled"] else "pending",
            )
            db.add(maintenance_request)
            requests_by_asset[asset.asset_id] = maintenance_request
        db.flush()

        for item in schedule_items:
            maintenance_request = requests_by_asset[item.asset_id]
            db.add(
                OptimizedSchedule(
                    run_id=run.run_id,
                    request_id=maintenance_request.request_id,
                    maintenance_start=item.start_time,
                    maintenance_end=item.end_time,
                    assigned_crew=item.assigned_crew,
                    optimization_score=item.optimization_score,
                    status="scheduled" if item.status == "Scheduled" else "not_scheduled",
                )
            )
        db.add(
            AuditLog(
                action="optimization.created",
                entity="optimization_run",
                entity_id=str(run.run_id),
                details=(
                    f"solver_status={solver_status_name}; "
                    f"requests={request_count}; scheduled={scheduled_count}"
                ),
            )
        )
        db.commit()
        db.refresh(run)
    except Exception:
        db.rollback()
        raise

    metrics = OptimizationMetrics(
        total_assets_scheduled=scheduled_count,
        request_count=request_count,
        average_delay_hours=float(average_delay),
        asset_availability_percent=float(asset_availability),
        crew_utilization_percent=float(crew_utilization),
        maintenance_completion_percent=float(completion_rate),
        estimated_train_impacts=int(train_impacts),
        optimization_score=solver_score,
        solver_status=solver_status_name,
        solver_seconds=float(solver_seconds),
    )
    schedule_items.sort(
        key=lambda item: (item.start_time is None, item.start_time or plan_start)
    )
    return OptimizationResult(run_id=run.id, schedule=schedule_items, metrics=metrics)
