from dataclasses import dataclass
from typing import Sequence, Dict, Any, Optional


@dataclass
class SensorPacket:
    sequence: int
    entity_name: str
    time_period: int
    metric_value: float
    raw_value_str: str
    security_hash: str


@dataclass
class VerifiedPacket:
    sequence: int
    entity_name: str
    time_period: int
    metric_value: float


class SchemaMapper:
    _TYPE_CASTS = {
        "string": str,
        "integer": int,
        "float": float,
    }

    def __init__(self, columns: Sequence[Dict[str, Any]]):
        self._schema: list[tuple[str, str, Any]] = []
        for column in columns:
            source = column.get("source_name")
            internal = column.get("internal_mapping")
            data_type = column.get("data_type", "string").lower()
            caster = self._TYPE_CASTS.get(data_type, str)
            if source and internal:
                self._schema.append((source, internal, caster))

    def map_row(self, raw_row: Dict[str, str], sequence: int) -> Optional[SensorPacket]:
        cleaned: Dict[str, Any] = {}
        for source, internal, caster in self._schema:
            raw_value = raw_row.get(source)
            if raw_value is None:
                return None
            try:
                cleaned[internal] = caster(raw_value)
            except (ValueError, TypeError):
                return None
        required = {"entity_name", "time_period", "metric_value", "security_hash"}
        if not required.issubset(cleaned.keys()):
            return None
        metric_value = float(cleaned["metric_value"])
        return SensorPacket(
            sequence=sequence,
            entity_name=str(cleaned["entity_name"]),
            time_period=int(cleaned["time_period"]),
            metric_value=metric_value,
            raw_value_str=f"{metric_value:.2f}",
            security_hash=str(cleaned["security_hash"]),
        )


def calculate_running_average(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)
