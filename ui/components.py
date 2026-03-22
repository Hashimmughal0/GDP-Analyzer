import tkinter as tk
from typing import Sequence, Dict, Any, Callable, Iterable


TELEMETRY_ROWS = [
    ("Raw Stream", "show_raw_stream"),
    ("Intermediate Stream", "show_intermediate_stream"),
    ("Post-Processing", "show_processed_stream"),
]


class TelemetryRibbon(tk.Frame):
    def __init__(self, parent: tk.Misc, queue_capacity: int, window_capacity: int,
                 telemetry_flags: Dict[str, Any]) -> None:
        super().__init__(parent, bg="#10131e")
        self.queue_capacity = max(queue_capacity, 1)
        self.window_capacity = max(window_capacity, 1)
        self.labels: Dict[str, Dict[str, tk.Label]] = {}
        for title, flag in TELEMETRY_ROWS:
            if not telemetry_flags.get(flag, True):
                continue
            row = tk.Frame(self, bg="#10131e")
            row.pack(side=tk.LEFT, padx=12, pady=6)

            lbl = tk.Label(row, text=f"{title}: --", bg="#10131e", fg="#d1d1d1",
                           font=("Segoe UI", 10, "bold"))
            lbl.pack(side=tk.LEFT)

            led = tk.Label(row, text=" ", bg="#5a5f6d", width=2, height=1,
                           relief=tk.SUNKEN, bd=1)
            led.pack(side=tk.LEFT, padx=(8, 0))

            self.labels[title] = {"text": lbl, "led": led}

    def refresh(self, raw: int, processed: int, backlog: int) -> None:
        statuses = []
        if "Raw Stream" in self.labels:
            statuses.append(("Raw Stream", raw, self.labels["Raw Stream"], self.queue_capacity))
        if "Intermediate Stream" in self.labels:
            statuses.append(("Intermediate Stream", processed, self.labels["Intermediate Stream"], self.queue_capacity))
        if "Post-Processing" in self.labels:
            statuses.append(("Post-Processing", backlog, self.labels["Post-Processing"], self.window_capacity))

        for label, count, widget_set, capacity in statuses:
            text_label = widget_set["text"]
            led_label = widget_set["led"]

            status_text, color = self._format_status(label, count, capacity)
            text_label.configure(text=status_text)
            led_label.configure(bg=color)

    @staticmethod
    def _format_status(label: str, count: int, capacity: int) -> tuple[str, str]:
        if count < 0 or capacity <= 0:
            return (f"{label}: {count if count >= 0 else '?'}", "#5a5f6d")
        ratio = min(count / capacity, 1.0)
        if ratio < 0.6:
            led_color = "#4caf50"  # green
        elif ratio < 0.85:
            led_color = "#ffeb3b"  # yellow
        else:
            led_color = "#f44336"  # red
        percent = f"{ratio * 100:.0f}%"
        return (f"{label}: {count}/{capacity} ({percent})", led_color)


class ChartView:
    def __init__(self, parent: tk.Misc, title: str, chart_type: str, color: str) -> None:
        self.chart_type = chart_type or ""
        self.color = color
        self.frame = tk.Frame(parent, bg="#0e121e")
        self.frame.columnconfigure(0, weight=1)
        tk.Label(self.frame, text=title, fg="#d4d4d4", bg="#0e121e",
                 font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, padx=6, pady=(2, 0))
        self.canvas = tk.Canvas(self.frame, width=460, height=180, bg="#0e121e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

    def draw(self, values: Sequence[float]) -> None:
        self.canvas.delete("all")
        data = list(values)
        if len(data) < 1:
            return
        width = int(self.canvas.winfo_width() or int(self.canvas["width"]))
        height = int(self.canvas.winfo_height() or int(self.canvas["height"]))
        self.canvas.update_idletasks()
        width = max(width, 120)
        height = max(height, 80)
        max_val = max(data)
        min_val = min(data)
        span = max_val - min_val or 1.0
        points = []
        step = max(1, width / max(len(data) - 1, 1))
        for idx, value in enumerate(data):
            x = 10 + idx * step
            y = height - ((value - min_val) / span) * (height - 20) - 10
            points.extend((x, y))
        if len(points) >= 4:
            self.canvas.create_line(*points, fill=self.color, width=2, smooth=True)
        self.canvas.create_text(10, 10, anchor=tk.NW, fill="#b0bec5", text=f"min {min_val:.2f}")
        self.canvas.create_text(width - 10, 10, anchor=tk.NE, fill="#b0bec5", text=f"max {max_val:.2f}")


class ChartGrid(tk.Frame):
    def __init__(self, parent: tk.Misc, chart_defs: Iterable[Dict[str, Any]], palette: Sequence[str]) -> None:
        super().__init__(parent, bg="#0e121e")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.chart_views: list[ChartView] = []
        defs = list(chart_defs)
        if not defs:
            defs = [{"type": "real_time_line_graph_values", "title": "Live Values"}]
        for idx, chart in enumerate(defs):
            chart_type = chart.get("type", "")
            title = chart.get("title", f"Chart {idx + 1}")
            color = palette[idx % len(palette)]
            view = ChartView(self, title, chart_type, color)
            view.frame.grid(row=idx // 2, column=idx % 2, padx=8, pady=8, sticky="nsew")
            self.chart_views.append(view)

    def refresh(self, selector: Callable[[str], Sequence[float]]) -> None:
        for view in self.chart_views:
            data = selector(view.chart_type)
            view.draw(data)


class LogPanel(tk.Frame):
    def __init__(self, parent: tk.Misc, max_entries: int = 12) -> None:
        super().__init__(parent, bg="#080b14")
        self.max_entries = max_entries
        self.text = tk.Text(self, height=12, bg="#080b14", fg="#a8a8b3",
                            font=("Consolas", 10), wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.configure(state=tk.DISABLED)

    def render(self, entries: Sequence[tuple]) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        for entity, timestamp, value, avg in list(entries)[:self.max_entries]:
            line = f"{timestamp} | {entity} | Value={value:.2f} | Avg={avg:.2f}\n"
            self.text.insert(tk.END, line)
        self.text.configure(state=tk.DISABLED)
        self.text.yview_moveto(0.0)
