"""MCP Server for iRacing data collection.

This server provides tools to collect telemetry and session data from iRacing
via pyirsdk and exposes them through the Model Context Protocol (MCP).
Supports both SSE and HTTPS streaming for ElevenLabs integration.
"""

import asyncio
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .iracing_data import IRacingDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data collector instance
data_collector = IRacingDataCollector()


async def serve() -> None:
    """Run the MCP server."""
    server = Server("iracing-mcp-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools for iRacing data collection."""
        return [
            Tool(
                name="connect_iracing",
                description="Connect to iRacing simulator. Must be called before using other tools.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="disconnect_iracing",
                description="Disconnect from iRacing simulator.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="check_connection",
                description="Check if connected to iRacing simulator.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_telemetry",
                description="Get current telemetry data including speed, RPM, gear, throttle, brake, steering, lap info, and fuel levels.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_session_info",
                description="Get session information including track name, session type, time remaining, and weather conditions.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_car_info",
                description="Get car information including car ID, class, and track status.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_position_info",
                description="Get position and standings information including overall position, class position, and lap times.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_all_data",
                description="Get all available data from iRacing in a single call (telemetry, session, car, and position info).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
        """Handle tool calls for iRacing data collection."""
        try:
            if name == "connect_iracing":
                success = data_collector.connect()
                return [
                    TextContent(
                        type="text",
                        text=f"{'Successfully connected' if success else 'Failed to connect'} to iRacing. "
                        + ("" if success else "Make sure iRacing is running and you are in a session."),
                    )
                ]

            elif name == "disconnect_iracing":
                data_collector.disconnect()
                return [
                    TextContent(
                        type="text",
                        text="Disconnected from iRacing.",
                    )
                ]

            elif name == "check_connection":
                is_connected = data_collector.is_connected()
                return [
                    TextContent(
                        type="text",
                        text=f"Connection status: {'Connected' if is_connected else 'Not connected'}",
                    )
                ]

            elif name == "get_telemetry":
                telemetry = data_collector.get_telemetry()
                if telemetry is None:
                    return [
                        TextContent(
                            type="text",
                            text="Failed to get telemetry data. Make sure you are connected to iRacing.",
                        )
                    ]
                
                # Format telemetry data nicely
                formatted = "\n".join([f"{key}: {value}" for key, value in telemetry.items()])
                return [
                    TextContent(
                        type="text",
                        text=f"Telemetry Data:\n{formatted}",
                    )
                ]

            elif name == "get_session_info":
                session_info = data_collector.get_session_info()
                if session_info is None:
                    return [
                        TextContent(
                            type="text",
                            text="Failed to get session info. Make sure you are connected to iRacing.",
                        )
                    ]
                
                formatted = "\n".join([f"{key}: {value}" for key, value in session_info.items()])
                return [
                    TextContent(
                        type="text",
                        text=f"Session Info:\n{formatted}",
                    )
                ]

            elif name == "get_car_info":
                car_info = data_collector.get_car_info()
                if car_info is None:
                    return [
                        TextContent(
                            type="text",
                            text="Failed to get car info. Make sure you are connected to iRacing.",
                        )
                    ]
                
                formatted = "\n".join([f"{key}: {value}" for key, value in car_info.items()])
                return [
                    TextContent(
                        type="text",
                        text=f"Car Info:\n{formatted}",
                    )
                ]

            elif name == "get_position_info":
                position_info = data_collector.get_position_info()
                if position_info is None:
                    return [
                        TextContent(
                            type="text",
                            text="Failed to get position info. Make sure you are connected to iRacing.",
                        )
                    ]
                
                formatted = "\n".join([f"{key}: {value}" for key, value in position_info.items()])
                return [
                    TextContent(
                        type="text",
                        text=f"Position Info:\n{formatted}",
                    )
                ]

            elif name == "get_all_data":
                if not data_collector.is_connected():
                    return [
                        TextContent(
                            type="text",
                            text="Not connected to iRacing. Please connect first.",
                        )
                    ]
                
                all_data = {
                    "telemetry": data_collector.get_telemetry(),
                    "session": data_collector.get_session_info(),
                    "car": data_collector.get_car_info(),
                    "position": data_collector.get_position_info(),
                }
                
                sections = []
                for section_name, section_data in all_data.items():
                    if section_data:
                        formatted = "\n".join([f"  {key}: {value}" for key, value in section_data.items()])
                        sections.append(f"{section_name.upper()}:\n{formatted}")
                
                return [
                    TextContent(
                        type="text",
                        text="\n\n".join(sections) if sections else "No data available",
                    )
                ]

            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {name}",
                    )
                ]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}",
                )
            ]

    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("iRacing MCP Server started")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point for the server."""
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        # Ensure we disconnect on exit
        data_collector.disconnect()


if __name__ == "__main__":
    main()
