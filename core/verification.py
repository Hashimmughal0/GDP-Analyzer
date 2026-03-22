import hashlib
from multiprocessing import Process, Queue
from typing import Any

from core.metrics import QueueCounter
from core.schema import SensorPacket, VerifiedPacket


class VerificationWorker(Process):
    def __init__(self, worker_id: int, raw_queue: Queue, processed_queue: Queue,
                 raw_counter: QueueCounter, processed_counter: QueueCounter,
                 secret_key: str, iterations: int, algorithm: str = "pbkdf2_hmac"):
        super().__init__(name=f"VerificationWorker-{worker_id}")
        self.worker_id = worker_id
        self.raw_queue = raw_queue
        self.processed_queue = processed_queue
        self.raw_counter = raw_counter
        self.processed_counter = processed_counter
        self.secret_key = secret_key
        self.iterations = max(iterations, 1000)
        self.algorithm = algorithm

    def run(self) -> None:
        while True:
            packet = self.raw_queue.get()
            self.raw_counter.decrement()
            if packet is None:
                break
            if self._verify(packet):
                verified = VerifiedPacket(
                    sequence=packet.sequence,
                    entity_name=packet.entity_name,
                    time_period=packet.time_period,
                    metric_value=packet.metric_value,
                )
                self.processed_queue.put(verified)
                self.processed_counter.increment()
            else:
                print(f"[Worker {self.worker_id}] Dropped packet {packet.sequence} (invalid signature)")
        self.processed_queue.put(None)
        self.processed_counter.increment()

    def _verify(self, packet: SensorPacket) -> bool:
        if not packet.security_hash:
            return False
        computed = self._compute_signature(packet.raw_value_str)
        return computed == packet.security_hash

    def _compute_signature(self, raw_value: str) -> str:
        if self.algorithm != "pbkdf2_hmac":
            raise ValueError(f"Algorithm '{self.algorithm}' is not supported")
        return hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=self.secret_key.encode("utf-8"),
            salt=raw_value.encode("utf-8"),
            iterations=self.iterations,
        ).hex()
