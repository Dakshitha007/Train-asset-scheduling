"""Domain constants used by validation, preprocessing, and planning."""

ASSET_TYPES = ("Bridge", "OHE", "Signal", "Switch", "Track")
ZONES = ("Central", "East", "North", "South", "West")
WEATHER_TYPES = ("Cloudy", "Fog", "Rain", "Sunny")
DEFECT_SEVERITIES = ("High", "Low", "Medium")
CATEGORICAL_FEATURES = (
    "asset_type",
    "zone",
    "weather",
    "defect_severity",
    "passenger_peak",
    "nearby_alternate_track",
)
MODEL_TARGET = "priority_score"

CRITICAL_DEADLINE_HOURS = 24
NIGHT_WINDOW_START_HOUR = 20
NIGHT_WINDOW_END_HOUR = 8
CRITICAL_DAY_WINDOW = (0, 12)
PEAK_PASSENGER_WINDOWS = ((7, 10), (16, 20))

# Weighted CP-SAT objective, expressed in integer score points.
AVAILABILITY_REWARD_WEIGHT = 1_000_000  # Per scheduled maintenance request.
PRIORITY_REWARD_WEIGHT = 10_000  # Per rounded priority point serviced.
EARLY_SERVICE_WEIGHT = 250  # Per priority point and hour completed before horizon.
TRAIN_DELAY_PENALTY_WEIGHT = 100  # Per estimated train exposed to a work block.
CREW_IDLE_REWARD_WEIGHT = 100  # Per scheduled crew-hour, reducing idle capacity.
MAINTENANCE_COST_PENALTY_WEIGHT = 25  # Per scheduled crew-hour of maintenance cost.
NO_ALTERNATE_TRACK_PENALTY = 50_000  # Per scheduled job without a detour track.
PEAK_OVERLAP_PENALTY_WEIGHT = 10_000  # Per peak-overlap hour; doubled at passenger peak.
CRITICAL_DAY_WINDOW_PENALTY = 10_000  # Per critical daytime-window job vs overnight.
