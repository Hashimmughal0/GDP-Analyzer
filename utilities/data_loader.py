import csv
import os

def load_gdp_data(csv_path: str) -> list:
    if not os.path.exists(csv_path):
        raise FileNotFoundError("GDP CSV file not found")

    with open(csv_path, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)