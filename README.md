# iRacing MCP Server

An MCP (Model Context Protocol) server for collecting iRacing telemetry data via pyirsdk. This server follows the MCP standard and can be integrated with ElevenLabs using either SSE (Server-Sent Events) or HTTPS streaming.

## Quick Start

Spin up the server in one terminal and tunnel it in another so the ElevenLabs remote client can reach the streamable HTTP endpoint.

1. **Start the MCP server (Command Prompt or PowerShell #1)**

   ```powershell
   cd C:\Users\dusti\OneDrive\Desktop\iracing-mcp-server
   # Optional if you haven't created a venv yet:
   # py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   python -m iracing_mcp_server.server --transport http --host 0.0.0.0 --port 8000 --http-path /mcp --http-json-response
   ```

   Leave this window open; it now serves `http://localhost:8000/mcp` plus `GET /health`.

2. **Expose it over HTTPS (Command Prompt or PowerShell #2)**

   ```powershell
   cd C:\Users\dusti\OneDrive\Desktop\iracing-mcp-server
   cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate
   ```

   Cloudflare prints a public `https://<random>.trycloudflare.com` URL. Test it with:

   ```powershell
   curl https://<random>.trycloudflare.com/health
   ```

3. **Configure ElevenLabs Web UI**

   - Transport: Streamable HTTP
   - Endpoint: `https://<random>.trycloudflare.com/mcp`
   - Health check: `https://<random>.trycloudflare.com/health`

   Once ElevenLabs confirms the health probe, it can call every MCP tool over HTTPS.

## Features

- **Real-time Telemetry**: Collect live telemetry data including speed, RPM, gear, throttle, brake, steering, and fuel levels
- **Session Information**: Access track name, session type, weather conditions, and time remaining
- **Car Information**: Get car ID, class, and track status
- **Position & Standings**: Track position, class position, lap times, and laps completed
- **Situational Awareness**: List nearby cars ahead/behind with relative gaps and speeds
- **Live Pass Events**: Automatically emits MCP logging notifications when the player gains a position so ElevenLabs can react in real time
- **MCP Standard Compliant**: Compatible with ElevenLabs and other MCP clients
- **SSE/HTTPS Support**: Works with both Server-Sent Events and HTTPS streaming

## Requirements

- Python 3.10 or higher
- iRacing simulator (must be running to collect data)
- Windows OS (required by iRacing and pyirsdk)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/consolecowboy0/iracing-mcp-server.git
cd iracing-mcp-server

# Install dependencies
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt
```

### Using pip (when published)

```bash
pip install iracing-mcp-server
```

## Usage

### Running the Server

#### Default (stdio) transport

Runs over stdio which is ideal when the MCP client spawns the process locally:

```bash
iracing-mcp-server
# or
python -m iracing_mcp_server.server
```

#### Server-Sent Events transport

Expose the server over HTTP so tools like the ElevenLabs web UI can connect via SSE:

```bash
# GET /sse streams responses, POST /messages/ receives client JSON-RPC payloads
iracing-mcp-server --transport sse --host 0.0.0.0 --port 8000 --sse-path /sse --messages-path /messages
```

A simple health probe is available at `GET /health`.

#### Streamable HTTP transport

Alternatively, use the Streamable HTTP transport (GET/POST/DELETE on a single endpoint):

```bash
iracing-mcp-server --transport http --host 0.0.0.0 --port 8000 --http-path /mcp
```

Flags:

- `--http-json-response` – respond with JSON payloads instead of SSE events.
- `--http-stateless` – create a fresh MCP session per request if your client cannot hold sessions.

The server exposes `GET /health` plus whatever path you configure via `--http-path`.

### Integration with ElevenLabs

You have two options depending on your environment:

1. **Local MCP config (stdio)** - Point ElevenLabs to the local command, as before:

    ```json
    {
      "mcpServers": {
        "iracing": {
          "command": "iracing-mcp-server"
        }
      }
    }
    ```

2. **Web UI over HTTP/SSE** - Run one of the network transports and enter the URL in the ElevenLabs interface:

   - **SSE**:  
     - SSE stream: `http://<host>:<port><sse_path>` (default `/sse`)  
     - Message POST endpoint: `http://<host>:<port><messages_path>` (default `/messages/`)
   - **Streamable HTTP**: `http://<host>:<port><http_path>` (default `/mcp`)

   Use `GET /health` to verify connectivity before pointing ElevenLabs at the server.

### Live race events

Once a client has listed tools or called any MCP tool, the server registers the
session with an internal event broadcaster. When the player's race position
improves, the broadcaster emits a `notifications/message` event with the logger
name `iracing.pass_events` that contains structured JSON describing the pass
(`type=player_pass`, previous/current position, and the car that was passed).
ElevenLabs treats these notifications as [client-to-server events](https://elevenlabs.io/docs/agents-platform/customization/events/client-to-server-events),
so the agent can immediately narrate real-world race moments without waiting for
another tool call.

Need help wiring that payload into your ElevenLabs agent? See
[docs/elevenlabs-client-events.md](docs/elevenlabs-client-events.md) for the exact
JSON shape plus a step-by-step walkthrough of the Builder settings you must
toggle on the ElevenLabs side.

### Headless ElevenLabs Client (SDK)

If the ElevenLabs UI cannot launch local stdio commands, use the bundled SDK client:

```bash
# .env should define ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID
python -m iracing_mcp_server.elevenlabs_client
```

Highlights:

- Automatically loads `.env` (via `python-dotenv`) and falls back to `ELEVENLABS_API_KEY` / `ELEVENLABS_AGENT_ID` environment variables, so you rarely need CLI flags
- Launches the MCP server over stdio (customize with `--command`, `--server-arg`, `--server-env`, `--server-cwd`)
- Registers every MCP tool as an ElevenLabs client tool on the fly so the agent can call them
- Runs a lightweight REPL (type `/quit` to exit). Add `--text-only` or `--audio` only if your agent explicitly allows overriding conversation mode
- Works with private agents that require signed URLs via `--requires-auth`

You can still override any value explicitly, e.g. `--agent-id`, `--api-key`, or transport flags. The same entry point is available as `iracing-elevenlabs-client` when installed via `pip`.

### Available Tools

The server provides the following tools:

1. **connect_iracing** - Connect to the iRacing simulator
2. **disconnect_iracing** - Disconnect from iRacing
3. **check_connection** - Check connection status
4. **get_telemetry** - Get current telemetry data (speed, RPM, etc.)
5. **get_session_info** - Get session information (track, weather, etc.)
6. **get_car_info** - Get car information
7. **get_position_info** - Get position and lap time data
8. **get_surroundings** - Show nearby cars ahead/behind with relative gaps
9. **get_all_data** - Get all available data in one call

### Example Usage

1. Start iRacing and enter a session (practice, qualifying, or race)
2. Run the MCP server
3. Connect to iRacing using the `connect_iracing` tool
4. Use any of the data collection tools to retrieve information
5. Disconnect when done using `disconnect_iracing`

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/consolecowboy0/iracing-mcp-server.git
cd iracing-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## Architecture

The server consists of two main components:

1. **IRacingDataCollector** (`iracing_data.py`): Handles connection and data collection from iRacing using pyirsdk
2. **MCP Server** (`server.py`): Implements the Model Context Protocol and exposes tools for data access

### Data Flow

```
iRacing Simulator → pyirsdk → IRacingDataCollector → MCP Server → Client (ElevenLabs/etc)
```

## Telemetry Data Available

- Speed (m/s)
- RPM (revolutions per minute)
- Gear (current gear)
- Throttle position (0-1)
- Brake position (0-1)
- Steering wheel angle
- Lap number
- Lap distance percentage
- Fuel level and percentage
- Engine warnings

## Session Information Available

- Track name and configuration
- Session type (practice, qualifying, race)
- Session time and time remaining
- Air temperature
- Track temperature
- Sky conditions

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/consolecowboy0/iracing-mcp-server/issues) page.

## Acknowledgments

- Built with [pyirsdk](https://github.com/kutu/pyirsdk) for iRacing data access
- Uses the [Model Context Protocol](https://modelcontextprotocol.io/) for standardized tool integration
- Designed for integration with ElevenLabs and other MCP-compatible clients
