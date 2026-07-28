"""
Event infrastructure for CQRS pattern.

The EventBus decouples the command side from the query side.
Command handlers publish events; query handlers subscribe to them.
In production, replace with Kafka, Redis Pub/Sub, or SQS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class Event:
    """Domain event representing something that happened."""

    event_type: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return (
            f"Event(type={self.event_type!r}, "
            f"payload={self.payload}, "
            f"ts={self.timestamp:%H:%M:%S})"
        )


class EventBus:
    """
    Simple in-process event bus (dict-based).

    Decouples publishers (command side) from subscribers (query side).
    Handlers are invoked synchronously when an event is published.

    In production, swap this for:
      - Redis Pub/Sub (low latency, acceptable loss)
      - Kafka (durable, ordered, high throughput)
      - AWS SQS/SNS (managed, scalable)
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._history: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Register a handler for a specific event type."""
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers."""
        self._history.append(event)
        for handler in self._subscribers.get(event.event_type, []):
            handler(event)

    @property
    def history(self) -> list[Event]:
        """All events published through this bus (useful for debugging/testing)."""
        return list(self._history)

    def clear(self) -> None:
        """Reset subscribers and history."""
        self._subscribers.clear()
        self._history.clear()


