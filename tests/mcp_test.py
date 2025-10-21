from __future__ import annotations

from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
import pytest_asyncio
from academy.exchange import ExchangeFactory
from academy.handle import Handle
from academy.manager import Manager

from academy_extensions.mcp import update_tools
from academy_extensions.mcp import wrap_agent
from testing.agents import IdentityAgent
from testing.mcp import MockServer


@pytest_asyncio.fixture
async def agent(
    exchange_factory: ExchangeFactory[Any],
) -> AsyncGenerator[Handle[IdentityAgent]]:
    async with await Manager.from_exchange_factory(
        factory=exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        hdl = await manager.launch(IdentityAgent)
        yield hdl
        await hdl.shutdown()


@pytest.mark.asyncio
async def test_wrap_agent(
    mock_fastmcp: MockServer,
    agent: Handle[Any],
) -> None:
    await wrap_agent(mock_fastmcp, agent)

    assert len(mock_fastmcp.tools) == 2  # noqa: PLR2004
    assert f'{agent.agent_id}-identity' in mock_fastmcp.tools


@pytest.mark.asyncio
async def test_update_tools(
    mock_fastmcp: MockServer,
    exchange_factory: ExchangeFactory[Any],
    agent: Handle[Any],
) -> None:
    async with await exchange_factory.create_user_client() as client:
        updates = await update_tools(mock_fastmcp, set(), client)
        assert agent.agent_id in updates
        await updates[agent.agent_id]
        assert len(mock_fastmcp.tools) == 2  # noqa: PLR2004


def test_refresh_loop(): ...


def test_app_has_tools(): ...


def test_add_agent(): ...
