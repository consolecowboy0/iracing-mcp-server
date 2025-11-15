# iRacing MCP Server

An MCP (Model Context Protocol) server for collecting iRacing telemetry data via pyirsdk. This server follows the MCP standard and can be integrated with ElevenLabs using either SSE (Server-Sent Events) or HTTPS streaming.

## Features

- **Real-time Telemetry**: Collect live telemetry data including speed, RPM, gear, throttle, brake, steering, and fuel levels
- **Session Information**: Access track name, session type, weather conditions, and time remaining
- **Car Information**: Get car ID, class, and track status
- **Position & Standings**: Track position, class position, lap times, and laps completed
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

Start the MCP server:

```bash
iracing-mcp-server
```

Or run directly with Python:

```bash
python -m iracing_mcp_server.server
```

### Integration with ElevenLabs

The server follows the MCP standard and can be configured in your MCP client configuration. For ElevenLabs integration, add the server to your MCP settings:

```json
{
  "mcpServers": {
    "iracing": {
      "command": "iracing-mcp-server"
    }
  }
}
```

### Available Tools

The server provides the following tools:

1. **connect_iracing** - Connect to the iRacing simulator
2. **disconnect_iracing** - Disconnect from iRacing
3. **check_connection** - Check connection status
4. **get_telemetry** - Get current telemetry data (speed, RPM, etc.)
5. **get_session_info** - Get session information (track, weather, etc.)
6. **get_car_info** - Get car information
7. **get_position_info** - Get position and lap time data
8. **get_all_data** - Get all available data in one call

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
