import os
import queue
from dataclasses import dataclass, field
from multiprocessing import Queue as MpQueue
from threading import Event
from typing import Any, Dict, Sequence, List

from core.aggregator import Aggregator
from core.config import load_config
from core.metrics import QueueCounter
from core.producer import InputProducer
from core.schema import SchemaMapper
from core.telemetry import PipelineTelemetrySubject, TelemetryWatcher, TelemetryQueueObserver
from core.verification import VerificationWorker


@dataclass
class PipelineRuntime:
    input_process: InputProducer
    workers: List[VerificationWorker]
    aggregator: Aggregator
    telemetry_watcher: TelemetryWatcher
    telemetry_subject: PipelineTelemetrySubject
    ui_queue: queue.Queue
    stream_max: int
    window_size: int
    chart_defs: Sequence[Dict[str, Any]]
    telemetry_flags: Dict[str, Any]
    _started: bool = field(default=False, init=False)
    _stopped: bool = field(default=False, init=False)

    def start_components(self) -> None:
        if self._started:
            return
        self._started = True
        self.telemetry_watcher.start()
        self.aggregator.start()
        self.input_process.start()
        for worker in self.workers:
            worker.start()

    def stop_components(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self.aggregator.stop()
        self.telemetry_watcher.stop()
        for proc in (self.input_process, *self.workers):
            if proc.is_alive():
                proc.terminate()

    def join_components(self, timeout: float = 0.5) -> None:
        for proc in (self.input_process, *self.workers):
            proc.join(timeout=timeout)
        if self.aggregator.is_alive():
            self.aggregator.join(timeout=timeout)
        if self.telemetry_watcher.is_alive():
            self.telemetry_watcher.join(timeout=timeout)


def build_pipeline(base_dir: str, config_path: str) -> PipelineRuntime:
    config = load_config(config_path)
    dataset_path = os.path.join(base_dir, config["dataset_path"])
    dynamics = config["pipeline_dynamics"]
    stream_max = dynamics["stream_queue_max_size"]
    core_parallelism = dynamics["core_parallelism"]
    input_delay = float(dynamics.get("input_delay_seconds", 0.0))

    raw_queue = MpQueue(maxsize=stream_max)
    processed_queue = MpQueue(maxsize=stream_max)
    ui_queue: queue.Queue = queue.Queue()
    raw_counter = QueueCounter()
    processed_counter = QueueCounter()

    telemetry_subject = PipelineTelemetrySubject()
    telemetry_subject.attach(TelemetryQueueObserver(ui_queue))
    telemetry_watcher = TelemetryWatcher(
        telemetry_subject,
        raw_counter,
        processed_counter,
        raw_queue=raw_queue,
        processed_queue=processed_queue,
        poll_interval=max(input_delay, 0.2),
    )

    mapper = SchemaMapper(config["schema_mapping"]["columns"])
    input_process = InputProducer(dataset_path, mapper, raw_queue, input_delay,
                                   core_parallelism, raw_counter)

    stateless = config["processing"]["stateless_tasks"]
    workers: List[VerificationWorker] = []
    for idx in range(core_parallelism):
        worker = VerificationWorker(
            worker_id=idx + 1,
            raw_queue=raw_queue,
            processed_queue=processed_queue,
            secret_key=stateless.get("secret_key", ""),
            raw_counter=raw_counter,
            processed_counter=processed_counter,
            iterations=int(stateless.get("iterations", 100000)),
            algorithm=stateless.get("algorithm", "pbkdf2_hmac"),
        )
        workers.append(worker)

    window_size = config["processing"]["stateful_tasks"]["running_average_window_size"]
    pipeline_done = Event()
    aggregator = Aggregator(processed_queue, processed_counter, core_parallelism, window_size,
                            ui_queue, telemetry_subject, pipeline_done)

    chart_defs = config.get("visualizations", {}).get("data_charts", [])
    telemetry_flags = config.get("visualizations", {}).get("telemetry", {})
    return PipelineRuntime(
        input_process=input_process,
        workers=workers,
        aggregator=aggregator,
        telemetry_watcher=telemetry_watcher,
        telemetry_subject=telemetry_subject,
        ui_queue=ui_queue,
        stream_max=stream_max,
        window_size=window_size,
        chart_defs=list(chart_defs),
        telemetry_flags=dict(telemetry_flags or {}),
    )
