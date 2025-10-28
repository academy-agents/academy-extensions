import asyncio
from concurrent.futures import ProcessPoolExecutor
import os

from academy.agent import Agent
from academy.agent import action
from academy.exchange.cloud.client import spawn_http_exchange
from academy.socket import open_port
from academy.manager import Manager
from academy.logging import init_logging

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
    
async def main():
    init_logging()

    with spawn_http_exchange(host="0.0.0.0", port=open_port()) as exchange_factory:
        async with await Manager.from_exchange_factory(
            factory=exchange_factory,
            executors=ProcessPoolExecutor(
                max_workers=1,
                initializer=init_logging,
            )
        ) as manager:
            os.environ['ACADEMY_MCP_EXCHANGE_ADDRESS'] = exchange_factory._info.url
            await manager.launch(SimulationAgent)
            await mcp.run_sse_async()

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))