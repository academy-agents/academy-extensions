from __future__ import annotations

from collections.abc import Generator
from typing import Any
from typing import Callable
from unittest import mock

import pytest


class MockServer:
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        self.tools: dict[str, tuple[Any, ...]] = {}

    def add_tool(
        self,
        method: Callable[..., Any],
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        assert name is not None
        self.tools[name] = (method, name, title, description)

    def remove_tool(self, name: str) -> None: # pragma: no cover
        if name in self.tools:
            del self.tools[name]


@pytest.fixture
def mock_fastmcp() -> Generator[MockServer]:
    mcp = MockServer()
    with mock.patch('mcp.server.fastmcp.FastMCP', return_value=mcp):
        yield mcp
