"""
Local File Repository Implementations — Real but simple.

These satisfy the Protocols using JSON files on disk.
Useful for local development, prototyping, or single-machine deployments.

No external dependencies — just Python stdlib (json, pathlib).
"""

from __future__ import annotations

import json
from pathlib import Path


class LocalFileFeatureRepository:
    """
    File-based implementation of FeatureRepository Protocol.

    Storage layout:
        base_path/
            features/
                {entity_id}.json   <- one file per entity
    """

    def __init__(self, base_path: str | Path) -> None:
        self._base = Path(base_path) / "features"
        self._base.mkdir(parents=True, exist_ok=True)

    def _entity_path(self, entity_id: str) -> Path:
        return self._base / f"{entity_id}.json"

    def get_features(self, entity_id: str) -> dict:
        path = self._entity_path(entity_id)
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def get_batch_features(self, entity_ids: list[str]) -> list[dict]:
        results = []
        for eid in entity_ids:
            features = self.get_features(eid)
            if features:
                results.append({"entity_id": eid, **features})
        return results

    def save_features(self, entity_id: str, features: dict) -> None:
        path = self._entity_path(entity_id)
        with open(path, "w") as f:
            json.dump(features, f, indent=2)


class LocalFilePredictionRepository:
    """
    File-based implementation of PredictionRepository Protocol.

    Storage layout:
        base_path/
            predictions/
                all_predictions.json   <- single file, append-style
    """

    def __init__(self, base_path: str | Path) -> None:
        self._base = Path(base_path) / "predictions"
        self._base.mkdir(parents=True, exist_ok=True)
        self._file = self._base / "all_predictions.json"

    def _load_all(self) -> list[dict]:
        if not self._file.exists():
            return []
        with open(self._file) as f:
            return json.load(f)

    def _save_all(self, predictions: list[dict]) -> None:
        with open(self._file, "w") as f:
            json.dump(predictions, f, indent=2)

    def save_prediction(self, prediction: dict) -> None:
        all_preds = self._load_all()
        all_preds.append(prediction)
        self._save_all(all_preds)

    def save_predictions(self, predictions: list[dict]) -> None:
        all_preds = self._load_all()
        all_preds.extend(predictions)
        self._save_all(all_preds)

    def get_predictions(self, model_id: str, limit: int = 100) -> list[dict]:
        all_preds = self._load_all()
        filtered = [p for p in all_preds if p.get("model_id") == model_id]
        return filtered[:limit]


