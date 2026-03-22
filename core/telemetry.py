import threading
import time
from typing import Protocol, Any

from core.metrics import QueueCounter


class TelemetryObserver(Protocol):
    def refresh(self, raw_queue_size: int, processed_queue_size: int, backlog: int) -> None: ...


class PipelineTelemetrySubject:
    def __init__(self) -> None:
        self._observers: list[TelemetryObserver] = []
        self._raw = 0
        self._processed = 0
        self._backlog = 0

    def attach(self, observer: TelemetryObserver) -> None:
        self._observers.append(observer)

    def report_stream_sizes(self, raw: int, processed: int) -> None:
        self._raw = raw
        self._processed = processed
        self._broadcast()

    def report_post_processing_backlog(self, backlog: int) -> None:
        self._backlog = backlog
        self._broadcast()

    def _broadcast(self) -> None:
        for observer in self._observers:
            observer.refresh(self._raw, self._processed, self._backlog)


class TelemetryWatcher(threading.Thread):
    def __init__(self, subject: PipelineTelemetrySubject, raw_counter: QueueCounter,
                 processed_counter: QueueCounter, raw_queue: Any = None,
                 processed_queue: Any = None, poll_interval: float = 0.8) -> None:
        super().__init__(name="TelemetryWatcher", daemon=True)
        self._subject = subject
        self._raw_counter = raw_counter
        self._processed_counter = processed_counter
        self._raw_queue = raw_queue
        self._processed_queue = processed_queue
        self._interval = max(poll_interval, 0.2)
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            raw_size = self._observe_queue(self._raw_queue, self._raw_counter)
            processed_size = self._observe_queue(self._processed_queue, self._processed_counter)
            self._subject.report_stream_sizes(raw_size, processed_size)
            time.sleep(self._interval)

    def stop(self) -> None:
        self._stop_event.set()

    def _observe_queue(self, queue_obj: Any, counter: QueueCounter) -> int:
        if queue_obj is None:
            return counter.snapshot()
        try:
            return queue_obj.qsize()
        except (OSError, NotImplementedError, AttributeError):
            return counter.snapshot()


class TelemetryQueueObserver:
    def __init__(self, ui_queue: Any) -> None:
        self._ui_queue = ui_queue

    def refresh(self, raw_queue_size: int, processed_queue_size: int, backlog: int) -> None:
        self._ui_queue.put({
            "type": "telemetry",
            "raw": raw_queue_size,
            "processed": processed_queue_size,
            "backlog": backlog,
        })
