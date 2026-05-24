"""Rate-limiting / throttling for check runs and notifications.

Provides a simple token-bucket throttler that prevents depwatch from
spamming checks or alerts when many file-change events arrive in quick
succession.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ThrottleState:
    """Per-key throttle bucket."""
    tokens: float
    last_refill: float = field(default_factory=time.monotonic)

    def __str__(self) -> str:  # pragma: no cover
        return f"ThrottleState(tokens={self.tokens:.2f})"


@dataclass
class Throttler:
    """Token-bucket throttler.

    Args:
        rate:     tokens added per second.
        capacity: maximum token bucket size.
    """
    rate: float = 1.0
    capacity: float = 1.0
    _buckets: Dict[str, ThrottleState] = field(default_factory=dict, init=False, repr=False)

    # ------------------------------------------------------------------
    def _refill(self, state: ThrottleState) -> None:
        now = time.monotonic()
        elapsed = now - state.last_refill
        state.tokens = min(self.capacity, state.tokens + elapsed * self.rate)
        state.last_refill = now

    def allow(self, key: str = "default") -> bool:
        """Return True and consume one token if the key is not throttled."""
        if key not in self._buckets:
            self._buckets[key] = ThrottleState(tokens=self.capacity)
        state = self._buckets[key]
        self._refill(state)
        if state.tokens >= 1.0:
            state.tokens -= 1.0
            return True
        return False

    def reset(self, key: str = "default") -> None:
        """Fully refill the bucket for *key* (useful in tests)."""
        if key in self._buckets:
            self._buckets[key].tokens = self.capacity

    def reset_all(self) -> None:
        """Refill all buckets."""
        for state in self._buckets.values():
            state.tokens = self.capacity

    @property
    def tracked_keys(self) -> list:
        return list(self._buckets.keys())
