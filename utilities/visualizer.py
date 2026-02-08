import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set(style="whitegrid")

def plot_region_gdp(df: pd.DataFrame, region: str, year: int):
    # Bar Chart
    plt.figure()
    sns.barplot(
        data=df,
        x="Country Name",
        y="Value"
    )
    plt.xticks(rotation=90)
    plt.title(f"GDP by Country in {region} ({year})")
    plt.xlabel("Country")
    plt.ylabel("GDP")
    plt.tight_layout()
    plt.show()

    # Pie Chart
    plt.figure()
    plt.pie(
        df["Value"],
        labels=df["Country Name"],
        autopct="%1.1f%%"
    )
    plt.title(f"GDP Distribution in {region} ({year})")
    plt.show()


def plot_year_distribution(df: pd.DataFrame, year: int):
    # Histogram
    plt.figure()
    sns.histplot(df["Value"], bins=10, kde=True)
    plt.title(f"GDP Distribution Histogram ({year})")
    plt.xlabel("GDP")
    plt.ylabel("Frequency")
    plt.show()

    # Scatter Plot
    plt.figure()
    sns.scatterplot(
        x=range(len(df)),
        y=df["Value"]
    )
    plt.title(f"GDP Scatter Plot ({year})")
    plt.xlabel("Index")
    plt.ylabel("GDP")
    plt.show()