#!/usr/bin/env python
"""
Example script showing how to interact with the iRacing MCP Server.

Workflow:
1. Connect to iRacing
2. Fetch telemetry, session, car, position, and surroundings data
3. Disconnect

Note: Run this while iRacing is active and you are in a session.
"""

import asyncio
import sys

from iracing_mcp_server.iracing_data import IRacingDataCollector


async def main() -> int:
    """Entry point for the example."""
    print("iRacing MCP Server - Example Usage")
    print("=" * 50)

    collector = IRacingDataCollector()

    print("\n1. Connecting to iRacing...")
    if collector.connect():
        print("Connected!")
    else:
        print("Failed to connect. Make sure iRacing is running and you are in a session.")
        return 1

    await asyncio.sleep(1)

    print("\n2. Getting Telemetry Data...")
    telemetry = collector.get_telemetry()
    if telemetry:
        for key, value in telemetry.items():
            print(f"  {key}: {value}")
    else:
        print("  No telemetry data available.")

    print("\n3. Getting Session Info...")
    session_info = collector.get_session_info()
    if session_info:
        for key, value in session_info.items():
            print(f"  {key}: {value}")
    else:
        print("  No session info available.")

    print("\n4. Getting Car Info...")
    car_info = collector.get_car_info()
    if car_info:
        for key, value in car_info.items():
            print(f"  {key}: {value}")
    else:
        print("  No car info available.")

    print("\n5. Getting Position Info...")
    position_info = collector.get_position_info()
    if position_info:
        for key, value in position_info.items():
            print(f"  {key}: {value}")
    else:
        print("  No position info available.")

    print("\n6. Getting Surroundings Info...")
    surroundings = collector.get_surroundings()
    if surroundings:
        player = surroundings.get("player", {})
        print(
            f"  You: {player.get('name', 'Unknown')} "
            f"(#{player.get('car_number', 'n/a')}, pos {player.get('position', 'n/a')})"
        )
        for label, title in (("cars_ahead", "Ahead"), ("cars_behind", "Behind")):
            print(f"  {title}:")
            cars = surroundings.get(label) or []
            if not cars:
                print("    None within range.")
                continue
            for car in cars:
                gap_pct = car.get("relative_lap_dist_pct")
                gap_str = f"{gap_pct:+.3f}%" if gap_pct is not None else "n/a"
                gap_m = car.get("gap_meters")
                if gap_m is not None:
                    gap_str += f" ({gap_m:+.1f} m)"
                print(
                    f"    - {car.get('name', 'Car')} "
                    f"(#{car.get('car_number', 'n/a')}, pos {car.get('position', 'n/a')}) gap {gap_str}"
                )
    else:
        print("  No surroundings info available.")

    print("\n7. Disconnecting from iRacing...")
    collector.disconnect()
    print("Disconnected.")

    print("\n" + "=" * 50)
    print("Example complete!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}")
        sys.exit(1)
