import tkinter as tk
from collections import deque
from queue import Empty, Queue
from typing import Sequence, Dict, Any, Callable, Optional


class UiDashboard:
    COLOR_PALETTE = ("#4dd0e1", "#f48fb1", "#90caf9", "#ffcc80", "#82e0aa")

    def __init__(self, ui_queue: Queue, queue_capacity: int, window_capacity: int,
                 chart_defs: Sequence[Dict[str, Any]], telemetry_flags: Dict[str, bool]):
        self.ui_queue = ui_queue
        self.chart_defs = list(chart_defs)
        self.queue_capacity = max(queue_capacity, 1)
        self.window_capacity = max(window_capacity, 1)
        self.telemetry_flags = telemetry_flags or {}
        self.root = tk.Tk()
        self.root.title("Generic Concurrent Pipeline")
        self.root.configure(bg="#111322")
        self.value_history = deque(maxlen=80)
        self.average_history = deque(maxlen=80)
        self.log_lines = deque(maxlen=12)
        self.shutdown_callback: Optional[Callable[[], None]] = None
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(120, self._poll_queue)

    def set_shutdown_callback(self, callback: Callable[[], None]) -> None:
        self.shutdown_callback = callback

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        telemetry_frame = tk.Frame(self.root, bg="#10131e")
        telemetry_frame.pack(fill=tk.X, padx=10, pady=(10, 6))
        self.telemetry_labels: Dict[str, tk.Label] = {}
        telemetry_rows = [
            ("Raw Stream", "show_raw_stream"),
            ("Intermediate Stream", "show_intermediate_stream"),
            ("Post-Processing", "show_processed_stream"),
        ]
        for label, flag in telemetry_rows:
            if not self.telemetry_flags.get(flag, True):
                continue
            lbl = tk.Label(telemetry_frame, text=f"{label}: --", bg="#10131e", fg="#d1d1d1",
                           font=("Segoe UI", 10, "bold"))
            lbl.pack(side=tk.LEFT, padx=12, pady=6)
            self.telemetry_labels[label] = lbl

        charts_frame = tk.Frame(self.root, bg="#0e121e")
        charts_frame.pack(padx=10, pady=6, fill=tk.BOTH, expand=True)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        if not self.chart_defs:
            self.chart_defs = [{"type": "real_time_line_graph_values", "title": "Live Values"}]
        self.chart_widgets = []
        for idx, chart in enumerate(self.chart_defs):
            frame = tk.Frame(charts_frame, bg="#0e121e")
            frame.grid(row=idx // 2, column=idx % 2, padx=8, pady=8, sticky="nsew")
            frame.columnconfigure(0, weight=1)
            title = chart.get("title", f"Chart {idx + 1}")
            tk.Label(frame, text=title, fg="#d4d4d4", bg="#0e121e", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, padx=6, pady=(2, 0))
            canvas = tk.Canvas(frame, width=460, height=180, bg="#0e121e", highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
            self.chart_widgets.append({
                "canvas": canvas,
                "type": chart.get("type", ""),
                "color": self.COLOR_PALETTE[idx % len(self.COLOR_PALETTE)],
            })

        log_frame = tk.Frame(self.root, bg="#080b14")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))
        self.log_text = tk.Text(log_frame, height=12, bg="#080b14", fg="#a8a8b3", font=("Consolas", 10), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)
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
        self._refresh_log()
        for widget in self.chart_widgets:
            data = self._select_chart_data(widget["type"])
            self._draw_chart(widget["canvas"], data, widget["color"])

    def _handle_telemetry(self, payload: Dict[str, Any]) -> None:
        if not self.telemetry_labels:
            return
        raw = payload.get("raw", -1)
        processed = payload.get("processed", -1)
        backlog = payload.get("backlog", -1)
        statuses = []
        if "Raw Stream" in self.telemetry_labels:
            statuses.append(("Raw Stream", raw, self.telemetry_labels["Raw Stream"], self.queue_capacity))
        if "Intermediate Stream" in self.telemetry_labels:
            statuses.append(("Intermediate Stream", processed, self.telemetry_labels["Intermediate Stream"], self.queue_capacity))
        if "Post-Processing" in self.telemetry_labels:
            statuses.append(("Post-Processing", backlog, self.telemetry_labels["Post-Processing"], self.window_capacity))
        for label, count, widget, capacity in statuses:
            text = self._format_status(label, count, capacity)
            widget.configure(text=text)

    def _handle_summary(self, payload: Dict[str, Any]) -> None:
        total = payload.get("total", 0)
        self.summary_label.configure(text=f"Pipeline completed {total} authenticated packets.")

    def _refresh_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        for entity, timestamp, value, avg in list(self.log_lines):
            line = f"{timestamp} | {entity} | Value={value:.2f} | Avg={avg:.2f}\n"
            self.log_text.insert(tk.END, line)
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.yview_moveto(0.0)

    def _draw_chart(self, canvas: tk.Canvas, values: Sequence[float], line_color: str) -> None:
        canvas.delete("all")
        if len(values) < 2:
            return
        canvas.update_idletasks()
        width = int(canvas.winfo_width() or int(canvas["width"]))
        height = int(canvas.winfo_height() or int(canvas["height"]))
        max_val = max(values)
        min_val = min(values)
        span = max_val - min_val or 1.0
        points = []
        step = max(1, width / max(len(values) - 1, 1))
        for idx, value in enumerate(values):
            x = 10 + idx * step
            y = height - ((value - min_val) / span) * (height - 20) - 10
            points.extend((x, y))
        if len(points) >= 4:
            canvas.create_line(*points, fill=line_color, width=2, smooth=True)
        canvas.create_text(10, 10, anchor=tk.NW, fill="#b0bec5", text=f"min {min_val:.2f}")
        canvas.create_text(width - 10, 10, anchor=tk.NE, fill="#b0bec5", text=f"max {max_val:.2f}")

    def _select_chart_data(self, chart_type: str) -> Sequence[float]:
        lower = (chart_type or "").lower()
        if "average" in lower or "running_average" in lower:
            return self.average_history
        return self.value_history

    def _format_status(self, label: str, count: int, capacity: int) -> str:
        if count < 0 or capacity <= 0:
            return f"{label}: {count if count >= 0 else '?'}"
        ratio = min(count / capacity, 1.0)
        color = "GREEN" if ratio < 0.6 else "YELLOW" if ratio < 0.85 else "RED"
        percent = f"{ratio * 100:.0f}%"
        return f"{label}: {count}/{capacity} [{color} {percent}]"

    def _on_close(self) -> None:
        if self.shutdown_callback:
            self.shutdown_callback()
        self.root.quit()
