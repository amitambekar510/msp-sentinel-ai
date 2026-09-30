import asyncio
import time
from collections.abc import Awaitable, Callable


class CircuitBreaker:
    def __init__(self, threshold: int = 3, cooldown: int = 120):
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.opened_at: float | None = None

    async def run(self, call: Callable[[], Awaitable[list]]):
        if self.opened_at and time.time() - self.opened_at < self.cooldown:
            raise RuntimeError("circuit open")
        try:
            result = await call()
            self.failures = 0
            self.opened_at = None
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = time.time()
            raise


async def retry(call: Callable[[], Awaitable[list]], attempts: int = 2):
    error = None
    for attempt in range(attempts):
        try:
            return await call()
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                await asyncio.sleep(0.4 * (attempt + 1))
    raise error
