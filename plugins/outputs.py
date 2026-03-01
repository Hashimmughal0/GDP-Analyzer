import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utilities.visualizer import plot_region_gdp, plot_year_distribution, _choose_scale


class ConsoleWriter:
    def write(self, records: List[Dict[str, Any]]) -> None:
        print("\n" + "=" * 70)
        print(" GDP ANALYTICS DASHBOARD ".center(70))
        print("=" * 70)
        for record in records:
            label = record.get("Label", "Result")
            data  = record.get("Data", [])
            if record.get("Type") == "Plot":
                df = pd.DataFrame(data)
                if not df.empty:
                    if "Country" in df.columns and "Country Name" not in df.columns:
                        df = df.rename(columns={"Country": "Country Name"})
                    plot_region_gdp(df, record.get("Region", ""), record.get("Year", 2020),
                                    top_n=record.get("Top_N", 10))
                    plot_year_distribution(df, record.get("Year", 2020))
                continue
            print(f"\n>> {label}")
            print("-" * 70)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        parts = []
                        for k, v in item.items():
                            if k == "Value" and isinstance(v, (int, float)):
                                factor, unit = _choose_scale([v])
                                sv = v / factor if factor else v
                                parts.append(f"{k}: {sv:,.2f} {unit} USD" if unit else f"{k}: {sv:,.2f}")
                            elif isinstance(v, float):
                                parts.append(f"{k}: {v:,.2f}")
                            else:
                                parts.append(f"{k}: {v}")
                        print("   " + " | ".join(parts))
                    else:
                        print(f"   {item}")
            else:
                print(f"   {data}")
        print("\n" + "=" * 70 + "\n")


class GraphicsChartWriter:
    def write(self, records: List[Dict[str, Any]]) -> None:
        print(f"[GraphicsChartWriter] {len(records)} records received.")


