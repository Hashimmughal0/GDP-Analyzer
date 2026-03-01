import csv
import json
import os
from core.contracts import PipelineService


class CsvReader:
    def __init__(self, core: PipelineService, file_path: str):
        self.core = core
        self.file_path = file_path

    def run(self) -> None:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")
        try:
            with open(self.file_path, newline="", encoding="utf-8") as f:
                data = list(csv.DictReader(f))
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV '{self.file_path}': {e}") from e
        self.core.execute(data)


class JsonReader:
    def __init__(self, core: PipelineService, file_path: str):
        self.core = core
        self.file_path = file_path

    def run(self) -> None:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"JSON file not found: {self.file_path}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in '{self.file_path}': {e}") from e
        self.core.execute(data)