"""Tests for MCP server functionality."""

import pytest


def test_server_import():
    """Test that the server module can be imported."""
    from iracing_mcp_server import server
    assert server is not None


def test_main_function_exists():
    """Test that the main function exists."""
    from iracing_mcp_server.server import main
    assert callable(main)


def test_serve_function_exists():
    """Test that the serve function exists."""
    from iracing_mcp_server.server import serve
    assert callable(serve)
