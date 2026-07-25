"""
Simulated DB connection pool.

Why simulated instead of a real Postgres pool?
- Zero external dependencies (no DB server to install/manage/break during the hackathon)
- Fully deterministic and controllable — you decide exactly when/how it fails
- Behaves like a real pool: fixed size, blocking acquire, timeout, release

This is the "thing that breaks" in the Sentinel demo.
"""

import threading
import time
import random

from opentelemetry import trace

tracer = trace.get_tracer("checkout-service.pool")


class ConnectionPoolExhausted(Exception):
    pass


class ConnectionPool:
    def __init__(self, size: int = 20, checkout_timeout: float = 2.0):
        self._lock = threading.Lock()
        self.size = size
        self.checkout_timeout = checkout_timeout
        self._semaphore = threading.Semaphore(size)
        self.in_use = 0

    def resize(self, new_size: int):
        """Change pool size at runtime — used both to BREAK it (demo setup)
        and to FIX it (the agent's remediation action)."""
        with self._lock:
            self.size = new_size
            self._semaphore = threading.Semaphore(new_size)
            self.in_use = 0

    def acquire(self):
        """Block up to checkout_timeout seconds waiting for a free connection.
        Raises ConnectionPoolExhausted if none becomes available in time —
        this is what shows up as "connection pool exhausted" in logs."""
        with tracer.start_as_current_span("db.pool.acquire") as span:
            span.set_attribute("db.pool.size", self.size)
            span.set_attribute("db.pool.in_use", self.in_use)
            got_it = self._semaphore.acquire(timeout=self.checkout_timeout)
            if not got_it:
                span.set_attribute("db.pool.exhausted", True)
                span.set_status(trace.Status(trace.StatusCode.ERROR, "pool exhausted"))
                raise ConnectionPoolExhausted(
                    f"Timed out after {self.checkout_timeout}s waiting for a "
                    f"connection (pool size={self.size})"
                )
            with self._lock:
                self.in_use += 1

    def release(self):
        with self._lock:
            self.in_use = max(0, self.in_use - 1)
        self._semaphore.release()

    def simulate_query(self, base_latency_ms: int = 40):
        """Pretend to run a DB query. Adds a little jitter so traces look real."""
        with tracer.start_as_current_span("db.query") as span:
            latency = base_latency_ms + random.randint(0, 30)
            span.set_attribute("db.statement", "SELECT * FROM inventory WHERE sku = ?")
            time.sleep(latency / 1000)
            span.set_attribute("db.latency_ms", latency)
            return latency
