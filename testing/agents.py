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
