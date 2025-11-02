"""Run the MCP server connected to non-empty local exchange."""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ProcessPoolExecutor

from academy.agent import action
from academy.agent import Agent
from academy.exchange.cloud.client import spawn_http_exchange
from academy.logging import init_logging
from academy.manager import Manager
from academy.socket import open_port

from academy_extensions.mcp import mcp


class SimulationAgent(Agent):
    """This is a simulation agent."""

    @action
    async def ionization_energy(self, chemical: str) -> float:
        """Simulates the ionization energy of molecule.

        Args:
            chemical: Molecule given as a SMILES string.

        Returns:
            The ionization energy in micro-joules
        """
        return 0.5


async def main() -> None:
    """Run example MCP server.

    This script does three things to create an isolated running MCP:
    1. Launches a local HTTP exchange
    2. Populates the exchange with an agent.
    3. Starts the academy-mcp connected to the local exchange.
    This allows an example MCP server to run without querying the cloud
    exchange.
    """
    init_logging()

    with spawn_http_exchange(
        host='0.0.0.0',
        port=open_port(),
    ) as exchange_factory:
        async with await Manager.from_exchange_factory(
            factory=exchange_factory,
            executors=ProcessPoolExecutor(
                max_workers=1,
                initializer=init_logging,
            ),
        ) as manager:
            os.environ['ACADEMY_MCP_EXCHANGE_ADDRESS'] = (
                exchange_factory._info.url
            )
            await manager.launch(SimulationAgent)
            await mcp.run_sse_async()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
