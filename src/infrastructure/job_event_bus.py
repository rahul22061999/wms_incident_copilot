"""
In-process pub/sub bus for job completion events.

Replaces the polling loop that previously hit the DB every second. When a
monitoring job finishes, MonitoringJobRunner calls publish(); every SSE stream
that subscribed for that ticket wakes up immediately with the result.

Design constraints:
- asyncio.Queue per subscriber (not one shared queue) so each SSE connection
  receives its own independent stream of events without racing other consumers.
- put_nowait instead of await put() because publish() is called from sync
  APScheduler job callbacks that cannot await. The queue is unbounded so
  put_nowait never raises QueueFull in normal operation.
- This bus is in-process only. Running uvicorn with multiple workers would
  require a real broker (Redis pub/sub, etc.).
"""

from __future__ import annotations

import asyncio
from collections import defaultdict


class JobEventBus:
    """In-process pub/sub: job runner publishes, SSE streams subscribe."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, ticket_number: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[ticket_number].append(q)
        return q

    def unsubscribe(self, ticket_number: str, q: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(ticket_number, [])
        try:
            subscribers.remove(q)
        except ValueError:
            pass

    def publish(self, ticket_number: str, event: dict) -> None:
        for q in self._subscribers.get(ticket_number, []):
            q.put_nowait(event)
