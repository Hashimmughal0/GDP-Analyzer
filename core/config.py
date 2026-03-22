import json
import os
from typing import Any, Dict, Sequence

MANDATORY_TOP_LEVEL = [
    "dataset_path",
    "pipeline_dynamics",
    "schema_mapping",
    "processing",
    "visualizations",
]


class ConfigError(Exception):
    """Raised when the configuration file is missing required keys or values."""


def _ensure_key(container: Dict[str, Any], key: str, path: str) -> Any:
    if key not in container:
        raise ConfigError(f"Missing required config key: {path}.{key}")
    return container[key]


def _ensure_sequence(value: Any, path: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ConfigError(f"{path} must be a list/sequence")
    if not value:
        raise ConfigError(f"{path} must contain at least one entry")
    return value


def _validate_schema_mapping(schema: Dict[str, Any]) -> None:
    columns = _ensure_key(schema, "columns", "schema_mapping")
    columns = _ensure_sequence(columns, "schema_mapping.columns")
    required_column_keys = ("source_name", "internal_mapping", "data_type")
    for idx, column in enumerate(columns):
        if not isinstance(column, dict):
            raise ConfigError(f"schema_mapping.columns[{idx}] must be an object")
        for key in required_column_keys:
            if key not in column or not column[key]:
                raise ConfigError(f"schema_mapping.columns[{idx}].{key} is required")


def _validate_pipeline_dynamics(dynamics: Dict[str, Any]) -> None:
    stream = _ensure_key(dynamics, "stream_queue_max_size", "pipeline_dynamics")
    parallel = _ensure_key(dynamics, "core_parallelism", "pipeline_dynamics")
    if not isinstance(stream, int) or stream <= 0:
        raise ConfigError("pipeline_dynamics.stream_queue_max_size must be a positive integer")
    if not isinstance(parallel, int) or parallel <= 0:
        raise ConfigError("pipeline_dynamics.core_parallelism must be a positive integer")
    delay = dynamics.get("input_delay_seconds")
    if delay is None:
        raise ConfigError("pipeline_dynamics.input_delay_seconds is required")
    if not isinstance(delay, (int, float)) or delay < 0:
        raise ConfigError("pipeline_dynamics.input_delay_seconds must be a non-negative number")


def _validate_processing(processing: Dict[str, Any]) -> None:
    stateless = _ensure_key(processing, "stateless_tasks", "processing")
    if not isinstance(stateless, dict):
        raise ConfigError("processing.stateless_tasks must be an object")
    operation = _ensure_key(stateless, "operation", "processing.stateless_tasks")
    if operation != "verify_signature":
        raise ConfigError("processing.stateless_tasks.operation must be 'verify_signature'")
    if not stateless.get("secret_key"):
        raise ConfigError("processing.stateless_tasks.secret_key is required")
    if not isinstance(stateless.get("iterations"), int) or stateless["iterations"] <= 0:
        raise ConfigError("processing.stateless_tasks.iterations must be a positive integer")
    stateful = _ensure_key(processing, "stateful_tasks", "processing")
    if not isinstance(stateful, dict):
        raise ConfigError("processing.stateful_tasks must be an object")
    window = stateful.get("running_average_window_size")
    if not isinstance(window, int) or window <= 0:
        raise ConfigError("processing.stateful_tasks.running_average_window_size must be a positive integer")


def _validate_visualizations(visualizations: Dict[str, Any]) -> None:
    if not isinstance(visualizations, dict):
        raise ConfigError("visualizations must be an object")
    telemetry = _ensure_key(visualizations, "telemetry", "visualizations")
    if not isinstance(telemetry, dict):
        raise ConfigError("visualizations.telemetry must be an object")
    charts = _ensure_key(visualizations, "data_charts", "visualizations")
    _ensure_sequence(charts, "visualizations.data_charts")
    for idx, chart in enumerate(charts):
        if not isinstance(chart, dict):
            raise ConfigError(f"visualizations.data_charts[{idx}] must be an object")
        if not chart.get("type"):
            raise ConfigError(f"visualizations.data_charts[{idx}].type is required")
        if not chart.get("title"):
            raise ConfigError(f"visualizations.data_charts[{idx}].title is required")


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    if not isinstance(config, dict):
        raise ConfigError("Configuration must be a JSON object")
    for key in MANDATORY_TOP_LEVEL:
        _ensure_key(config, key, "config")
    _validate_pipeline_dynamics(config["pipeline_dynamics"])
    _validate_schema_mapping(config["schema_mapping"])
    _validate_processing(config["processing"])
    _validate_visualizations(config["visualizations"])
    if not isinstance(config["dataset_path"], str) or not config["dataset_path"]:
        raise ConfigError("dataset_path must be a non-empty string")
    return config
