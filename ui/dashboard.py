import tkinter as tk
from collections import deque
from queue import Empty, Queue
from typing import Deque, Sequence, Dict, Any, Callable, Optional

from ui.components import TelemetryRibbon, ChartGrid, LogPanel


class UiDashboard:
    COLOR_PALETTE = ("#4dd0e1", "#f48fb1", "#90caf9", "#ffcc80", "#82e0aa")

    def __init__(self, ui_queue: Queue, queue_capacity: int, window_capacity: int,
                 chart_defs: Sequence[Dict[str, Any]], telemetry_flags: Dict[str, Any]):
        self.ui_queue = ui_queue
        self.chart_defs = list(chart_defs)
        self.queue_capacity = max(queue_capacity, 1)
        self.window_capacity = max(window_capacity, 1)
        self.telemetry_flags = telemetry_flags or {}
        self.root = tk.Tk()
        self.root.title("Generic Concurrent Pipeline")
        self.root.configure(bg="#111322")
        self.value_history: Deque[float] = deque(maxlen=80)
        self.average_history: Deque[float] = deque(maxlen=80)
        self.log_lines: Deque[tuple] = deque(maxlen=12)
        self.shutdown_callback: Optional[Callable[[], None]] = None
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(120, self._poll_queue)

    def set_shutdown_callback(self, callback: Callable[[], None]) -> None:
        self.shutdown_callback = callback

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.telemetry_ribbon = TelemetryRibbon(self.root, self.queue_capacity, self.window_capacity,
                                                self.telemetry_flags)
        self.telemetry_ribbon.pack(fill=tk.X, padx=10, pady=(10, 6))

        charts_frame = tk.Frame(self.root, bg="#0e121e")
        charts_frame.pack(padx=10, pady=6, fill=tk.BOTH, expand=True)
        self.chart_grid = ChartGrid(charts_frame, self.chart_defs, self.COLOR_PALETTE)
        self.chart_grid.pack(fill=tk.BOTH, expand=True)

        log_container = tk.Frame(self.root, bg="#080b14")
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))
        self.log_panel = LogPanel(log_container)
        self.log_panel.pack(fill=tk.BOTH, expand=True)

        self.summary_label = tk.Label(self.root, text="", fg="#f5f5f5", bg="#111322", font=("Segoe UI", 10))
        self.summary_label.pack(pady=(0, 10))

    def _poll_queue(self) -> None:
        try:
            while True:
                payload = self.ui_queue.get_nowait()
                payload_type = payload.get("type")
                if payload_type == "data":
                    self._handle_data(payload)
                elif payload_type == "telemetry":
                    self._handle_telemetry(payload)
                elif payload_type == "summary":
                    self._handle_summary(payload)
        except Empty:
            pass
        self.root.after(150, self._poll_queue)

    def _handle_data(self, payload: Dict[str, Any]) -> None:
        value = float(payload.get("value", 0.0))
        avg = float(payload.get("average", 0.0))
        self.value_history.append(value)
        self.average_history.append(avg)
        entry = (payload.get("entity"), payload.get("time"), value, avg)
        self.log_lines.appendleft(entry)
        self.log_panel.render(self.log_lines)
        self.chart_grid.refresh(self._select_chart_data)

    def _handle_telemetry(self, payload: Dict[str, Any]) -> None:
        raw = payload.get("raw", -1)
        processed = payload.get("processed", -1)
        backlog = payload.get("backlog", -1)
        self.telemetry_ribbon.refresh(raw, processed, backlog)

    def _handle_summary(self, payload: Dict[str, Any]) -> None:
        total = payload.get("total", 0)
        self.summary_label.configure(text=f"Pipeline completed {total} authenticated packets.")

    def _select_chart_data(self, chart_type: str) -> Sequence[float]:
        lower = (chart_type or "").lower()
        if "average" in lower or "running_average" in lower:
            return self.average_history
        return self.value_history

    def _on_close(self) -> None:
        if self.shutdown_callback:
            self.shutdown_callback()
        self.root.quit()
