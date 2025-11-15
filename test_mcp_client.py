"""
Quick sanity check for the iRacing MCP server.

Usage:
    python test_mcp_client.py

The script spawns the MCP server via stdio, calls connect_iracing,
then fetches telemetry (and session info if available) so you can
confirm data is flowing without involving ElevenLabs.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def call_tool(session: ClientSession, name: str, args: dict[str, Any] | None = None) -> None:
    print(f"\n=== Calling {name} ===")
    result = await session.call_tool(name=name, arguments=args)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


async def main() -> None:
    params = StdioServerParameters(command="python", args=["-m", "iracing_mcp_server.server"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await call_tool(session, "connect_iracing")
            await call_tool(session, "get_telemetry")
            await call_tool(session, "get_session_info")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
