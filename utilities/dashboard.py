from utilities.data_processor import filter_data, compute_statistic
from utilities.visualizer import plot_region_gdp, plot_year_distribution
import pandas as pd

def run_dashboard(df, config):
    region = config["region"]
    year = config["year"]
    operation = config["operation"]

    filtered_list = filter_data(df, region, year)
    result = compute_statistic(filtered_list, operation)

    print("\nGDP ANALYTICS DASHBOARD")
    print("=" * 35)
    print(f"Region    : {region}")
    print(f"Year      : {year}")
    print(f"Operation : {operation.upper()}")
    print(f"Result    : {result:,.2f}")

    
    df_plot = pd.DataFrame(filtered_list)
    if "Country" in df_plot.columns and "Country Name" not in df_plot.columns:
        df_plot = df_plot.rename(columns={"Country": "Country Name"})

    plot_region_gdp(df_plot, region, year)
    plot_year_distribution(df_plot, year)