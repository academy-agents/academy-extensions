"""MCP Server interface to Academy Exchange."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from academy.agent import Agent
from academy.exception import MailboxTerminatedError
from academy.exchange import ExchangeClient
from academy.exchange import HttpExchangeFactory
from academy.handle import Handle
from academy.identifier import AgentId
from mcp.server.fastmcp import Context
from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    exchange_client: ExchangeClient[Any]
    agents: set[AgentId[Any]] = field(default_factory=set)


def format_name(agent: AgentId[Any], action: str) -> str:
    """Format an agent action into a tool name."""
    return f'{agent.uid}_{action}'


async def wrap_agent(server: FastMCP, agent: Handle[Any]) -> dict[str, str]:
    """Wrap tool from agent for use by server."""
    logger.debug(f'Starting wrap agent for {agent.agent_id}')
    agent_info = await agent.agent_describe()
    logger.debug(f'Got description for {agent.agent_id}')
    tools: dict[str, str] = {}
    for action, description in agent_info.actions.items():
        name = format_name(agent.agent_id, action)

        async def invoke(
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
            name_: str = name,
            action_: str = action,
        ) -> Any:
            try:
                return await agent.action(action_, *args, **kwargs)
            except MailboxTerminatedError as e:
                server.remove_tool(name_)
                raise e

        desc = (
            f'This tool executes an action on agent {agent.agent_id}\n'
            f'Documentation: {description.doc}\n'
            f'Type Signature: {description.type_signature}\n'
            'Note: Arguments must be passed as `args`: a tuple of positional'
            'arguments and `kwargs`: a dictionary of key-word arguments.'
        )
        server.add_tool(
            invoke,
            name=name,
            title=action,
            description=desc,
        )
        tools[name] = desc
        logger.info(f'Added tool: {name}')

    return tools


async def update_tools(
    server: FastMCP,
    existing: set[AgentId[Any]],
    client: ExchangeClient[Any],
    base_class: type[Agent] = Agent,
    allow_subclasses: bool = True,
) -> dict[AgentId[Any], asyncio.Task[Any]]:
    """Update tools by discovering agents on the exchange."""
    update_futures: dict[AgentId[Any], asyncio.Task[Any]] = {}
    agent_ids = await client.discover(
        base_class,
        allow_subclasses=allow_subclasses,
    )
    new_agents = set(agent_ids) - existing
    for agent_id in new_agents:
        logger.info(f'Adding agent {agent_id}')
        agent = Handle(agent_id)
        # Create task in case agent is not online
        update_futures[agent_id] = asyncio.create_task(
            wrap_agent(server, agent),
        )
        existing.add(agent_id)

    return update_futures


async def refresh_loop(
    server: FastMCP,
    context: AppContext,
    interval_s: int = 300,
) -> None:
    """Regularly update the discovered tools."""
    tasks: list[asyncio.Task[Any]] = []
    try:
        while True:
            updates = await update_tools(
                server,
                context.agents,
                context.exchange_client,
            )
            tasks.extend(updates.values())
            await asyncio.sleep(interval_s)
    except asyncio.CancelledError as e:
        for task in tasks:
            task.cancel()

        raise e


@asynccontextmanager
async def app_lifespan(
    server: FastMCP,
) -> AsyncIterator[AppContext]:
    """Initialize exchange client for lifespan of server."""
    if 'ACADEMY_MCP_EXCHANGE_ADDRESS' in os.environ:
        url = os.environ['ACADEMY_MCP_EXCHANGE_ADDRESS']
        auth = 'globus' if 'ACADEMY_MCP_EXCHANGE_AUTH' in os.environ else None
        logger.info(f'Connection to exchange at {url}')
        exchange_factory = HttpExchangeFactory(
            url,
            auth_method=auth,  # type: ignore
        )
    else:  # pragma: no cover
        logger.info('Connection to exchange at dummy-address')
        exchange_factory = HttpExchangeFactory(
            'dummy-address',  #'https://exchange.academy-agents.org',
            auth_method='globus',
        )

    async with await exchange_factory.create_user_client() as client:
        logger.info('Connected to exchange')
        context = AppContext(exchange_client=client)
        refresh_task = asyncio.create_task(refresh_loop(server, context))
        yield context
        logger.info('Context exiting!')
        refresh_task.cancel()


mcp = FastMCP('MCP Academy Exchange Interface', lifespan=app_lifespan)


@mcp.tool()
async def add_agent(
    ctx: Context[ServerSession, AppContext],
    agent_uid: uuid.UUID,
) -> dict[str, str]:
    """Add agent to MCP server based on ID.

    Args:
        ctx: FastMCP context (provided)
        agent_uid: uuid of the agent to add to MCP server.

    Returns:
        A dictionary of newely added actions and their docs.
    """
    aid: AgentId[Any] = AgentId(uid=agent_uid)  # type: ignore[call-arg]
    agent: Handle[Any] = Handle(aid)
    return await wrap_agent(mcp, agent)


if __name__ == '__main__':
    mcp.run(transport='sse')
