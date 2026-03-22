import csv
import os
import time
from multiprocessing import Process, Queue
from queue import Full
from typing import Any

from core.metrics import QueueCounter
from core.schema import SchemaMapper, SensorPacket


class InputProducer(Process):
    def __init__(self, dataset_path: str, schema: SchemaMapper, raw_queue: Queue,
                 delay_seconds: float, worker_count: int, raw_counter: QueueCounter):
        super().__init__(name="InputProducer")
        self.dataset_path = dataset_path
        self.schema = schema
        self.raw_queue = raw_queue
        self.delay_seconds = max(delay_seconds, 0.0)
        self.worker_count = worker_count
        self.raw_counter = raw_counter

    def run(self) -> None:
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        with open(self.dataset_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for sequence, row in enumerate(reader):
                packet = self.schema.map_row(row, sequence)
                if packet is None:
                    continue
                self._push(packet)
                if self.delay_seconds:
                    time.sleep(self.delay_seconds)
        self._drain()

    def _push(self, packet: SensorPacket | None) -> None:
        while True:
            try:
                self.raw_queue.put(packet, timeout=0.5)
                self.raw_counter.increment()
                return
            except Full:
                continue

    def _drain(self) -> None:
        for _ in range(self.worker_count):
            self._push(None)
