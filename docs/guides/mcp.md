# Running the Academy-MCP Plug-in
---
The Academy-MCP plug-in is an MCP server that connects to a (remote) Academy exchange instance.


## Installation
```[bash]
$ git clone git@github.com:academy-agents/academy-extensions.git
$ cd academy-extenstions
$ python -m venv venv
$ . ./venv/bin/activate
$ pip install -e .
```
Refer to the installation of academy-extensions for more details


## Running
To run the MCP server manually (i.e for testing or to connect to it as a remote MCP server), run:
```
$ python -m academy_extensions.mcp
```


To install it with claude desktop, using `uv`:
```
$ uv run mcp install academy_extensions/mcp.py
```

The exchange that the MCP server connects to defaults to the hosted exchange at https://exchange.academy-agents.org. To connect to a different exchange specify the url in an environment variable:
```
$ export ACADEMY_MCP_EXCHANGE_ADDRESS="https://dummy-address.org/exchange"
$ export ACADEMY_MCP_EXCHANGE_AUTH=1 # If the exchange uses globus auth
$ python -m academy_extensions.mcp
```

or to configure the environment when installing:
```
$ uv run mcp install academy_extensions/mcp.py -v ACADEMY_MCP_EXCHANGE_ADDRESS=...
```

**Note**: Only the `HttpExchangeFactory` is currently supported with the Academy-MCP plug-in. We are working to be able to configure other exchange types.

## Use
The MCP server discovers all agents that you have available to you and turns them in to MCP tools.
The discovery script is run every 5 minutes to find new agents.
You can manually discover agents using the `discover` tool, and add agents based on their `uid` using the `add_agent` tool.

Currently we do not support agent management functionality (i.e. shutting down agents, terminating mailboxes, etc.).
