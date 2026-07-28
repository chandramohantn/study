"""
Resilient ML Inference Service
===============================

Demonstrates combining Retry + Circuit Breaker to build a resilient
ML inference pipeline that calls:
  1. A feature store (to fetch user features)
  2. A model API (to get predictions)

Both are SIMULATED — no real external services required.
Failures are controlled via counters so you can see the patterns in action.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict

from src.retry import retry
from src.circuit_breaker import CircuitBreaker

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Simulated External Services (fail N times, then succeed)
# =============================================================================


@dataclass
class SimulatedService:
    """
    Simulates an external service that fails a configurable number of times
    before succeeding. Useful for testing retry/circuit-breaker behavior.
    """

    name: str
    failures_before_success: int = 3
    _call_count: int = field(default=0, init=False)

    def call(self, payload: Any = None) -> Dict[str, Any]:
        """Simulate a service call. Raises ConnectionError on failure calls."""
        self._call_count += 1
        if self._call_count <= self.failures_before_success:
            raise ConnectionError(
                f"[{self.name}] Service unavailable "
                f"(call {self._call_count}/{self.failures_before_success} failures)"
            )
        return {
            "service": self.name,
            "status": "success",
            "call_number": self._call_count,
            "payload": payload,
        }

    def reset(self) -> None:
        """Reset the call counter."""
        self._call_count = 0


# =============================================================================
# ML Inference Service with Retry + Circuit Breaker
# =============================================================================


class MLInferenceService:
    """
    An ML inference service that fetches features and calls a model API,
    protected by retry logic and a circuit breaker.

    Architecture:
        Request -> [Circuit Breaker check] -> [Retry wrapper] -> External Service
                                                                    | (if all fail)
                                                              Fallback Response
    """

    def __init__(self):
        # Circuit breakers for each dependency
        self.feature_store_breaker = CircuitBreaker(
            name="feature-store",
            failure_threshold=3,
            recovery_timeout=5.0,
            success_threshold=2,
        )
        self.model_api_breaker = CircuitBreaker(
            name="model-api",
            failure_threshold=3,
            recovery_timeout=5.0,
            success_threshold=2,
        )

        # Simulated external services
        self._feature_store = SimulatedService(
            name="FeatureStore", failures_before_success=2
        )
        self._model_api = SimulatedService(
            name="ModelAPI", failures_before_success=4
        )

    def predict(self, user_id: str) -> Dict[str, Any]:
        """
        Full inference pipeline:
        1. Fetch features from feature store (with retry + circuit breaker)
        2. Call model API for prediction (with retry + circuit breaker)
        3. Return prediction or fallback
        """
        logger.info(f"{'='*60}")
        logger.info(f"Prediction request for user_id={user_id}")

        # Step 1: Get features
        features = self._get_features_with_resilience(user_id)

        # Step 2: Get prediction
        prediction = self._get_prediction_with_resilience(features)

        return prediction

    def _get_features_with_resilience(self, user_id: str) -> Dict[str, Any]:
        """Fetch features with circuit breaker + retry protection."""
        if not self.feature_store_breaker.allow_request():
            logger.warning("Feature store circuit OPEN — using cached features")
            return self._fallback_features(user_id)

        try:
            features = self._fetch_features_with_retry(user_id)
            self.feature_store_breaker.record_success()
            return features
        except Exception as e:
            self.feature_store_breaker.record_failure()
            logger.error(f"Feature store call failed: {e}")
            return self._fallback_features(user_id)

    @retry(max_attempts=3, base_delay=0.1, backoff_factor=2.0,
           retryable_exceptions=(ConnectionError,))
    def _fetch_features_with_retry(self, user_id: str) -> Dict[str, Any]:
        """Fetch features from the feature store (retries on transient errors)."""
        result = self._feature_store.call(payload={"user_id": user_id})
        return result.get("payload", {})

    def _get_prediction_with_resilience(
        self, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call model API with circuit breaker + retry protection."""
        if not self.model_api_breaker.allow_request():
            logger.warning("Model API circuit OPEN — using fallback prediction")
            return self._fallback_prediction(features)

        try:
            prediction = self._call_model_with_retry(features)
            self.model_api_breaker.record_success()
            return prediction
        except Exception as e:
            self.model_api_breaker.record_failure()
            logger.error(f"Model API call failed: {e}")
            return self._fallback_prediction(features)

    @retry(max_attempts=2, base_delay=0.1, backoff_factor=2.0,
           retryable_exceptions=(ConnectionError,))
    def _call_model_with_retry(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Call the model API (retries on transient errors)."""
        self._model_api.call(payload=features)
        return {"prediction": 0.87, "model": "xgboost-v2", "source": "live"}

    # =========================================================================
    # Fallback Logic
    # =========================================================================

    @staticmethod
    def _fallback_features(user_id: str) -> Dict[str, Any]:
        """Return cached/default features when the feature store is down."""
        logger.info(f"Using fallback features for user {user_id}")
        return {
            "user_id": user_id,
            "avg_session_duration": 300.0,
            "total_purchases": 5,
            "source": "fallback_cache",
        }

    @staticmethod
    def _fallback_prediction(features: Dict[str, Any]) -> Dict[str, Any]:
        """Return a safe default prediction when the model API is down."""
        logger.info("Using fallback prediction (conservative default)")
        return {
            "prediction": 0.5,
            "model": "fallback-rule-based",
            "source": "fallback",
            "note": "Model API unavailable, using default score",
        }


# =============================================================================
# Demo: Run the service and observe retry + circuit breaker behavior
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  CIRCUIT BREAKER + RETRY DEMO — ML Inference Service")
    print("=" * 70)
    print()
    print("This demo simulates:")
    print("  - Feature Store: fails 2 times, then succeeds")
    print("  - Model API: fails 4 times, then succeeds")
    print("  - Circuit breaker threshold: 3 failures -> OPEN")
    print("  - Retry: up to 3 attempts for feature store, 2 for model API")
    print()

    service = MLInferenceService()

    # Make several prediction requests to see the patterns
    for i in range(6):
        print(f"\n{'─'*70}")
        print(f"  REQUEST {i + 1}")
        print(f"{'─'*70}")

        result = service.predict(user_id=f"user_{i + 1}")
        print(f"\n  Result: {result}")

        # Show circuit breaker states
        print(f"\n  Circuit States:")
        print(
            f"    Feature Store: {service.feature_store_breaker.state.value} "
            f"(failures: {service.feature_store_breaker.failure_count})"
        )
        print(
            f"    Model API:     {service.model_api_breaker.state.value} "
            f"(failures: {service.model_api_breaker.failure_count})"
        )

    print(f"\n{'='*70}")
    print("  DEMO COMPLETE")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  1. Retry handles transient failures (feature store recovered)")
    print("  2. Circuit breaker prevents hammering a dead service (model API)")
    print("  3. Fallback logic ensures graceful degradation")
    print("  4. The system never crashes — it degrades gracefully")


