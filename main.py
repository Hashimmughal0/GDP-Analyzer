from utilities.config_loader import load_config
from utilities.data_loader import load_gdp_data
from utilities.data_cleaner import clean_data

CONFIG_PATH = "config/config.json"
DATA_PATH = "data/GDP_Data.csv"

def main():
    try:
        config = load_config(CONFIG_PATH)
        raw_data = load_gdp_data(DATA_PATH)
        clean_dataset = clean_data(raw_data)

    except Exception as e:
        print("ERROR:", str(e))


if __name__ == "__main__":
    main()