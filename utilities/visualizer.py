import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import numpy as np

# ─── Shared dark theme constants ─────────────────────────────────────────────
BG      = "#0f0f0f"      # near-black canvas
PANEL   = "#1a1a2e"      # card / axes background
ACCENT  = "#e94560"      # vivid red-pink accent
BLUE    = "#0f3460"      # deep navy
MUTED   = "#a8a8b3"      # secondary text
FG      = "#eaeaea"      # primary text
GRID    = "#2a2a3e"      # subtle grid lines

DARK_RC = {
    "figure.facecolor":  BG,
    "axes.facecolor":    PANEL,
    "axes.edgecolor":    GRID,
    "axes.labelcolor":   FG,
    "axes.grid":         True,
    "grid.color":        GRID,
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "text.color":        FG,
    "legend.facecolor":  PANEL,
    "legend.edgecolor":  GRID,
    "font.family":       "DejaVu Sans",
    "font.size":         11,
}


def _choose_scale(values):
    maxv = 0
    try:
        maxv = max(abs(float(v)) for v in values if v is not None)
    except Exception:
        maxv = 0
    if maxv >= 1e12:
        return 1e12, "Trillion"
    if maxv >= 1e9:
        return 1e9, "Billion"
    if maxv >= 1e6:
        return 1e6, "Million"
    if maxv >= 1e3:
        return 1e3, "Thousand"
    return 1, ""


def _apply_dark():
    plt.style.use("dark_background")
    plt.rcParams.update(DARK_RC)


# ─── Plot 1: Top-N Horizontal Bar Chart ──────────────────────────────────────
def plot_region_gdp(df: pd.DataFrame, region: str, year: int,
                    top_n: int = 12, return_fig: bool = False):
    df = df.copy()
    df["Value"] = df["Value"].astype(float)
    factor, unit = _choose_scale(df["Value"].tolist())
    df["Value_Scaled"] = df["Value"] / factor
    unit_label = f" ({unit} USD)" if unit else ""

    if top_n is None or top_n <= 0:
        top_n = len(df)

    df_sorted = df.sort_values("Value", ascending=False).reset_index(drop=True)
    top_df    = df_sorted.head(top_n).copy()
    others_sum = df_sorted["Value"].sum() - top_df["Value"].sum()

    figs = []
    _apply_dark()

    # ── Bar chart ──────────────────────────────────────────────────────────────
    fig1, ax1 = plt.subplots(figsize=(14, 7))
    figs.append(fig1)
    # 'turbo' stays vivid from min→max, unlike 'rocket' which starts near-black
    palette = ["#e94560", "#f28c38", "#f2d438", "#56cfad", "#00bfff",
               "#a78bfa", "#fb7185", "#34d399", "#fbbf24", "#60a5fa",
               "#f472b6", "#a3e635"]
    bar_colors = palette[:len(top_df)]
    bars = ax1.barh(
        y=top_df["Country Name"][::-1],
        width=top_df["Value_Scaled"][::-1],
        color=bar_colors[::-1],
        edgecolor="none",
        height=0.65
    )

    # data labels on bars
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + w * 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{w:,.1f}", va="center", ha="left",
                 fontsize=9, color=MUTED, fontweight="bold")

    ax1.set_title(f"Top {top_n} Countries by GDP — {region}  ({year})",
                  fontsize=16, fontweight="bold", color=FG, pad=14)
    ax1.set_xlabel(f"GDP {unit_label}", fontsize=12, color=MUTED)
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.1f}"))
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_facecolor(PANEL)
    fig1.tight_layout()
    if not return_fig:
        plt.show()

    # ── Donut chart ────────────────────────────────────────────────────────────
    pie_top = min(8, len(df_sorted))
    pie_df  = df_sorted.head(pie_top)
    pie_vals   = pie_df["Value"].tolist()
    pie_labels = pie_df["Country Name"].tolist()
    if others_sum > 0:
        pie_vals.append(others_sum)
        pie_labels.append("Others")
    pie_vals_scaled = [v / factor for v in pie_vals]

    fig2, ax2 = plt.subplots(figsize=(9, 9))
    figs.append(fig2)
    colors = ["#e94560", "#f28c38", "#f2d438", "#56cfad", "#00bfff",
              "#a78bfa", "#fb7185", "#34d399", "#fbbf24"]
    colors = colors[:len(pie_labels)]
    wedges, _, autotexts = ax2.pie(
        pie_vals_scaled,
        labels=None,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.42, edgecolor=BG, linewidth=2),
        pctdistance=0.78,
    )
    plt.setp(autotexts, size=9, weight="bold", color=FG)
    ax2.set_title(f"GDP Share — {region}  ({year})",
                  fontsize=15, fontweight="bold", color=FG, pad=18)
    legend_labels = [
        f"{n}  ({v:,.1f} {unit})" if unit else f"{n}  ({v:,.0f})"
        for n, v in zip(pie_labels, pie_vals_scaled)
    ]
    leg = ax2.legend(wedges, legend_labels, loc="center left",
                     bbox_to_anchor=(1.0, 0.5), fontsize=10, framealpha=0.2)
    for t in leg.get_texts():
        t.set_color(MUTED)
    fig2.set_facecolor(BG)
    fig2.tight_layout()
    if not return_fig:
        plt.show()

    return figs if return_fig else None


