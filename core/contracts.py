from typing import Protocol, List, Any, Dict, runtime_checkable


@runtime_checkable
class DataSink(Protocol):
    def write(self, records: List[Dict[str, Any]]) -> None: ...


class PipelineService(Protocol):
    def execute(self, raw_data: List[Any]) -> None: ...
