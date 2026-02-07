import json
import os

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError("Config file not found")

    with open(config_path, "r") as file:
        config = json.load(file)

    required_fields = ["region", "year", "operation", "output"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing configuration field: {field}")

    if config["operation"] not in ["average", "sum"]:
        raise ValueError("Operation must be 'average' or 'sum'")

    if not isinstance(config["year"], int):
        raise ValueError("Year must be an integer")

    return config