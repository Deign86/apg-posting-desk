from __future__ import annotations

from collections.abc import Callable
from time import sleep
from typing import TypeVar

T = TypeVar("T")


def retry(
    operation: Callable[[], T],
    *,
    attempts: int,
    delay_seconds: float,
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as error:
            last_error = error
            if attempt < attempts - 1 and delay_seconds:
                sleep(delay_seconds)

    if last_error is None:
        raise RuntimeError("retry operation did not run")
    raise last_error