class UiWriter:
    BG        = "#0f0f0f"
    PANEL     = "#1a1a2e"
    ACCENT    = "#e94560"
    FG        = "#eaeaea"
    MUTED     = "#a8a8b3"
    GRID      = "#2a2a3e"
    TAB_BG    = "#16213e"
    FONT_MONO = ("Consolas", 11)
    FONT_UI   = ("Segoe UI", 11)

    def write(self, records: List[Dict[str, Any]]) -> None:
        root = tk.Tk()
        root.title("GDP Analytics — Professional Dashboard")
        root.geometry("1280x820")
        root.minsize(900, 600)
        root.configure(bg=self.BG)
        root.protocol("WM_DELETE_WINDOW", lambda: self._on_close(root))

        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame",        background=self.BG)
        style.configure("TNotebook",     background=self.BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab", background=self.TAB_BG, foreground=self.MUTED,
                         padding=[18, 8], font=(*self.FONT_UI, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", self.PANEL)],
                  foreground=[("selected", self.FG)])
        style.configure("Vertical.TScrollbar",
                         troughcolor=self.BG, background=self.GRID, arrowcolor=self.MUTED)

        nb = ttk.Notebook(root)
        nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self._build_config_tab(nb)
        plots_to_render = self._build_outputs_tab(nb, records)
        self._build_viz_tab(nb, plots_to_render)

        root.mainloop()

    def _on_close(self, root: tk.Tk) -> None:
        root.destroy()
        sys.exit(0)

    def _scrollable_text(self, parent, fg: str) -> tk.Text:
        sb = ttk.Scrollbar(parent)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        t = tk.Text(parent, bg=self.PANEL, fg=fg, font=self.FONT_MONO,
                    wrap=tk.NONE, padx=18, pady=14, relief=tk.FLAT,
                    selectbackground=self.ACCENT, yscrollcommand=sb.set)
        sb.config(command=t.yview)
        t.pack(fill=tk.BOTH, expand=True)
        return t

    def _build_config_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb)
        nb.add(tab, text="  Configuration  ")
        t = self._scrollable_text(tab, "#56cfad")
        # NOTE: config.json lives inside the `config` directory at project root.
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "config.json",
        )
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                t.insert(tk.END, json.dumps(json.load(f), indent=4))
        except Exception as e:
            t.insert(tk.END, f"Error loading config: {e}")
        t.config(state=tk.DISABLED)

    def _build_outputs_tab(self, nb: ttk.Notebook, records: List[Dict[str, Any]]) -> list:
        tab = ttk.Frame(nb)
        nb.add(tab, text="  Analytical Outputs  ")
        t = self._scrollable_text(tab, self.FG)
        t.tag_config("header", foreground=self.ACCENT, font=(*self.FONT_MONO, "bold"))
        t.tag_config("row",    foreground=self.FG)
        t.tag_config("dim",    foreground=self.MUTED)

        plots = []
        for record in records:
            if record.get("Type") == "Plot":
                plots.append(record)
                continue
            label = record.get("Label", "Result")
            data  = record.get("Data", [])
            t.insert(tk.END, f"\n  {label}\n", "header")
            t.insert(tk.END, "  " + "─" * 72 + "\n", "dim")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        parts = []
                        for k, v in item.items():
                            if k == "Value" and isinstance(v, (int, float)):
                                factor, unit_ = _choose_scale([v])
                                sv = v / factor if factor else v
                                parts.append(f"{k}: {sv:,.2f} {unit_} USD" if unit_ else f"{k}: {sv:,.2f}")
                            elif isinstance(v, float):
                                parts.append(f"{k}: {v:,.2f}")
                            else:
                                parts.append(f"{k}: {v}")
                        t.insert(tk.END, "  • " + "  |  ".join(parts) + "\n", "row")
                    else:
                        t.insert(tk.END, f"  • {item}\n", "row")
            else:
                t.insert(tk.END, f"  {data}\n", "row")
        t.config(state=tk.DISABLED)
        return plots

    def _build_viz_tab(self, nb: ttk.Notebook, plots: list) -> None:
        tab = ttk.Frame(nb)
        nb.add(tab, text="  Visualizations  ")

        viz_sb     = ttk.Scrollbar(tab, orient=tk.VERTICAL)
        viz_canvas = tk.Canvas(tab, bg=self.BG, highlightthickness=0, yscrollcommand=viz_sb.set)
        inner      = ttk.Frame(viz_canvas)
        viz_sb.config(command=viz_canvas.yview)

        inner.bind("<Configure>",
                   lambda e: viz_canvas.configure(scrollregion=viz_canvas.bbox("all")))
        win_id = viz_canvas.create_window((0, 0), window=inner, anchor="nw")
        viz_canvas.bind("<Configure>",
                        lambda e: viz_canvas.itemconfig(win_id, width=e.width))

        viz_sb.pack(side=tk.RIGHT, fill=tk.Y)
        viz_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _mw(event):
            viz_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        viz_canvas.bind("<Enter>", lambda _: viz_canvas.bind_all("<MouseWheel>", _mw))
        viz_canvas.bind("<Leave>", lambda _: viz_canvas.unbind_all("<MouseWheel>"))

        for plot_rec in plots:
            try:
                df = pd.DataFrame(plot_rec.get("Data", []))
                if df.empty:
                    continue
                if "Country" in df.columns and "Country Name" not in df.columns:
                    df = df.rename(columns={"Country": "Country Name"})
                region = plot_rec.get("Region", "Unknown")
                year   = plot_rec.get("Year", 2020)
                top_n  = plot_rec.get("Top_N", 10)
                all_figs = (plot_region_gdp(df, region, year, top_n=top_n, return_fig=True) or []) + \
                           (plot_year_distribution(df, year, return_fig=True) or [])
                for fig in all_figs:
                    if fig is None:
                        continue
                    fig.set_facecolor(self.BG)
                    fc = FigureCanvasTkAgg(fig, master=inner)
                    fc.draw()
                    fc.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=18, pady=14)
            except Exception as e:
                print(f"[WARN] Could not render plot: {e}")