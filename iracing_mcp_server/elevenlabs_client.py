"""
Headless ElevenLabs client that bridges the iRacing MCP server over stdio.

The script launches the local MCP server, exposes its tools to ElevenLabs as
client-side tools, and relays tool invocations back to the server.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import AsyncExitStack
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import (
    AgentChatResponsePartType,
    AsyncAudioInterface,
    AsyncConversation,
    ClientTools,
    ConversationInitiationData,
)
from mcp import types as mcp_types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.session import RequestResponder

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

LOGGER = logging.getLogger("iracing-elevenlabs-client")


class SilentAudioInterface(AsyncAudioInterface):
    """No-op audio interface so we can stay in text-only mode."""

    async def start(self, input_callback: Callable[[bytes], Awaitable[None]]) -> None:  # noqa: ARG002
        return

    async def stop(self) -> None:
        return

    async def output(self, audio: bytes) -> None:  # noqa: ARG002
        return

    async def interrupt(self) -> None:
        return


def parse_env_pairs(pairs: Iterable[str]) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid env pair '{pair}', expected KEY=VALUE.")
        key, value = pair.split("=", 1)
        env[key.strip()] = value
    return env


def format_tool_result(tool: str, result: mcp_types.CallToolResult) -> str:
    """Simplify MCP tool content into a string ElevenLabs can announce."""
    if result.isError:
        return f"{tool} reported an error."

    text_chunks: List[str] = []
    for block in result.content:
        if isinstance(block, mcp_types.TextContent):
            text_chunks.append(block.text)
        else:
            text_chunks.append(json.dumps(block.model_dump(mode="json")))

    if result.structuredContent:
        text_chunks.append(json.dumps(result.structuredContent, indent=2))

    if not text_chunks:
        text_chunks.append(f"{tool} call completed but returned no content.")

    return "\n".join(text_chunks)


class MCPBridge:
    """Owns the stdio transport and dispatches tool calls."""

    def __init__(self, params: StdioServerParameters) -> None:
        self._params = params
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "MCPBridge":
        read_stream, write_stream = await self._stack.enter_async_context(stdio_client(self._params))
        self._session = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream, message_handler=self._handle_server_message)
        )
        init = await self._session.initialize()
        LOGGER.info("Connected to MCP server (%s %s)", init.serverInfo.name, init.serverInfo.version)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ARG002
        await self._stack.aclose()

    @property
    def session(self) -> ClientSession:
        if not self._session:
            raise RuntimeError("MCP session not ready.")
        return self._session

    async def list_tools(self) -> List[mcp_types.Tool]:
        cursor: Optional[str] = None
        tools: List[mcp_types.Tool] = []
        while True:
            result = await (
                self.session.list_tools(cursor)
                if cursor
                else self.session.list_tools()
            )
            tools.extend(result.tools)
            cursor = result.nextCursor
            if not cursor:
                break
        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any] | None) -> str:
        LOGGER.info("Calling MCP tool '%s' with %s", name, arguments or "{}")
        result = await self.session.call_tool(name=name, arguments=arguments)
        LOGGER.debug("Tool '%s' returned %s blocks", name, len(result.content))
        return format_tool_result(name, result)

    async def _handle_server_message(
        self,
        message: RequestResponder[mcp_types.ServerRequest, mcp_types.ClientResult]
        | mcp_types.ServerNotification
        | Exception,
    ) -> None:
        if isinstance(message, RequestResponder):
            LOGGER.debug("Server sent request %s", message.request.root.method)
            with message:
                await message.respond(mcp_types.ClientResult(root=mcp_types.EmptyResult()))
        elif isinstance(message, mcp_types.ServerNotification):
            LOGGER.debug("Server notification: %s", message.root.method)
        else:
            LOGGER.error("Server message error: %s", message)


def build_tool_overrides(tools: Iterable[mcp_types.Tool]) -> List[Dict[str, Any]]:
    overrides: List[Dict[str, Any]] = []
    for tool in tools:
        overrides.append(
            {
                "type": "client",
                "name": tool.name,
                "description": tool.description or f"MCP tool {tool.name}",
                "parameters": tool.inputSchema or {"type": "object"},
                "expects_response": True,
                "execution_mode": "immediate",
            }
        )
    return overrides


async def print_agent_text(text: str, part: AgentChatResponsePartType) -> None:
    prefix = "\nAgent > " if part == AgentChatResponsePartType.START else ""
    suffix = "\n" if part == AgentChatResponsePartType.STOP else ""
    sys.stdout.write(f"{prefix}{text}{suffix}")
    sys.stdout.flush()


async def interactive_user_loop(conversation: AsyncConversation, bridge: MCPBridge) -> None:
    print("Type messages to chat with the agent. Use /quit to exit.")
    print("Prefix with 'run <tool> [json_args]' to call MCP tools directly.\n")
    loop = asyncio.get_running_loop()
    while True:
        user_input = await loop.run_in_executor(None, lambda: input("You   > ").strip())
        if not user_input:
            continue
        lowered = user_input.lower()
        if lowered in ("/quit", "/exit", "quit", "exit"):
            break
        if lowered in ("/help", "help"):
            print("Commands: /quit to exit, 'run <tool> [json_args]' to call MCP tools, otherwise chat.")
            continue
        if lowered.startswith("run ") or lowered.startswith("/run "):
            parts = user_input.split(maxsplit=2)
            if len(parts) < 2:
                print("Usage: run <tool_name> [json_arguments]")
                continue
            tool_name = parts[1]
            arguments: Dict[str, Any] | None = None
            if len(parts) == 3:
                try:
                    arguments = json.loads(parts[2])
                except json.JSONDecodeError as exc:
                    print(f"Invalid JSON arguments: {exc}")
                    continue
            result = await bridge.call_tool(tool_name, arguments)
            print(f"\n{result}\n")
            continue
        await conversation.send_user_message(user_input)


async def run_bridge(args: argparse.Namespace) -> None:
    params = StdioServerParameters(
        command=args.command,
        args=args.server_args,
        env=args.server_env or None,
        cwd=args.server_cwd,
    )

    api_key = args.api_key or os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Provide --api-key or set ELEVENLABS_API_KEY.")

    async with MCPBridge(params) as bridge:
        tools = await bridge.list_tools()
        if not tools:
            raise RuntimeError("No tools available from MCP server.")

        loop = asyncio.get_running_loop()
        client_tools = ClientTools(loop=loop)

        for tool in tools:
            async def handler(
                params_dict: Dict[str, Any],
                *,
                _tool_name: str = tool.name,
            ) -> str:
                arguments = {k: v for k, v in params_dict.items() if k != "tool_call_id"}
                return await bridge.call_tool(_tool_name, arguments or None)

            client_tools.register(tool.name, handler, is_async=True)

        overrides = build_tool_overrides(tools)

        conversation_override: Dict[str, Any] = {"agent": {"prompt": {"tools": overrides}}}
        if args.text_only is not None:
            conversation_override["conversation"] = {"text_only": args.text_only}

        config = ConversationInitiationData(
            conversation_config_override=conversation_override,
            user_id=args.user_id,
        )

        eleven = ElevenLabs(api_key=api_key)
        conversation = AsyncConversation(
            client=eleven,
            agent_id=args.agent_id,
            user_id=args.user_id,
            requires_auth=args.requires_auth,
            audio_interface=SilentAudioInterface(),
            client_tools=client_tools,
            config=config,
            callback_agent_chat_response_part=print_agent_text,
        )

        await conversation.start_session()
        LOGGER.info("Conversation started. Conversation ID will be available once ElevenLabs responds.")

        try:
            await interactive_user_loop(conversation, bridge)
        finally:
            await conversation.end_session()
            await conversation.wait_for_session_end()
            LOGGER.info("Conversation closed.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bridge ElevenLabs to the iRacing MCP server.")
    parser.add_argument("--agent-id", help="ElevenLabs agent identifier (or set ELEVENLABS_AGENT_ID).")
    parser.add_argument("--api-key", help="ElevenLabs API key (falls back to ELEVENLABS_API_KEY).")
    parser.add_argument("--user-id", help="Optional user identifier ElevenLabs should log.")
    parser.add_argument(
        "--requires-auth",
        action="store_true",
        help="Set if the ElevenLabs agent requires signed URLs.",
    )
    parser.add_argument("--command", help="Command used to start the MCP server (defaults to current Python).")
    parser.add_argument(
        "--server-arg",
        dest="server_args",
        action="append",
        help="Additional argument for the MCP server command (repeatable).",
    )
    parser.add_argument(
        "--server-env",
        dest="server_env",
        action="append",
        default=[],
        help="Environment variables passed to the MCP server (KEY=VALUE, repeatable).",
    )
    parser.add_argument("--server-cwd", help="Working directory for the MCP server.")
    parser.set_defaults(text_only=None)
    parser.add_argument(
        "--text-only",
        dest="text_only",
        action="store_true",
        help="Force text-only conversation mode (requires agent support).",
    )
    parser.add_argument(
        "--audio",
        dest="text_only",
        action="store_false",
        help="Force audio streaming mode (requires agent support).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity.",
    )
    args = parser.parse_args(argv)
    args.server_args = args.server_args or []
    args.server_env = parse_env_pairs(args.server_env) if args.server_env else {}
    if args.command and " " in args.command and not args.server_args:
        LOGGER.warning("Command contains spaces; pass args via --server-arg to avoid quoting issues.")
    return args


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    if load_dotenv:
        load_dotenv()

    args = parse_args(argv)
    if args.command is None:
        args.command = sys.executable
        if not args.server_args:
            args.server_args = ["-m", "iracing_mcp_server.server"]

    args.agent_id = args.agent_id or os.getenv("ELEVENLABS_AGENT_ID")
    if not args.agent_id:
        raise RuntimeError("Provide --agent-id or set ELEVENLABS_AGENT_ID in your environment or .env file.")

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, loop.stop)
        except NotImplementedError:
            pass

    try:
        loop.run_until_complete(run_bridge(args))
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user.")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
