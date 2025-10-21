from __future__ import annotations

from typing import TypeVar

from academy.agent import action
from academy.agent import Agent

T = TypeVar('T')


class IdentityAgent(Agent):
    """Agent that echoes any value"""

    @action
    async def identity(self, value: T) -> T:
        """Echo the provided value.

        Args:
            value: Any value.

        Returns:
            The same value.
        """
        return value


class CounterAgent(Agent):
    def __init__(self) -> None:
        super().__init__()
        self._count = 0

    async def agent_on_startup(self) -> None:
        self._count = 0

    @action
    async def add(self, value: int) -> None:
        self._count += value

    @action
    async def count(self) -> int:
        return self._count
