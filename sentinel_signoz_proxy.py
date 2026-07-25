"""
sentinel_signoz_proxy.py

A minimal, custom replacement for the `mcp-remote` npm bridge tool.

WHY THIS EXISTS: mcp-remote kept crashing when spawned by Claude Desktop with
"HTTP 404: Invalid OAuth error response" — it was attempting OAuth dynamic
client registration against SigNoz's MCP server (which only needs a simple
API key header, no OAuth at all), got a plain 404 back, and crashed trying to
parse it as JSON. This happened consistently via Desktop even though a manual
terminal test worked once — not worth debugging a third-party tool's internal
auth-fallback logic under time pressure.

WHAT THIS DOES INSTEAD: connects to SigNoz's MCP server using ONLY the
SIGNOZ-API-KEY header (the same one already curl-verified as HTTP 200), lists
whatever tools SigNoz exposes, and transparently forwards every tool call
between Claude Desktop (stdio) and SigNoz (streamable HTTP). No OAuth code
path exists in this file at all, so the mcp-remote bug class is impossible
here by construction.

Setup:
  export SIGNOZ_API_KEY='<your key>'
  python sentinel_signoz_proxy.py

Claude Desktop config entry (replaces the old mcp-remote-based "signoz" block):
  "signoz": {
    "command": "wsl.exe",
    "args": [
      "bash", "-c",
      "cd ~/sentinel-demo-app && source venv/bin/activate && export SIGNOZ_API_KEY='...' && python sentinel_signoz_proxy.py"
    ]
  }

⚠️ NOT YET LIVE-TESTED against Claude Desktop — built to eliminate a confirmed
bug in the previous approach, but this exact file has not been run end-to-end
yet. First run may need a small fix. Report back immediately if it errors.
"""

import os
import sys
import asyncio

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp import types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SIGNOZ_MCP_URL = "http://localhost:8000/mcp"
SIGNOZ_API_KEY = os.environ.get("SIGNOZ_API_KEY")

if not SIGNOZ_API_KEY:
    print("ERROR: SIGNOZ_API_KEY env var not set.", file=sys.stderr)
    sys.exit(1)

# Our local stdio-facing server — this is what Claude Desktop actually talks to
proxy = Server("signoz-proxy")

# Holds the live upstream session to SigNoz, set once at startup
upstream_session: ClientSession | None = None


@proxy.list_tools()
async def list_tools() -> list[types.Tool]:
    """Ask SigNoz what tools it has, and hand that list straight through."""
    result = await upstream_session.list_tools()
    return result.tools


@proxy.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Forward a tool call straight to SigNoz and return whatever it says."""
    result = await upstream_session.call_tool(name, arguments)
    return result.content


async def main():
    headers = {"SIGNOZ-API-KEY": SIGNOZ_API_KEY}

    print(f"Connecting to SigNoz MCP at {SIGNOZ_MCP_URL} ...", file=sys.stderr)

    async with streamablehttp_client(SIGNOZ_MCP_URL, headers=headers) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()

            global upstream_session
            upstream_session = session

            print("Connected to SigNoz. Tools:", file=sys.stderr)
            tools = await session.list_tools()
            for t in tools.tools:
                print(f"  - {t.name}", file=sys.stderr)

            print("Starting local stdio server for Claude Desktop...", file=sys.stderr)

            async with stdio_server() as (read_stream, write_stream):
                await proxy.run(
                    read_stream,
                    write_stream,
                    proxy.create_initialization_options(),
                )


if __name__ == "__main__":
    asyncio.run(main())
