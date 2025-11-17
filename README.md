# Academy Extensions
[![docs](https://github.com/academy-agents/academy-extensions/actions/workflows/docs.yml/badge.svg)](https://github.com/academy-agents/academy-extensions/actions)
[![tests](https://github.com/academy-agents/academy-extensions/actions/workflows/tests.yml/badge.svg)](https://github.com/academy-agents/academy-extensions/actions)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/academy-agents/academy-extensions/main.svg)](https://results.pre-commit.ci/latest/github/academy-agents/academy-extensions/main)

`academy-extensions` provides additional functionality that is adjacent to the core capabilities of `academy` and therefore not packaged with the rest of `academy` since it is not needed by all users.

## Installation

Install via github:
```
git clone git@github.com:academy-agents/academy-extensions.git
cd academy-extenstions
python -m venv venv
. ./venv/bin/activate
pip install -e .
```

For local development:
```
$ tox --devenv venv -e py310
$ pre-commit install
```
or
```
$ pip install -e .[dev]
```

## Modules

Academy-extensions currently provides the following modules:

 - [Academy MCP Plug-in](guides/mcp.md)
