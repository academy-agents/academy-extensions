from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
import pytest_asyncio
from academy.exchange import ExchangeFactory
from academy.handle import Handle
from academy.identifier import AgentId
from academy.manager import Manager
from mcp.server.fastmcp.exceptions import ToolError
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)
from mcp.types import TextContent

from academy_extensions.mcp import format_name
from academy_extensions.mcp import update_tools
from academy_extensions.mcp import wrap_agent
from testing.agents import IdentityAgent
from testing.mcp import MockServer

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def agent(
    local_exchange_factory: ExchangeFactory[Any],
) -> AsyncGenerator[Handle[IdentityAgent]]:
    async with await Manager.from_exchange_factory(
        factory=local_exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        logger.debug('Launching agent')
        hdl = await manager.launch(IdentityAgent)
        logger.debug('Got handle.')
        yield hdl
        await hdl.shutdown()


def test_format_name():
    agent: AgentId[Any] = AgentId.new()
    name = format_name(agent, 'simulate')
    assert str(agent.uid) in name
    assert 'simulate' in name


@pytest.mark.asyncio
async def test_wrap_agent(
    mock_fastmcp: MockServer,
    agent: Handle[Any],
) -> None:
    tools = await wrap_agent(mock_fastmcp, agent)

    tool = format_name(agent.agent_id, 'identity')
    assert len(mock_fastmcp.tools) == 2  # noqa: PLR2004
    assert tool in mock_fastmcp.tools
    assert tool in tools


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
async def test_server_call_tool(local_exchange_factory: ExchangeFactory[Any]):
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

        tool_name = format_name(id_agent.agent_id, 'identity')
        result = await mcp._tool_manager.call_tool(
            tool_name,
            {'args': ('hello',), 'kwargs': {}},
        )
        assert result == 'hello'

        await id_agent.shutdown()
        await manager.wait([id_agent])

        with pytest.raises(ToolError):
            await mcp._tool_manager.call_tool(
                tool_name,
                {'args': ('hello',), 'kwargs': {}},
            )

        new_tools = mcp._tool_manager.list_tools()
        assert len(new_tools) == len(tools) - 1

    server_task.cancel()


@pytest.mark.asyncio
async def test_client(http_exchange_factory: ExchangeFactory[Any]):
    from academy_extensions.mcp import mcp  # noqa: PLC0415

    async with await Manager.from_exchange_factory(
        factory=http_exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        id_agent = await manager.launch(IdentityAgent)
        tool_name = format_name(id_agent.agent_id, 'identity')
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
