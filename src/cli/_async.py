"""Async runner helper for CLI commands."""

import asyncio
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")


def run(coro: Coroutine[None, None, T]) -> T:
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
