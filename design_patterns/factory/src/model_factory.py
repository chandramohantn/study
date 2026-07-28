"""
Model Factory - Config-driven object creation.

This is the core of the Factory pattern. It does ONE thing:
given a name and parameters, create the right object.

Patterns used here:
- Factory: This file IS the factory
- Repository: Could be used to STORE created models
- Strategy: The models CREATED by the factory are strategies used by pipelines
"""

from typing import Any, Callable


class ModelFactory:
    """
    Registry-based model factory.

    Usage:
        factory = ModelFactory()
        factory.register("xgboost", create_xgboost)
        model = factory.create("xgboost", n_estimators=200)
    """

    def __init__(self):
        self._registry: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, creator: Callable[..., Any]) -> None:
        """
        Register a creator function under a name.

        Args:
            name: Identifier used in configs (e.g., "xgboost", "lightgbm")
            creator: A callable that accepts **kwargs and returns a model
        """
        if name in self._registry:
            raise ValueError(f"Model '{name}' is already registered. Use a different name.")
        self._registry[name] = creator

    def create(self, name: str, **kwargs) -> Any:
        """
        Create a model by name with given parameters.

        Args:
            name: Registered model name
            **kwargs: Parameters passed to the creator (override defaults)

        Returns:
            A ready-to-use model instance

        Raises:
            ValueError: If name is not registered
        """
        if name not in self._registry:
            available = self.available_models()
            raise ValueError(
                f"Unknown model: '{name}'. Available models: {available}"
            )
        creator = self._registry[name]
        return creator(**kwargs)

    def create_from_config(self, config: dict) -> Any:
        """
        Create a model from a config dictionary.

        Expected config format:
            {
                "algorithm": "xgboost",
                "hyperparameters": {"n_estimators": 200, "max_depth": 8}
            }
        """
        algorithm = config.get("algorithm")
        if not algorithm:
            raise ValueError("Config must have an 'algorithm' key")

        hyperparameters = config.get("hyperparameters", {})
        return self.create(algorithm, **hyperparameters)

    def available_models(self) -> list[str]:
        """List all registered model names."""
        return sorted(self._registry.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a model name is registered."""
        return name in self._registry


