"""
Model Creators - Each function knows HOW to create one type of model.

Each creator function:
1. Has sensible defaults
2. Accepts **kwargs to override defaults
3. Returns a ready-to-use model

This is where the Factory pattern meets the Strategy pattern:
- Factory creates the model (this file)
- The model is then USED as a strategy in a pipeline (training_pipeline.py)
"""

from typing import Any


# -- XGBoost Creator --

def create_xgboost(**kwargs) -> Any:
    """
    Create an XGBoost classifier with sensible defaults.

    Key defaults:
        n_estimators: 100
        max_depth: 6
        learning_rate: 0.1
    """
    from xgboost import XGBClassifier

    defaults = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "eval_metric": "logloss",
        "use_label_encoder": False,
        "random_state": 42,
        "verbosity": 0,
    }
    params = {**defaults, **kwargs}
    return XGBClassifier(**params)


# -- LightGBM Creator --

def create_lightgbm(**kwargs) -> Any:
    """
    Create a LightGBM classifier with sensible defaults.

    Key defaults:
        n_estimators: 100
        num_leaves: 31
        learning_rate: 0.1
    """
    from lightgbm import LGBMClassifier

    defaults = {
        "n_estimators": 100,
        "num_leaves": 31,
        "learning_rate": 0.1,
        "verbose": -1,
        "random_state": 42,
    }
    params = {**defaults, **kwargs}
    return LGBMClassifier(**params)


# -- Random Forest Creator --

def create_random_forest(**kwargs) -> Any:
    """
    Create a Random Forest classifier.

    Key defaults:
        n_estimators: 100
        max_depth: None (unlimited)
    """
    from sklearn.ensemble import RandomForestClassifier

    defaults = {
        "n_estimators": 100,
        "max_depth": None,
        "random_state": 42,
        "n_jobs": -1,
    }
    params = {**defaults, **kwargs}
    return RandomForestClassifier(**params)


# -- Logistic Regression Creator --

def create_logistic_regression(**kwargs) -> Any:
    """
    Create a Logistic Regression model (fast baseline).

    Key defaults:
        C: 1.0
        max_iter: 1000
    """
    from sklearn.linear_model import LogisticRegression

    defaults = {
        "C": 1.0,
        "max_iter": 1000,
        "random_state": 42,
    }
    params = {**defaults, **kwargs}
    return LogisticRegression(**params)


# -- Gradient Boosting Creator --

def create_gradient_boosting(**kwargs) -> Any:
    """
    Create a Gradient Boosting classifier (sklearn native).

    Key defaults:
        n_estimators: 100
        max_depth: 3
        learning_rate: 0.1
    """
    from sklearn.ensemble import GradientBoostingClassifier

    defaults = {
        "n_estimators": 100,
        "max_depth": 3,
        "learning_rate": 0.1,
        "random_state": 42,
    }
    params = {**defaults, **kwargs}
    return GradientBoostingClassifier(**params)


# -- Factory Setup --
# This function creates and configures the factory with all available models.
# Call this once at application startup.

def setup_factory():
    """
    Create a ModelFactory with all models registered.

    This is the SINGLE place where model registration happens.
    Adding a new model = add one register() call here.
    """
    from src.model_factory import ModelFactory

    factory = ModelFactory()
    factory.register("xgboost", create_xgboost)
    factory.register("lightgbm", create_lightgbm)
    factory.register("random_forest", create_random_forest)
    factory.register("logistic_regression", create_logistic_regression)
    factory.register("gradient_boosting", create_gradient_boosting)
    return factory


