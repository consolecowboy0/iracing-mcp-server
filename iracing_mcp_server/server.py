"""MCP Server for iRacing data collection.

This server provides tools to collect telemetry and session data from iRacing
via pyirsdk and exposes them through the Model Context Protocol (MCP). It can
now run over stdio (CLI), SSE, or Streamable HTTP transports.
"""

import argparse
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Sequence

import uvicorn
from mcp.server import Server as MCPServer
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from .iracing_data import IRacingDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data collector instance
data_collector = IRacingDataCollector()


def ensure_connection() -> bool:
    """Connect to iRacing if not already connected."""
    if data_collector.is_connected():
        return True
    return data_collector.connect()


def create_mcp_server() -> MCPServer:
    """Build and configure the MCP server instance."""
    server = MCPServer("iracing-mcp-server")

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
                name="get_surroundings",
                description="Show nearby cars ahead and behind the player along with relative gaps.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Number of cars to show ahead/behind (default 3).",
                        }
                    },
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
                if not ensure_connection():
                    return [
                        TextContent(
                            type="text",
                            text="Unable to connect to iRacing. Please make sure the sim is running and you are in a session.",
                        )
                    ]
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
                if not ensure_connection():
                    return [
                        TextContent(
                            type="text",
                            text="Unable to connect to iRacing. Please make sure the sim is running and you are in a session.",
                        )
                    ]
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
                if not ensure_connection():
                    return [
                        TextContent(
                            type="text",
                            text="Unable to connect to iRacing. Please make sure the sim is running and you are in a session.",
                        )
                    ]
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
                if not ensure_connection():
                    return [
                        TextContent(
                            type="text",
                            text="Unable to connect to iRacing. Please make sure the sim is running and you are in a session.",
                        )
                    ]
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

            elif name == "get_surroundings":
                if not ensure_connection():
                    return [
                        TextContent(
                            type="text",
                            text="Unable to connect to iRacing. Please make sure the sim is running and you are in a session.",
                        )
                    ]
                count_value = None
                if arguments and isinstance(arguments, dict):
                    raw_count = arguments.get("count")
                    if raw_count is not None:
                        try:
                            count_value = int(raw_count)
                        except (TypeError, ValueError):
                            pass
                surroundings = data_collector.get_surroundings(count=count_value or 3)
                if surroundings is None:
                    return [
                        TextContent(
                            type="text",
                            text="Failed to get surroundings info. Make sure you are connected to iRacing.",
                        )
                    ]

                def format_car(car: dict[str, Any]) -> str:
                    name = car.get("name", "Unknown")
                    number = car.get("car_number")
                    pos = car.get("position")
                    gap_pct = car.get("relative_lap_dist_pct")
                    gap = f"{gap_pct:+.3f}%" if gap_pct is not None else "n/a"
                    gap_m = car.get("gap_meters")
                    if gap_m is not None:
                        gap += f" ({gap_m:+.1f} m)"
                    return f"- {name} (#{number or 'n/a'}, pos {pos or 'n/a'}) gap {gap}"

                lines = [
                    f"Player: {surroundings['player'].get('name', 'Unknown')} "
                    f"(#{surroundings['player'].get('car_number', 'n/a')}, pos {surroundings['player'].get('position', 'n/a')})",
                    "Cars ahead:",
                ]
                ahead = surroundings.get("cars_ahead") or []
                if ahead:
                    lines.extend(format_car(car) for car in ahead)
                else:
                    lines.append("- None within range")

                lines.append("Cars behind:")
                behind = surroundings.get("cars_behind") or []
                if behind:
                    lines.extend(format_car(car) for car in behind)
                else:
                    lines.append("- None within range")

                return [
                    TextContent(
                        type="text",
                        text="\n".join(lines),
                    )
                ]

            elif name == "get_all_data":
                if not ensure_connection():
                    return [
                        TextContent(
                            type="text",
                            text="Unable to connect to iRacing. Please make sure the sim is running and you are in a session.",
                        )
                    ]
                
                all_data = {
                    "telemetry": data_collector.get_telemetry(),
                    "session": data_collector.get_session_info(),
                    "car": data_collector.get_car_info(),
                    "position": data_collector.get_position_info(),
                    "surroundings": data_collector.get_surroundings(),
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

    return server


async def run_stdio_server(server: MCPServer) -> None:
    """Run the MCP server over stdio (default CLI transport)."""
    async with stdio_server() as (read_stream, write_stream):
        logger.info("iRacing MCP Server started (stdio transport)")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def _ensure_leading_slash(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def _ensure_trailing_slash(path: str) -> str:
    path = _ensure_leading_slash(path)
    return path if path.endswith("/") else f"{path}/"


async def run_sse_server(
    server: MCPServer,
    host: str,
    port: int,
    sse_path: str,
    messages_path: str,
) -> None:
    """Expose the MCP server via SSE + POST endpoints."""
    sse_path = _ensure_leading_slash(sse_path)
    messages_path = _ensure_trailing_slash(messages_path)

    transport = SseServerTransport(messages_path)

    async def handle_sse(request: Request) -> Response:
        logger.info("SSE client connected from %s", request.client)
        async with transport.connect_sse(request.scope, request.receive, request._send) as streams:  # type: ignore[attr-defined]  # Starlette exposes _send
            read_stream, write_stream = streams
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
        return Response()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "transport": "sse",
                "sse_path": sse_path,
                "messages_path": messages_path,
            }
        )

    routes = [
        Route("/health", health, methods=["GET"]),
        Route(sse_path, handle_sse, methods=["GET"]),
        Mount(messages_path, app=transport.handle_post_message),
    ]

    starlette_app = Starlette(routes=routes)
    config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
    http_server = uvicorn.Server(config)
    logger.info("Starting SSE transport at http://%s:%s%s", host, port, sse_path)
    await http_server.serve()


