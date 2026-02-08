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


def plot_region_gdp(df: pd.DataFrame, region: str, year: int, top_n: int = 12):
    df = df.copy()
    df["Value"] = df["Value"].astype(float)

    factor, unit = _choose_scale(df["Value"].tolist())
    df["Value_Scaled"] = df["Value"] / factor
    unit_label = f" ({unit} USD)" if unit else ""

    
    if top_n is None or top_n <= 0:
        top_n = len(df)

    df_sorted = df.sort_values("Value", ascending=False).reset_index(drop=True)
    top_df = df_sorted.head(top_n)
    others_sum = df_sorted["Value"].sum() - top_df["Value"].sum()

   
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(data=top_df, x="Country Name", y="Value_Scaled", palette="tab20")
    plt.xticks(rotation=45, ha="right")
    plt.title(f"GDP by Country in {region} ({year})")
    plt.xlabel("Country")
    plt.ylabel(f"GDP{unit_label}")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:,.1f}"))
    plt.tight_layout()
    plt.show()

    
    pie_top = min(8, len(df_sorted))
    pie_df = df_sorted.head(pie_top).copy()
    pie_values = pie_df["Value"].tolist()
    pie_labels = pie_df["Country Name"].tolist()

    if others_sum > 0:
        pie_values.append(others_sum)
        pie_labels.append("Other")

    
    pie_values_scaled = [v / factor for v in pie_values]

    plt.figure(figsize=(8, 8))
    patches, texts, autotexts = plt.pie(pie_values_scaled, labels=None, autopct="%1.1f%%", startangle=140)
    plt.title(f"GDP Distribution in {region} ({year})")
    legend_labels = [f"{n} ({v:,.1f} {unit})" if unit else f"{n} ({v:,.0f})" for n, v in zip(pie_labels, pie_values_scaled)]
    plt.legend(patches, legend_labels, loc="best", fontsize="small")
    plt.tight_layout()
    plt.show()


def plot_year_distribution(df: pd.DataFrame, year: int):
    df = df.copy()
    df["Value"] = df["Value"].astype(float)
    factor, unit = _choose_scale(df["Value"].tolist())
    df["Value_Scaled"] = df["Value"] / factor
    unit_label = f" ({unit} USD)" if unit else ""

    
    plt.figure()
    sns.histplot(df["Value_Scaled"], bins=10, kde=True)
    plt.title(f"GDP Distribution Histogram ({year})")
    plt.xlabel(f"GDP{unit_label}")
    plt.ylabel("Frequency")
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:,.1f}"))
    plt.tight_layout()
    plt.show()

   
    plt.figure()
    sns.scatterplot(x=range(len(df)), y=df["Value_Scaled"])
    plt.title(f"GDP Scatter Plot ({year})")
    plt.xlabel("Index")
    plt.ylabel(f"GDP{unit_label}")
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:,.1f}"))
    plt.tight_layout()
    plt.show()