"""RailOpt AI operations dashboard backed by the existing FastAPI service."""

from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import ApiClient, ApiError


ASSET_TYPES = ("Bridge", "OHE", "Signal", "Switch", "Track")
ZONES = ("Central", "East", "North", "South", "West")
ASSET_REQUEST_FIELDS = (
    "asset_id",
    "asset_type",
    "zone",
    "station",
    "track_id",
    "installation_date",
    "asset_age_years",
    "last_maintenance_days",
    "defect_count",
    "defect_severity",
    "inspection_score",
    "train_frequency",
    "average_speed",
    "weather",
    "temperature",
    "rainfall",
    "axle_load",
    "crew_available",
    "maintenance_duration",
    "passenger_peak",
    "nearby_alternate_track",
    "previous_failures",
    "predicted_failure_probability",
    "status",
)

NAV_ITEMS = (
    "Dashboard",
    "Railway Assets",
    "Predictions & Risk",
    "Block Planning",
    "System Status",
)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: light;
            --rail-navy: #17365d;
            --rail-blue: #2463a6;
            --rail-blue-pale: #eef5fc;
            --rail-ink: #1d2b3a;
            --rail-muted: #66778a;
            --rail-border: #e1e8f0;
            --rail-green: #21845b;
            --rail-amber: #a96508;
            --rail-red: #b83a43;
        }
        .stApp {
            background: #f7f9fc;
            color: var(--rail-ink);
        }
        [data-testid="stHeader"] { background: rgba(247, 249, 252, .96); }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--rail-border);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
        .block-container { max-width: 1480px; padding-top: 2rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--rail-navy); letter-spacing: -0.025em; }
        h1 { font-size: clamp(1.8rem, 3vw, 2.35rem); }
        h2 { font-size: 1.4rem; }
        p, label, .stCaption { color: var(--rail-ink); }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--rail-border);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 3px 12px rgba(26, 47, 74, .045);
        }
        [data-testid="stMetricLabel"] { color: var(--rail-muted); }
        [data-testid="stMetricValue"] { color: var(--rail-navy); font-weight: 700; }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--rail-border);
            border-radius: 12px;
            overflow: hidden;
        }
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            border-color: var(--rail-border);
            border-radius: 12px;
        }
        .brand-lockup { padding: .3rem .2rem 1rem; }
        .brand-mark {
            display: inline-flex; align-items: center; justify-content: center;
            width: 40px; height: 40px; border-radius: 12px;
            color: white; background: var(--rail-navy);
            font-weight: 800; font-size: 1rem; margin-right: .65rem;
        }
        .brand-name { color: var(--rail-navy); font-size: 1.18rem; font-weight: 800; }
        .brand-sub { color: var(--rail-muted); font-size: .76rem; margin-top: .3rem; }
        .page-kicker {
            color: var(--rail-blue); text-transform: uppercase; letter-spacing: .12em;
            font-size: .73rem; font-weight: 800; margin-bottom: .25rem;
        }
        .page-subtitle { color: var(--rail-muted); max-width: 850px; margin-top: -.35rem; }
        .panel {
            background: #ffffff; border: 1px solid var(--rail-border);
            border-radius: 14px; padding: 1rem 1.15rem;
            box-shadow: 0 3px 12px rgba(26, 47, 74, .035);
            height: 100%;
        }
        .panel-label { color: var(--rail-muted); font-size: .79rem; font-weight: 650; }
        .panel-value { color: var(--rail-navy); font-size: 1.3rem; font-weight: 750; margin-top: .38rem; }
        .panel-note { color: var(--rail-muted); font-size: .78rem; margin-top: .3rem; }
        .status-pill {
            display: inline-flex; align-items: center; gap: .42rem;
            padding: .25rem .62rem; border-radius: 999px; font-size: .77rem;
            font-weight: 700; border: 1px solid transparent;
        }
        .status-pill::before {
            content: ""; width: .45rem; height: .45rem; border-radius: 50%;
            background: currentColor;
        }
        .status-ok { color: var(--rail-green); background: #edf8f2; border-color: #d3eddf; }
        .status-warn { color: var(--rail-amber); background: #fff6e8; border-color: #f5e1ba; }
        .status-bad { color: var(--rail-red); background: #fff0f0; border-color: #f3d4d5; }
        .status-neutral { color: #526579; background: #f0f4f8; border-color: #e0e7ef; }
        .section-caption { color: var(--rail-muted); margin-top: -.55rem; margin-bottom: 1rem; }
        .callout {
            border-left: 3px solid var(--rail-blue); background: var(--rail-blue-pale);
            border-radius: 0 9px 9px 0; color: #334b64;
            padding: .7rem .9rem; font-size: .88rem;
        }
        .stButton > button[kind="primary"] {
            background: var(--rail-blue); border-color: var(--rail-blue);
            border-radius: 9px; font-weight: 700; padding: .55rem 1rem;
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--rail-navy); border-color: var(--rail-navy);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_page_header(title: str, subtitle: str, kicker: str) -> None:
    st.markdown(f'<div class="page-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)


def status_pill(label: str, state: str) -> str:
    normalized = state.strip().lower()
    if normalized in {"healthy", "connected", "loaded", "optimal", "scheduled", "success"}:
        style = "status-ok"
    elif normalized in {"degraded", "warning", "partial", "no_requests"}:
        style = "status-warn"
    elif normalized in {"unhealthy", "disconnected", "failed", "error"}:
        style = "status-bad"
    else:
        style = "status-neutral"
    return (
        f'<span class="status-pill {style}">{escape(label)}: '
        f"{escape(state.replace('_', ' ').title())}</span>"
    )


def panel(label: str, value: str, note: str = "") -> None:
    st.markdown(
        '<div class="panel">'
        f'<div class="panel-label">{escape(label)}</div>'
        f'<div class="panel-value">{escape(value)}</div>'
        f'<div class="panel-note">{escape(note)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def data_section(data: Any) -> Any:
    if not isinstance(data, dict):
        raise ApiError("The backend returned an unexpected data format.")
    return data


def fetch_health(client: ApiClient) -> dict[str, Any]:
    return data_section(client.get("/health"))


def fetch_summary(client: ApiClient) -> dict[str, Any]:
    return data_section(client.get("/dashboard/summary"))


def fetch_charts(client: ApiClient) -> dict[str, Any]:
    return data_section(client.get("/dashboard/charts"))


def fetch_assets(
    client: ApiClient,
    *,
    limit: int = 100,
    offset: int = 0,
    asset_type: str | None = None,
    zone: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if asset_type:
        params["asset_type"] = asset_type
    if zone:
        params["zone"] = zone
    return data_section(client.get("/assets", params=params))


def asset_request_payload(asset: dict[str, Any]) -> dict[str, Any]:
    return {key: asset[key] for key in ASSET_REQUEST_FIELDS if key in asset}


def asset_options(client: ApiClient) -> list[dict[str, Any]]:
    response = fetch_assets(client, limit=500)
    items = response.get("items", [])
    if not isinstance(items, list):
        raise ApiError("The backend returned an invalid asset list.")
    return [asset for asset in items if isinstance(asset, dict)]


def asset_label(asset: dict[str, Any]) -> str:
    return " · ".join(
        str(value)
        for value in (
            asset.get("asset_id", ""),
            asset.get("asset_type", ""),
            asset.get("station", ""),
        )
        if value
    )


def render_sidebar(client: ApiClient) -> str:
    with st.sidebar:
        st.markdown(
            '<div class="brand-lockup"><span class="brand-mark">R</span>'
            '<span class="brand-name">RailOpt AI</span>'
            '<div class="brand-sub">Railway asset & block operations</div></div>',
            unsafe_allow_html=True,
        )
        page = st.radio("WORKSPACE", NAV_ITEMS, label_visibility="visible")
        st.divider()
        try:
            health = fetch_health(client)
            st.markdown(status_pill("Backend", str(health.get("status", "unknown"))), unsafe_allow_html=True)
            db_status = "connected" if health.get("database_connected") else "disconnected"
            st.caption(f"Database · {db_status.title()}")
        except ApiError:
            st.markdown(status_pill("Backend", "unavailable"), unsafe_allow_html=True)
            st.caption("Start FastAPI to load live operations data.")
        st.caption("Data and schedules are provided by the connected RailOpt AI API.")
    return page


def render_dashboard(client: ApiClient) -> None:
    show_page_header(
        "Operations dashboard",
        "A live overview of railway asset condition, model predictions and block-planning activity.",
        "Railway operations · overview",
    )

    try:
        health = fetch_health(client)
        status = str(health.get("status", "unknown"))
        db_status = "connected" if health.get("database_connected") else "disconnected"
        model_status = "loaded" if health.get("model_loaded") else "unavailable"
        st.markdown(
            " ".join(
                [
                    status_pill("API", status),
                    status_pill("PostgreSQL", db_status),
                    status_pill("ML model", model_status),
                ]
            ),
            unsafe_allow_html=True,
        )
    except ApiError as exc:
        st.error(f"System health could not be loaded. {exc}")

    try:
        summary = fetch_summary(client)
    except ApiError as exc:
        st.error(f"Dashboard summary is unavailable. {exc}")
        summary = None

    if summary is not None:
        st.subheader("Operational indicators")
        first_kpi_row = st.columns(2)
        with first_kpi_row[0]:
            panel("Total assets", f"{summary.get('total_assets', 0):,}", "Registered in the backend")
        with first_kpi_row[1]:
            panel(
                "Predictions",
                f"{summary.get('predictions_recorded', 0):,}",
                "Recorded model results",
            )

        second_kpi_row = st.columns(2)
        with second_kpi_row[0]:
            panel(
                "High priority",
                f"{summary.get('high_priority_assets', 0):,}",
                "Score threshold 75+",
            )
        mean_score = summary.get("mean_priority_score")
        with second_kpi_row[1]:
            panel(
                "Mean priority score",
                f"{float(mean_score):.1f}" if mean_score is not None else "—",
                "Mean recorded score",
            )
        run_status = summary.get("latest_optimization_status")
        scheduled_count = summary.get("latest_scheduled_count")
        latest_value = str(run_status).replace("_", " ").title() if run_status else "No run recorded"
        panel_note = (
            f"{scheduled_count} scheduled in the latest reported run"
            if run_status
            else "No optimization run is currently recorded"
        )
        st.markdown("#### Latest optimization summary")
        panel("Solver status", latest_value, panel_note)

    try:
        charts = fetch_charts(client)
    except ApiError as exc:
        st.error(f"Dashboard charts are unavailable. {exc}")
        return

    st.subheader("Asset and prediction overview")
    chart_left, chart_right = st.columns(2)
    by_type = charts.get("assets_by_type") or []
    if by_type:
        chart_left.plotly_chart(
            px.bar(
                pd.DataFrame(by_type),
                x="label",
                y="value",
                title="Assets by type",
                labels={"label": "Asset type", "value": "Assets"},
                color_discrete_sequence=["#2463a6"],
                template="plotly_white",
            ).update_layout(
                height=340,
                margin=dict(l=12, r=12, t=55, b=12),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color="#334b64",
            ),
            width="stretch",
        )
    else:
        chart_left.info("No asset-type aggregates are available yet.")

    by_zone = charts.get("assets_by_zone") or []
    if by_zone:
        chart_right.plotly_chart(
            px.bar(
                pd.DataFrame(by_zone),
                x="label",
                y="value",
                title="Assets by zone",
                labels={"label": "Zone", "value": "Assets"},
                color_discrete_sequence=["#3b82b8"],
                template="plotly_white",
            ).update_layout(
                height=340,
                margin=dict(l=12, r=12, t=55, b=12),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color="#334b64",
            ),
            width="stretch",
        )
    else:
        chart_right.info("No zone aggregates are available yet.")

    st.caption(
        "All figures above are backend-reported aggregates. Asset availability and "
        "crew-utilization metrics are shown with an optimization plan, not as measured uptime."
    )


def render_assets(client: ApiClient) -> None:
    show_page_header(
        "Railway assets",
        "Browse live asset records from the backend. Filters use the API's supported asset type and zone parameters.",
        "Asset register",
    )
    filters = st.columns([1, 1, 2])
    asset_type = filters[0].selectbox("Asset type", ("All types", *ASSET_TYPES))
    zone = filters[1].selectbox("Zone", ("All zones", *ZONES))
    search = filters[2].text_input("Search this result page", placeholder="Asset ID, station or track")
    page_controls = st.columns([1, 2])
    page_size = page_controls[0].selectbox("Rows per page", (25, 50, 100), index=2)
    page_number = page_controls[1].number_input("Page", min_value=1, step=1, value=1)

    try:
        response = fetch_assets(
            client,
            limit=int(page_size),
            offset=(int(page_number) - 1) * int(page_size),
            asset_type=None if asset_type == "All types" else asset_type,
            zone=None if zone == "All zones" else zone,
        )
    except ApiError as exc:
        st.error(f"Asset records could not be loaded. {exc}")
        return

    assets = response.get("items", [])
    total = int(response.get("total", 0))
    if not assets:
        if total == 0:
            st.info("No assets match these filters.")
        else:
            st.info("There are no rows on this page. Choose an earlier page.")
        return

    if search.strip():
        query = search.strip().casefold()
        assets = [
            asset
            for asset in assets
            if query
            in " ".join(
                str(asset.get(key, ""))
                for key in ("asset_id", "station", "track_id", "asset_type", "zone")
            ).casefold()
        ]

    st.caption(f"{total:,} matching assets in the backend")
    if not assets:
        st.info("No assets on this page match the search text.")
        return

    rows = []
    for asset in assets:
        probability = asset.get("predicted_failure_probability")
        rows.append(
            {
                "Asset ID": asset.get("asset_id"),
                "Type": asset.get("asset_type"),
                "Zone": asset.get("zone"),
                "Station": asset.get("station"),
                "Track": asset.get("track_id") or "—",
                "Status": asset.get("status"),
                "Defect severity": asset.get("defect_severity"),
                "Defects": asset.get("defect_count"),
                "Age (years)": asset.get("asset_age_years"),
                "Failure probability": (
                    f"{float(probability):.1%}" if probability is not None else "—"
                ),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(
        "Failure probability is the stored asset input value. The asset-list response does not include a predicted priority score."
    )


def render_predictions(client: ApiClient) -> None:
    show_page_header(
        "Predictions & risk",
        "Run the existing priority-prediction API on one or more assets already registered with the backend.",
        "Model inference",
    )
    try:
        assets = asset_options(client)
    except ApiError as exc:
        st.error(f"Assets are unavailable for prediction. {exc}")
        return

    if not assets:
        st.info("No backend assets are available. Add assets through the existing API before requesting predictions.")
        return

    by_id = {str(asset["asset_id"]): asset for asset in assets if asset.get("asset_id")}
    ids = list(by_id)
    selected = st.multiselect(
        "Choose assets",
        options=ids,
        format_func=lambda asset_id: asset_label(by_id[asset_id]),
        help="Predictions use the complete stored asset records and the loaded backend model.",
    )
    st.caption("Results are recorded by the backend as prediction requests.")

    if st.button("Run priority prediction", type="primary", disabled=not selected):
        try:
            payload = {
                "assets": [asset_request_payload(by_id[asset_id]) for asset_id in selected]
            }
            result = client.post("/prediction/batch", payload)
            st.session_state["railopt_prediction_result"] = result
            st.success(f"Prediction completed for {len(result)} asset(s).")
        except ApiError as exc:
            st.error(f"Prediction could not be completed. {exc}")

    result = st.session_state.get("railopt_prediction_result")
    if result:
        st.subheader("Latest prediction response")
        frame = pd.DataFrame(result)
        if not frame.empty:
            display = frame.rename(
                columns={
                    "asset_id": "Asset ID",
                    "predicted_priority_score": "Predicted priority score",
                    "recommended_action": "Recommended action",
                    "model_version": "Model version",
                }
            )
            st.dataframe(display, hide_index=True, width="stretch")
            st.caption(
                "Priority bands use the block-planning defaults: 75 for planning eligibility and 95 for critical priority."
            )
            for record in result:
                score = float(record.get("predicted_priority_score", 0))
                if score >= 95:
                    label, state = "Critical priority", "failed"
                elif score >= 75:
                    label, state = "Planning threshold met", "warning"
                else:
                    label, state = "Below planning threshold", "healthy"
                st.markdown(
                    f"{escape(str(record.get('asset_id', 'Asset')))} · "
                    f"{status_pill(label, state)}",
                    unsafe_allow_html=True,
                )


def render_schedule(result: dict[str, Any]) -> None:
    metrics = result.get("metrics") or {}
    st.markdown(f"#### Optimization run #{escape(str(result.get('run_id', '—')))}")
    st.markdown(
        status_pill("Solver", str(metrics.get("solver_status", "unknown"))),
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric(
        "Assets scheduled",
        f"{metrics.get('total_assets_scheduled', 0)} / {metrics.get('request_count', 0)}",
    )
    metric_columns[1].metric(
        "Availability metric",
        f"{float(metrics.get('asset_availability_percent', 0)):.1f}%",
    )
    metric_columns[2].metric(
        "Crew utilization",
        f"{float(metrics.get('crew_utilization_percent', 0)):.1f}%",
    )
    metric_columns[3].metric(
        "Maintenance completion",
        f"{float(metrics.get('maintenance_completion_percent', 0)):.1f}%",
    )

    detail_columns = st.columns(3)
    detail_columns[0].metric(
        "Estimated train impacts", metrics.get("estimated_train_impacts", 0)
    )
    detail_columns[1].metric(
        "Average schedule delay",
        f"{float(metrics.get('average_delay_hours', 0)):.1f} h",
    )
    detail_columns[2].metric(
        "Solver time",
        f"{float(metrics.get('solver_seconds', 0)):.2f} s",
    )
    st.markdown(
        '<div class="callout">Availability is the optimizer\'s scheduled-hours metric '
        'for this plan; it is not measured real-world asset uptime.</div>',
        unsafe_allow_html=True,
    )

    schedule = result.get("schedule") or []
    if not schedule:
        st.info("The optimization response contains no schedule rows.")
        return
    rows = []
    for item in schedule:
        rows.append(
            {
                "Status": item.get("status"),
                "Asset ID": item.get("asset_id"),
                "Type": item.get("asset_type"),
                "Priority": item.get("predicted_priority_score"),
                "Start": item.get("start_time") or "—",
                "End": item.get("end_time") or "—",
                "Duration (h)": item.get("duration_hours"),
                "Crew": item.get("assigned_crew") or "—",
                "Station": item.get("station"),
                "Track": item.get("track_id") or "—",
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def render_block_planning(client: ApiClient) -> None:
    show_page_header(
        "Block planning",
        "Submit selected backend assets and planning controls to the existing ML + CP-SAT optimization endpoint.",
        "Automatic maintenance planning",
    )
    try:
        assets = asset_options(client)
    except ApiError as exc:
        st.error(f"Planning inputs could not be loaded. {exc}")
        return
    if not assets:
        st.info("No backend assets are available. Add valid asset records before generating a block plan.")
        return

    by_id = {str(asset["asset_id"]): asset for asset in assets if asset.get("asset_id")}
    ids = list(by_id)
    with st.form("block_plan_form"):
        selected = st.multiselect(
            "Assets to consider",
            options=ids,
            format_func=lambda asset_id: asset_label(by_id[asset_id]),
            help="Choose existing assets. Their stored model inputs are submitted to the optimizer.",
        )
        control_columns = st.columns(3)
        available_crews = control_columns[0].number_input(
            "Available crews", min_value=1, max_value=100, value=8, step=1
        )
        horizon_days = control_columns[1].number_input(
            "Planning horizon (days)", min_value=1, max_value=30, value=7, step=1
        )
        priority_threshold = control_columns[2].number_input(
            "Priority threshold", min_value=0.0, max_value=100.0, value=75.0, step=1.0
        )
        critical_threshold = st.number_input(
            "Critical priority threshold",
            min_value=0.0,
            max_value=100.0,
            value=95.0,
            step=1.0,
            help="Must be greater than or equal to the priority threshold.",
        )
        custom_start = st.checkbox("Set a planning start time")
        planning_start: datetime | None = None
        if custom_start:
            date_column, time_column = st.columns(2)
            start_date = date_column.date_input("Planning start date", value=date.today())
            start_time = time_column.time_input("Planning start time", value=time(20, 0))
            planning_start = datetime.combine(start_date, start_time)
        submitted = st.form_submit_button(
            "Generate Optimal Block Plan", type="primary", width="stretch"
        )

    st.caption(
        "Planning thresholds control which predicted priorities are eligible for scheduling. "
        "The backend returns the solver status and schedule."
    )
    if submitted:
        if not selected:
            st.error("Select at least one asset to generate a plan.")
        elif critical_threshold < priority_threshold:
            st.error("Critical priority threshold must be greater than or equal to the priority threshold.")
        else:
            payload: dict[str, Any] = {
                "assets": [asset_request_payload(by_id[asset_id]) for asset_id in selected],
                "available_crews": int(available_crews),
                "horizon_days": int(horizon_days),
                "priority_threshold": float(priority_threshold),
                "critical_priority_threshold": float(critical_threshold),
            }
            if planning_start is not None:
                payload["planning_start"] = planning_start.isoformat()
            try:
                with st.spinner("Running model prediction and CP-SAT optimization…"):
                    result = client.post("/optimization", payload)
                if not isinstance(result, dict) or "metrics" not in result:
                    raise ApiError("The optimization endpoint returned an unexpected result.")
                st.session_state["railopt_current_optimization"] = result
                st.success("The optimization response was received and saved for this session.")
            except ApiError as exc:
                st.error(f"Block plan could not be generated. {exc}")

    result = st.session_state.get("railopt_current_optimization")
    if result:
        st.subheader("Current plan")
        render_schedule(result)


def render_system_status(client: ApiClient) -> None:
    show_page_header(
        "System status",
        "Live readiness information from the FastAPI health endpoint.",
        "Service health",
    )
    try:
        health = fetch_health(client)
    except ApiError as exc:
        st.error(f"FastAPI health could not be confirmed. {exc}")
        st.markdown(status_pill("API", "unavailable"), unsafe_allow_html=True)
        return

    api_status = str(health.get("status", "unknown"))
    database_status = "connected" if health.get("database_connected") else "disconnected"
    model_status = "loaded" if health.get("model_loaded") else "unavailable"
    overall = (
        "healthy"
        if api_status == "healthy"
        and database_status == "connected"
        and model_status == "loaded"
        else "degraded"
    )
    st.subheader("Readiness")
    columns = st.columns(4)
    columns[0].markdown(status_pill("Overall", overall), unsafe_allow_html=True)
    columns[1].markdown(status_pill("FastAPI", api_status), unsafe_allow_html=True)
    columns[2].markdown(status_pill("PostgreSQL", database_status), unsafe_allow_html=True)
    columns[3].markdown(status_pill("ML model", model_status), unsafe_allow_html=True)
    st.divider()
    st.write("**Model version:**", health.get("model_version") or "Not reported")
    st.caption("These values come directly from GET /health.")


def main() -> None:
    st.set_page_config(
        page_title="RailOpt AI | Railway Operations",
        page_icon="🚆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_styles()
    client = ApiClient()
    page = render_sidebar(client)
    if page == "Dashboard":
        render_dashboard(client)
    elif page == "Railway Assets":
        render_assets(client)
    elif page == "Predictions & Risk":
        render_predictions(client)
    elif page == "Block Planning":
        render_block_planning(client)
    else:
        render_system_status(client)


if __name__ == "__main__":
    main()