async def run_streamable_http_server(
    server: MCPServer,
    host: str,
    port: int,
    http_path: str,
    json_response: bool,
    stateless: bool,
) -> None:
    """Expose the MCP server via Streamable HTTP (GET/POST/DELETE)."""
    http_path = _ensure_leading_slash(http_path)
    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=json_response,
        stateless=stateless,
    )

    async def mcp_app(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "transport": "streamable-http",
                "path": http_path,
                "json_response": json_response,
                "stateless": stateless,
            }
        )

    @asynccontextmanager
    async def lifespan(app):
        async with session_manager.run():
            yield

    routes = [
        Route("/health", health, methods=["GET"]),
        Mount(http_path, app=mcp_app),
    ]

    starlette_app = Starlette(routes=routes, lifespan=lifespan)
    config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
    http_server = uvicorn.Server(config)
    logger.info("Starting Streamable HTTP transport at http://%s:%s%s", host, port, http_path)
    await http_server.serve()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for transport selection."""
    parser = argparse.ArgumentParser(description="Run the iRacing MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "http"),
        default="stdio",
        help="Transport to expose (stdio for CLI, sse for Server-Sent Events, http for Streamable HTTP).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host/interface for network transports.")
    parser.add_argument("--port", type=int, default=8000, help="Port for network transports.")
    parser.add_argument("--sse-path", default="/sse", help="GET endpoint for SSE transport.")
    parser.add_argument(
        "--messages-path",
        default="/messages",
        help="POST endpoint for SSE transport where clients send MCP messages.",
    )
    parser.add_argument("--http-path", default="/mcp", help="Endpoint root for Streamable HTTP transport.")
    parser.add_argument(
        "--http-json-response",
        action="store_true",
        help="Return JSON responses instead of SSE streams for Streamable HTTP transport.",
    )
    parser.add_argument(
        "--http-stateless",
        action="store_true",
        help="Disable session tracking for Streamable HTTP transport (one-off requests).",
    )
    return parser.parse_args()


def main():
    """Main entry point for the server."""
    args = parse_args()
    server = create_mcp_server()

    try:
        if args.transport == "stdio":
            asyncio.run(run_stdio_server(server))
        elif args.transport == "sse":
            asyncio.run(
                run_sse_server(
                    server=server,
                    host=args.host,
                    port=args.port,
                    sse_path=args.sse_path,
                    messages_path=args.messages_path,
                )
            )
        else:
            asyncio.run(
                run_streamable_http_server(
                    server=server,
                    host=args.host,
                    port=args.port,
                    http_path=args.http_path,
                    json_response=args.http_json_response,
                    stateless=args.http_stateless,
                )
            )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        data_collector.disconnect()


if __name__ == "__main__":
    main()
