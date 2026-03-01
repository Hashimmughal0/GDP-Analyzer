import json
import os
import sys
from core.engine import TransformationEngine
from plugins.inputs import CsvReader, JsonReader
from plugins.outputs import ConsoleWriter, GraphicsChartWriter, UiWriter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DRIVERS = {
    "json": JsonReader,
    "csv":  CsvReader,
}

OUTPUT_DRIVERS = {
    "console": ConsoleWriter,
    "file":    GraphicsChartWriter,
    "ui":      UiWriter,
}


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bootstrap() -> None:
    config_path = os.path.join(BASE_DIR, "config/config.json")

    try:
        config = load_config(config_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] Failed to load config: {e}")
        sys.exit(1)

    in_type  = config.get("input",  "csv").lower()
    out_type = config.get("output", "ui").lower()

    if in_type not in INPUT_DRIVERS:
        print(f"[ERROR] Unsupported input type '{in_type}'. Valid: {list(INPUT_DRIVERS)}")
        sys.exit(1)

    if out_type not in OUTPUT_DRIVERS:
        print(f"[ERROR] Unsupported output type '{out_type}'. Valid: {list(OUTPUT_DRIVERS)}")
        sys.exit(1)

    sink         = OUTPUT_DRIVERS[out_type]()
    core_engine  = TransformationEngine(sink=sink, config=config)
    input_file   = os.path.join(BASE_DIR, config.get("input_file", "data/GDP_Data.csv"))
    input_source = INPUT_DRIVERS[in_type](core=core_engine, file_path=input_file)
    input_source.run()


def main() -> None:
    try:
        bootstrap()
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()