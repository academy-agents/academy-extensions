from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from unittest import mock

import pytest
import pytest_asyncio
from academy.exchange import ExchangeFactory
from academy.handle import Handle
from academy.identifier import AgentId
from academy.manager import Manager
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)
from mcp.types import TextContent

from academy_extensions.mcp import add_agent
from academy_extensions.mcp import AppContext
from academy_extensions.mcp import discover
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


@pytest_asyncio.fixture
async def context_and_agent(
    http_exchange_factory: ExchangeFactory[Any],
) -> AsyncGenerator[
    tuple[Context[ServerSession, AppContext], Handle[IdentityAgent]]
]:
    async with await Manager.from_exchange_factory(
        factory=http_exchange_factory,
        executors=ThreadPoolExecutor(),
    ) as manager:
        id_agent = await manager.launch(IdentityAgent)
        async with await http_exchange_factory.create_user_client() as client:
            lifespan_context = AppContext(
                exchange_client=client,
                agents=set(),
            )
            ctx = mock.Mock()
            ctx.request_context.lifespan_context = lifespan_context
            yield ctx, id_agent


@pytest.mark.asyncio
async def test_add_agent(
    context_and_agent: tuple[
        Context[ServerSession, AppContext],
        Handle[IdentityAgent],
    ],
) -> None:
    server_context, agent = context_and_agent
    tools = await add_agent(server_context, agent.agent_id.uid)
    assert len(tools) == 2  # noqa: PLR2004
    assert format_name(agent.agent_id, 'identity') in tools
    agents = server_context.request_context.lifespan_context.agents
    assert agent.agent_id in agents


@pytest.mark.asyncio
async def test_discover(
    context_and_agent: tuple[
        Context[ServerSession, AppContext],
        Handle[IdentityAgent],
    ],
) -> None:
    server_context, agent = context_and_agent
    all_agents = await discover(server_context, 'Agent', 'academy.agent')
    assert len(all_agents) == 1
    assert agent.agent_id.uid in all_agents

    identity_agents = await discover(
        server_context,
        'IdentityAgent',
        'testing.agents',
    )
    assert len(identity_agents) == 1
    assert agent.agent_id.uid in all_agents


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

            await id_agent.shutdown()
            await manager.wait([id_agent])

            result = await client.call_tool(
                tool_name,
                {'args': ('hello',), 'kwargs': {}},
            )
            assert result.isError

            new_tools = await client.list_tools()
            assert len(new_tools.tools) == len(tools.tools) - 1
