"""
Adapter Pattern — Data Source Interface + Adapters

Demonstrates adapting different data sources (local files, in-memory)
to a single DataSource protocol your ETL/training pipeline uses.

In production you'd add S3Adapter, BigQueryAdapter, etc.
"""

from pathlib import Path
from typing import Protocol

import numpy as np


class DataSource(Protocol):
    """Your ETL pipeline codes against this interface."""

    def load_features(self, location: str) -> np.ndarray:
        """Load feature matrix from the given location."""
        ...

    def load_labels(self, location: str) -> np.ndarray:
        """Load label array from the given location."""
        ...

    def save(self, data: np.ndarray, location: str) -> None:
        """Persist data to the given location."""
        ...


class LocalFileAdapter:
    """Adapts numpy file I/O to the DataSource protocol.

    Supports .npy and .csv formats.
    """

    def __init__(self, base_dir: str = ".") -> None:
        self._base = Path(base_dir)

    def _resolve(self, location: str) -> Path:
        return self._base / location

    def load_features(self, location: str) -> np.ndarray:
        path = self._resolve(location)
        if path.suffix == ".npy":
            return np.load(path)
        elif path.suffix == ".csv":
            return np.loadtxt(path, delimiter=",", skiprows=1)
        raise ValueError(f"Unsupported format: {path.suffix}")

    def load_labels(self, location: str) -> np.ndarray:
        path = self._resolve(location)
        if path.suffix == ".npy":
            return np.load(path)
        elif path.suffix == ".csv":
            return np.loadtxt(path, delimiter=",", skiprows=1).astype(int)
        raise ValueError(f"Unsupported format: {path.suffix}")

    def save(self, data: np.ndarray, location: str) -> None:
        path = self._resolve(location)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".npy":
            np.save(path, data)
        elif path.suffix == ".csv":
            np.savetxt(path, data, delimiter=",")
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")


class InMemoryAdapter:
    """Adapts in-memory numpy arrays to the DataSource protocol.

    Useful for testing and local experimentation — no I/O needed.
    """

    def __init__(self) -> None:
        self._store: dict[str, np.ndarray] = {}

    def register(self, location: str, data: np.ndarray) -> None:
        """Pre-load data that will be 'read' from this location key."""
        self._store[location] = data

    def load_features(self, location: str) -> np.ndarray:
        if location not in self._store:
            raise FileNotFoundError(f"No data registered for '{location}'")
        return self._store[location]

    def load_labels(self, location: str) -> np.ndarray:
        if location not in self._store:
            raise FileNotFoundError(f"No data registered for '{location}'")
        return self._store[location]

    def save(self, data: np.ndarray, location: str) -> None:
        self._store[location] = data


