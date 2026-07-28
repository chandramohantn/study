"""Stack builder — assembles the decorator chain from a config dict.

This is how you'd wire up the Decorator pattern in a real ML service:
a config dict (from YAML, env vars, feature flags) determines which
layers are active. The core prediction logic never changes.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .core_predictor import ModelPredictor
from .decorators import (
    CachingDecorator,
    LoggingDecorator,
    TimingDecorator,
    ValidationDecorator,
)
from .predictor_interface import Predictor

logger = logging.getLogger(__name__)


def build_prediction_stack(model: Any, config: dict[str, Any]) -> Predictor:
    """Build a decorated prediction stack based on config.

    The stacking order (inside to outside):
        Core -> Validation -> Caching -> Timing -> Logging

    This means:
        - Logging sees everything (outermost)
        - Timing measures all inner layers
        - Caching short-circuits before validation+model on cache hits
        - Validation guards the model from bad inputs
        - Core just runs the model

    Args:
        model: A trained sklearn estimator with .predict() method.
        config: Dict controlling which decorators are active. Keys:
            - enable_validation (bool): Add input validation. Default True.
            - expected_features (int): Required if validation enabled.
            - enable_caching (bool): Add result caching. Default False.
            - cache_size (int): Max cached entries. Default 1000.
            - enable_timing (bool): Add latency tracking. Default True.
            - enable_logging (bool): Add request logging. Default True.

    Returns:
        A Predictor instance (possibly decorated multiple times).
    """
    # Innermost: the actual model
    predictor: Predictor = ModelPredictor(model)

    # Layer 1: Validation (closest to model)
    if config.get("enable_validation", True):
        expected = config.get("expected_features")
        if expected is None:
            raise ValueError(
                "Config has enable_validation=True but no 'expected_features' set."
            )
        predictor = ValidationDecorator(predictor, expected_features=expected)

    # Layer 2: Caching (above validation)
    if config.get("enable_caching", False):
        cache_size = config.get("cache_size", 1000)
        predictor = CachingDecorator(predictor, max_size=cache_size)

    # Layer 3: Timing
    if config.get("enable_timing", True):
        predictor = TimingDecorator(predictor)

    # Layer 4: Logging (outermost)
    if config.get("enable_logging", True):
        predictor = LoggingDecorator(predictor)

    return predictor


