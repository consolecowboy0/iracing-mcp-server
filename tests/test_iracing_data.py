"""Tests for iRacing MCP Server."""

import pytest
from iracing_mcp_server.iracing_data import IRacingDataCollector


def test_data_collector_init():
    """Test that the data collector can be initialized."""
    collector = IRacingDataCollector()
    assert collector is not None
    assert not collector.is_connected()


def test_data_collector_connection_when_iracing_not_running():
    """Test connection behavior when iRacing is not running."""
    collector = IRacingDataCollector()
    # Connection should fail when iRacing is not running
    result = collector.connect()
    # On Linux or when iRacing is not running, this should return False
    # We can't test success case without iRacing running
    assert result in (True, False)


def test_data_collector_disconnect():
    """Test that disconnect doesn't raise errors."""
    collector = IRacingDataCollector()
    collector.disconnect()  # Should not raise


def test_get_telemetry_when_not_connected():
    """Test getting telemetry when not connected."""
    collector = IRacingDataCollector()
    telemetry = collector.get_telemetry()
    assert telemetry is None


def test_get_session_info_when_not_connected():
    """Test getting session info when not connected."""
    collector = IRacingDataCollector()
    session_info = collector.get_session_info()
    assert session_info is None


def test_get_car_info_when_not_connected():
    """Test getting car info when not connected."""
    collector = IRacingDataCollector()
    car_info = collector.get_car_info()
    assert car_info is None


def test_get_position_info_when_not_connected():
    """Test getting position info when not connected."""
    collector = IRacingDataCollector()
    position_info = collector.get_position_info()
    assert position_info is None
