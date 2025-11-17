"""Tests for the telemetry event broadcaster."""

import asyncio

from iracing_mcp_server.server import IRacingEventBroadcaster


class DummyCollector:
    """Minimal stand-in for the iRacing data collector."""

    def __init__(self, positions: list[int], surroundings: dict | None = None) -> None:
        self.positions = positions
        self._index = 0
        self._surroundings = surroundings or {}
        self._connected = True

    def is_connected(self) -> bool:
        return self._connected

    def get_position_info(self):  # noqa: D401 - mimic collector signature
        if self._index >= len(self.positions):
            return {"position": self.positions[-1], "class_position": 2}
        value = self.positions[self._index]
        self._index += 1
        return {"position": value, "class_position": 2}

    def get_surroundings(self, count: int = 1):  # noqa: D401 - mimic collector signature
        return self._surroundings


class StubSession:
    """Records the notifications that would be sent to a real MCP session."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    async def send_log_message(self, level, data, logger=None, related_request_id=None):  # noqa: D401
        self.events.append({"level": level, "data": data, "logger": logger})


def test_pass_event_is_emitted_when_position_improves():
    async def _run_test() -> StubSession:
        collector = DummyCollector(
            positions=[6, 6, 5],
            surroundings={"cars_behind": [{"name": "Rival", "car_number": "22", "gap_meters": 1.2}]},
        )
        broadcaster = IRacingEventBroadcaster(collector, poll_interval=0.01)
        session = StubSession()
        broadcaster.register_session(session)

        await asyncio.sleep(0.05)

        await broadcaster.stop()
        return session

    session = asyncio.run(_run_test())

    assert session.events, "Expected at least one telemetry event"
    payload = session.events[0]["data"]
    assert payload["type"] == "player_pass"
    assert payload["previous_position"] == 6
    assert payload["current_position"] == 5
    assert payload["passed_car"]["name"] == "Rival"
