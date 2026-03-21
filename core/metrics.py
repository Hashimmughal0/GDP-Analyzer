from multiprocessing import Lock, Value


class QueueCounter:
    def __init__(self) -> None:
        self._value = Value('i', 0)
        self._lock = Lock()

    def increment(self) -> None:
        with self._lock:
            self._value.value += 1

    def decrement(self) -> None:
        with self._lock:
            if self._value.value > 0:
                self._value.value -= 1

    def snapshot(self) -> int:
        with self._lock:
            return self._value.value
