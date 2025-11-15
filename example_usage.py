#!/usr/bin/env python
"""
Example script showing how to interact with the iRacing MCP Server.

This script demonstrates the typical workflow:
1. Connect to iRacing
2. Fetch various types of data
3. Disconnect when done

Note: This requires iRacing to be running and you must be in a session.
"""

import asyncio
import sys
from iracing_mcp_server.iracing_data import IRacingDataCollector


async def main():
    """Main example function."""
    print("iRacing MCP Server - Example Usage")
    print("=" * 50)
    
    collector = IRacingDataCollector()
    
    # Try to connect to iRacing
    print("\n1. Connecting to iRacing...")
    if collector.connect():
        print("✓ Successfully connected to iRacing")
    else:
        print("✗ Failed to connect to iRacing")
        print("  Make sure iRacing is running and you are in a session.")
        return 1
    
    # Give some time for data to be available
    await asyncio.sleep(1)
    
    # Get telemetry data
    print("\n2. Getting Telemetry Data...")
    telemetry = collector.get_telemetry()
    if telemetry:
        print("✓ Telemetry data retrieved:")
        for key, value in telemetry.items():
            print(f"   {key}: {value}")
    else:
        print("✗ No telemetry data available")
    
    # Get session info
    print("\n3. Getting Session Info...")
    session_info = collector.get_session_info()
    if session_info:
        print("✓ Session info retrieved:")
        for key, value in session_info.items():
            print(f"   {key}: {value}")
    else:
        print("✗ No session info available")
    
    # Get car info
    print("\n4. Getting Car Info...")
    car_info = collector.get_car_info()
    if car_info:
        print("✓ Car info retrieved:")
        for key, value in car_info.items():
            print(f"   {key}: {value}")
    else:
        print("✗ No car info available")
    
    # Get position info
    print("\n5. Getting Position Info...")
    position_info = collector.get_position_info()
    if position_info:
        print("✓ Position info retrieved:")
        for key, value in position_info.items():
            print(f"   {key}: {value}")
    else:
        print("✗ No position info available")
    
    # Disconnect
    print("\n6. Disconnecting from iRacing...")
    collector.disconnect()
    print("✓ Disconnected")
    
    print("\n" + "=" * 50)
    print("Example complete!")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
