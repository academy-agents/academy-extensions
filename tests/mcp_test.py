from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any

import pytest
import pytest_asyncio
from academy.exchange import ExchangeFactory
from academy.handle import Handle
from academy.manager import Manager
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)
from mcp.types import TextContent

from academy_extensions.mcp import update_tools
from academy_extensions.mcp import wrap_agent
from testing.agents import IdentityAgent
from testing.mcp import MockServer

MAX_TRIES = 5

logger = logging.getLogger(__name__)

@pytest_asyncio.fixture
async def agent(
    local_exchange_factory: ExchangeFactory[Any],
) -> AsyncGenerator[Handle[IdentityAgent]]:
    async with await Manager.from_exchange_factory(
        factory=local_exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        logger.debug(f"Launching agent")
        hdl = await manager.launch(IdentityAgent)
        logger.debug(f"Got handle.")
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
    local_exchange_factory: ExchangeFactory[Any],
    agent: Handle[Any],
) -> None:
    async with await local_exchange_factory.create_user_client() as client:
        updates = await update_tools(mock_fastmcp, set(), client)
        assert agent.agent_id in updates
        await updates[agent.agent_id]
        assert len(mock_fastmcp.tools) == 2  # noqa: PLR2004


@pytest.mark.asyncio
async def test_server(local_exchange_factory: ExchangeFactory[Any]):
    from academy_extensions.mcp import mcp  # noqa: PLC0415

    # For some reason run_stdio_async throws errors on clean up.
    # I don't think this is a bug with my implementation, but not sure.
    server_task = asyncio.create_task(mcp.run_sse_async())

    async with await Manager.from_exchange_factory(
        factory=local_exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        id_agent = await manager.launch(IdentityAgent)
        await mcp.call_tool(
            'add_agent',
            {'agent_uid': id_agent.agent_id.uid},
        )
        tools = mcp._tool_manager.list_tools()
        assert len(tools) > 1

        await id_agent.shutdown()

    server_task.cancel()


@pytest.mark.asyncio
async def test_client(http_exchange_factory: ExchangeFactory[Any]):
    from academy_extensions.mcp import mcp  # noqa: PLC0415

    async with await Manager.from_exchange_factory(
        factory=http_exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        id_agent = await manager.launch(IdentityAgent)
        tool_name = f'{id_agent.agent_id}-identity'
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool(
                'add_agent',
                {'agent_uid': id_agent.agent_id.uid},
            )
            tools = await client.list_tools()
            assert len(tools.tools) > 1
            result = await client.call_tool(
                tool_name,
                {'args': ('hello',), 'kwargs': {}},
            )
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert content.text == 'hello'
