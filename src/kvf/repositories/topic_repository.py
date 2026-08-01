# src/kvf/repositories/topic_repository.py

import csv
from pathlib import Path

from kvf.models.topic import Topic


class TopicRepository:

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def get_first(self) -> Topic:

        with self.csv_path.open(
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)
            row = next(reader)

        return Topic.model_validate(row)