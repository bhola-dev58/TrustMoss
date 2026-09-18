"""
tracer.py — Lightweight per-stage latency tracker.

Usage:
    tracer = Tracer()
    with tracer.stage("moss_retrieval"):
        results = await moss_client.query(...)

    trace = tracer.get_trace()
    # [{"stage": "moss_retrieval", "duration_ms": 12.4}, ...]
"""

from contextlib import contextmanager
import time


class StageTimer:
    def __init__(self, name: str):
        self.name = name
        self.start_time: float = 0.0
        self.duration_ms: float = 0.0

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.duration_ms = round((time.perf_counter() - self.start_time) * 1000, 2)


class Tracer:
    def __init__(self):
        self._timers: list[StageTimer] = []

    @contextmanager
    def stage(self, name: str):
        timer = StageTimer(name)
        self._timers.append(timer)
        timer.start()
        try:
            yield timer
        finally:
            timer.stop()

    def get_trace(self) -> list[dict]:
        return [{"stage": t.name, "duration_ms": t.duration_ms} for t in self._timers]

    def total_ms(self) -> float:
        return round(sum(t.duration_ms for t in self._timers), 2)
