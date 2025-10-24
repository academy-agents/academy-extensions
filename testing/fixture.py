from __future__ import annotations

import logging
import os
import socket
from collections.abc import AsyncGenerator
from typing import Any
from unittest import mock

import pytest_asyncio
from academy.exchange import ExchangeFactory
from academy.exchange import LocalExchangeFactory
from academy.exchange.cloud import spawn_http_exchange

_used_ports: set[int] = set()


def open_port() -> int:
    """Return open port.

    Source: https://stackoverflow.com/questions/2838244
    """
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        if port not in _used_ports:  # pragma: no branch
            _used_ports.add(port)
            return port


@pytest_asyncio.fixture
async def http_exchange_factory() -> AsyncGenerator[ExchangeFactory[Any]]:
    host = '0.0.0.0'
    port = open_port()
    address = f'http://{host}:{port}'
    env = {
        'ACADEMY_MCP_EXCHANGE_ADDRESS': address,
    }
    with (
        mock.patch.dict(os.environ, env),
        spawn_http_exchange(
            host=host,
            port=port,
            level=logging.DEBUG,
            timeout=2,
        ) as exchange,
    ):
        yield exchange

@pytest_asyncio.fixture
async def local_exchange_factory() -> ExchangeFactory[Any]:
    factory = LocalExchangeFactory()
    return factory
