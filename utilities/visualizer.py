import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.ticker as ticker

sns.set(style="whitegrid")


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


def plot_region_gdp(df: pd.DataFrame, region: str, year: int):
    df = df.copy()
    df["Value"] = df["Value"].astype(float)

    factor, unit = _choose_scale(df["Value"].tolist())
    df["Value_Scaled"] = df["Value"] / factor
    unit_label = f" ({unit} USD)" if unit else ""

    # Bar Chart
    plt.figure()
    ax = sns.barplot(data=df, x="Country Name", y="Value_Scaled")
    plt.xticks(rotation=90)
    plt.title(f"GDP by Country in {region} ({year})")
    plt.xlabel("Country")
    plt.ylabel(f"GDP{unit_label}")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:,.1f}"))
    plt.tight_layout()
    plt.show()

    # Pie Chart 
    plt.figure()
    values = df["Value_Scaled"].tolist()
    labels = df["Country Name"].tolist()
    patches, texts, autotexts = plt.pie(values, labels=None, autopct="%1.1f%%")
    plt.title(f"GDP Distribution in {region} ({year})")
    # Build legend with formatted values
    legend_labels = [f"{n} ({v:,.1f} {unit})" if unit else f"{n} ({v:,.0f})" for n, v in zip(labels, df["Value_Scaled"].tolist())]
    plt.legend(patches, legend_labels, loc="best", fontsize="small")
    plt.tight_layout()
    plt.show()


def plot_year_distribution(df: pd.DataFrame, year: int):
    df = df.copy()
    df["Value"] = df["Value"].astype(float)
    factor, unit = _choose_scale(df["Value"].tolist())
    df["Value_Scaled"] = df["Value"] / factor
    unit_label = f" ({unit} USD)" if unit else ""

    # Histogram
    plt.figure()
    sns.histplot(df["Value_Scaled"], bins=10, kde=True)
    plt.title(f"GDP Distribution Histogram ({year})")
    plt.xlabel(f"GDP{unit_label}")
    plt.ylabel("Frequency")
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:,.1f}"))
    plt.tight_layout()
    plt.show()

    # Scatter Plot
    plt.figure()
    sns.scatterplot(x=range(len(df)), y=df["Value_Scaled"])
    plt.title(f"GDP Scatter Plot ({year})")
    plt.xlabel("Index")
    plt.ylabel(f"GDP{unit_label}")
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:,.1f}"))
    plt.tight_layout()
    plt.show()