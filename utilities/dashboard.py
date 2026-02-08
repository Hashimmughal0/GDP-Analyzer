from utilities.data_processor import filter_data, compute_statistic
from utilities.visualizer import plot_region_gdp, plot_year_distribution

def run_dashboard(df, config):
    region = config["region"]
    year = config["year"]
    operation = config["operation"]

    filtered_df = filter_data(df, region, year)
    result = compute_statistic(filtered_df, operation)

    print("\nGDP ANALYTICS DASHBOARD")
    print("=" * 35 show)
    print(f"Region    : {region}")
    print(f"Year      : {year}")
    print(f"Operation : {operation.upper()}")
    print(f"Result    : {result:,.2f}")

    plot_region_gdp(filtered_df, region, year)
    plot_year_distribution(filtered_df, year)