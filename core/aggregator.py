import queue
from collections import deque
from threading import Event, Thread
from typing import Any, List

from core.metrics import QueueCounter
from core.schema import VerifiedPacket, calculate_running_average
from core.telemetry import PipelineTelemetrySubject


class Aggregator(Thread):
    def __init__(self, processed_queue: queue.Queue, processed_counter: QueueCounter,
                 worker_count: int, window_size: int,
                 ui_queue: queue.Queue, telemetry_subject: PipelineTelemetrySubject,
                 pipeline_done: Event):
        super().__init__(name="Aggregator")
        self.processed_queue = processed_queue
        self.processed_counter = processed_counter
        self.worker_count = max(worker_count, 1)
        self.window_size = max(window_size, 1)
        self.ui_queue = ui_queue
        self.telemetry_subject = telemetry_subject
        self.pipeline_done = pipeline_done
        self.pending: List[VerifiedPacket] = []
        self.sliding_window = deque(maxlen=self.window_size)
        self.last_emitted_time = -1
        self.total_processed = 0
        self._stop_event = Event()

    def run(self) -> None:
        sentinel_seen = 0
        while not self._stop_event.is_set():
            try:
                payload = self.processed_queue.get(timeout=0.5)
                self.processed_counter.decrement()
            except queue.Empty:
                if sentinel_seen >= self.worker_count and not self.pending:
                    break
                continue
            if payload is None:
                sentinel_seen += 1
                if sentinel_seen >= self.worker_count and not self.pending:
                    break
                continue
            self.pending.append(payload)
            self.pending.sort(key=lambda pkt: pkt.time_period)
            self._report_backlog()
            while self.pending:
                candidate = self.pending[0]
                if candidate.time_period <= self.last_emitted_time:
                    self.pending.pop(0)
                    self._report_backlog()
                    continue
                self.pending.pop(0)
                self.last_emitted_time = candidate.time_period
                self.sliding_window.append(candidate.metric_value)
                average = calculate_running_average(self.sliding_window)
                self.total_processed += 1
                self._publish(candidate, average)
                self._report_backlog()
            if sentinel_seen >= self.worker_count and not self.pending:
                break
        self._publish_summary()
        self.pipeline_done.set()

    def stop(self) -> None:
        self._stop_event.set()
        try:
            self.processed_queue.put(None, timeout=0.5)
            self.processed_counter.increment()
        except queue.Full:
            pass

    def _publish(self, packet: VerifiedPacket, average: Any) -> None:
        self.ui_queue.put({
            "type": "data",
            "sequence": packet.sequence,
            "entity": packet.entity_name,
            "time": packet.time_period,
            "value": packet.metric_value,
            "average": average or 0.0,
            "window": len(self.sliding_window),
        })

    def _publish_summary(self) -> None:
        self.ui_queue.put({"type": "summary", "total": self.total_processed})

    def _report_backlog(self) -> None:
        if self.telemetry_subject:
            self.telemetry_subject.report_post_processing_backlog(len(self.pending))