# ─── Plot 2: Histogram + Rank scatter ─────────────────────────────────────────
def plot_year_distribution(df: pd.DataFrame, year: int, return_fig: bool = False):
    df = df.copy()
    df["Value"] = df["Value"].astype(float)
    factor, unit = _choose_scale(df["Value"].tolist())
    df["Value_Scaled"] = df["Value"] / factor
    unit_label = f" ({unit} USD)" if unit else ""

    figs = []
    _apply_dark()

    # ── Histogram with log10 data transform ────────────────────────────────────
    # GDP data follows a power-law / log-normal distribution.
    # Plotting values directly creates one giant bar with all others negligible.
    # Standard fix: transform to log10 space → histogram becomes bell-shaped,
    # then relabel ticks with real GDP values.
    df_hist = df[df["Value_Scaled"] > 0].copy()
    df_hist["log_val"] = np.log10(df_hist["Value_Scaled"])

    fig1, ax1 = plt.subplots(figsize=(11, 6))
    figs.append(fig1)
    n, bins, patches = ax1.hist(
        df_hist["log_val"],
        bins=30,
        color=ACCENT,
        edgecolor="none",
        alpha=0.85,
        rwidth=0.88,
    )
    # KDE overlay in log10 space
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(df_hist["log_val"], bw_method=0.3)
        x_kde = np.linspace(df_hist["log_val"].min(), df_hist["log_val"].max(), 200)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(x_kde, kde(x_kde), color="#ffffff", linewidth=2, alpha=0.6)
        ax1_twin.set_yticks([])
        ax1_twin.set_facecolor(PANEL)
    except ImportError:
        pass  # scipy optional

    # Relabel X-axis ticks with real GDP values (10^tick)
    real_ticks = np.arange(
        np.floor(df_hist["log_val"].min()),
        np.ceil(df_hist["log_val"].max()) + 1
    )
    ax1.set_xticks(real_ticks)
    # Value_Scaled is already in `unit` (e.g. Trillion). 10^tick is value in that unit.
    def _tick_label(log_v):
        val = 10 ** log_v
        if val >= 1000:
            return f"{val/1000:.0f}k {unit}"
        if val >= 1:
            return f"{val:.1f} {unit}"
        if val >= 0.01:
            return f"{val:.2f} {unit}"
        return f"{val:.3f} {unit}"
    ax1.set_xticklabels(
        [_tick_label(t) for t in real_ticks],
        rotation=30, ha="right", fontsize=9, color=MUTED
    )
    ax1.set_title(f"GDP Distribution  ({year})",
                  fontsize=14, fontweight="bold", color=FG, pad=12)
    ax1.set_xlabel(f"GDP in {unit} USD" if unit else "GDP (USD)", fontsize=11, color=MUTED)
    ax1.set_ylabel("Number of Countries / Regions", fontsize=11, color=MUTED)
    ax1.set_facecolor(PANEL)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    fig1.tight_layout()
    if not return_fig:
        plt.show()

    # ── Rank Scatter ───────────────────────────────────────────────────────────
    # Use the DataFrame in its ORIGINAL (unsorted) order so points scatter naturally.
    # Only drop clear NaN rows.
    df_scatter = df.dropna(subset=["Value_Scaled"]).reset_index(drop=True)
    fig2, ax2 = plt.subplots(figsize=(11, 6))
    figs.append(fig2)
    sc = ax2.scatter(
        df_scatter.index,
        df_scatter["Value_Scaled"],
        c="#00e5ff",           # vivid cyan — clearly visible on dark background
        s=55,
        alpha=0.82,
        linewidths=0,
        zorder=3,
    )
    # Abbreviated Y-axis labels (no log scale)
    ax2.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: (
            f"{x/1000:.1f}T" if abs(x) >= 1000 else
            f"{x:.1f}B" if abs(x) >= 1 else f"{x*1000:.0f}M"
        ))
    )
    ax2.set_title(f"GDP Scatter  ({year})",
                  fontsize=14, fontweight="bold", color=FG, pad=12)
    ax2.set_xlabel("Dataset Index", fontsize=11, color=MUTED)
    ax2.set_ylabel(f"GDP {unit_label}", fontsize=11, color=MUTED)
    ax2.set_facecolor(PANEL)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    fig2.tight_layout()
    if not return_fig:
        plt.show()

    return figs if return_fig else None