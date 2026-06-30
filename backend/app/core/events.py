"""Internal event dispatcher — in-process pub/sub.

Usage in routers:
    from app.core.events import dispatch
    await dispatch("measurements.ingested", {"measurements": data})

Subscribers registered at startup in main.py:
    subscribe("measurements.ingested", websocket_broadcaster)
    subscribe("measurements.ingested", alarm_evaluator)
    subscribe("measurements.ingested", calc_signal_evaluator)
"""

import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

_subscribers: dict[str, list[Callable[[dict], Awaitable[Any]]]] = {}


def subscribe(event_type: str, handler: Callable[[dict], Awaitable[Any]]):
    """Register a handler for an event type."""
    if event_type not in _subscribers:
        _subscribers[event_type] = []
    _subscribers[event_type].append(handler)
    logger.debug("Subscribed handler %s to event '%s'", handler.__name__, event_type)


async def dispatch(event_type: str, data: dict):
    """Dispatch an event to all registered handlers.

    Each handler runs independently — a failure in one does not
    affect others (fire-and-forget with isolated exception handling).
    """
    handlers = _subscribers.get(event_type, [])
    if not handlers:
        return

    for handler in handlers:
        try:
            await handler(data)
        except Exception:
            logger.exception("Event handler %s failed for '%s'", handler.__name__, event_type)
