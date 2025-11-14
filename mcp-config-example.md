# Example MCP Client Configuration

This file shows how to configure the iRacing MCP Server with various MCP clients.

## ElevenLabs Configuration

Add this to your ElevenLabs MCP settings:

```json
{
  "mcpServers": {
    "iracing": {
      "command": "iracing-mcp-server",
      "args": [],
      "env": {}
    }
  }
}
```

## Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "iracing": {
      "command": "iracing-mcp-server"
    }
  }
}
```

## Using with Python Path

If the server is not in your PATH, specify the full path to Python:

```json
{
  "mcpServers": {
    "iracing": {
      "command": "python",
      "args": ["-m", "iracing_mcp_server.server"]
    }
  }
}
```

Or use the full path to the script:

```json
{
  "mcpServers": {
    "iracing": {
      "command": "python",
      "args": ["C:/path/to/iracing-mcp-server/iracing_mcp_server/server.py"]
    }
  }
}
```

## Using with Virtual Environment

```json
{
  "mcpServers": {
    "iracing": {
      "command": "C:/path/to/venv/Scripts/iracing-mcp-server.exe"
    }
  }
}
```

## Transport Options

The server uses stdio transport by default, which is compatible with both SSE and HTTPS streaming when used with MCP-compatible clients like ElevenLabs.

## Environment Variables

You can pass environment variables if needed:

```json
{
  "mcpServers": {
    "iracing": {
      "command": "iracing-mcp-server",
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```
