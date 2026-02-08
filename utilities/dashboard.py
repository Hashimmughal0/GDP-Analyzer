from utilities.data_processor import filter_data, compute_statistic
from utilities.visualizer import plot_region_gdp, plot_year_distribution, _choose_scale
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
   
    factor, unit = _choose_scale([result])
    scaled_result = result / factor
    unit_label = f" {unit} USD" if unit else " USD"
    print(f"Result    : {scaled_result:,.2f}{unit_label}")

    
    df_plot = pd.DataFrame(filtered_list)
    if "Country" in df_plot.columns and "Country Name" not in df_plot.columns:
        df_plot = df_plot.rename(columns={"Country": "Country Name"})

    top_n = config.get("top_n") if isinstance(config, dict) else None
    plot_region_gdp(df_plot, region, year, top_n=top_n)
    plot_year_distribution(df_plot, year)