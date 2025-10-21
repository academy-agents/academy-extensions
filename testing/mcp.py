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
    ):
        self.tools: dict[str, tuple[Any, ...]] = {}

    def add_tool(
        self,
        method: Callable[..., Any],
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        if name is None:
            name = method.__name__

        self.tools[name] = (method, name, title, description)


@pytest.fixture
def mock_fastmcp() -> Generator[MockServer]:
    mcp = MockServer()
    with mock.patch('mcp.server.fastmcp.FastMCP', return_value=mcp):
        yield mcp
