import asyncio
import random
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


async def with_backoff(
    func: Callable[[], Awaitable[T]],
    retries: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 2.5,
) -> T:
    last_exception = None
    for attempt in range(retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt == retries - 1:
                raise
            delay = min(max_delay, base_delay * (2**attempt)) + random.uniform(0, 0.2)
            await asyncio.sleep(delay)
    # This should never be reached, but type checker needs it
    if last_exception:
        raise last_exception
    raise RuntimeError("with_backoff: unexpected state")
