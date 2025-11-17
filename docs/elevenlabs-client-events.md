# ElevenLabs client-to-server events

This document summarizes what you need to configure inside the ElevenLabs Agents
UI so that the `player_pass` events emitted by the MCP server are actually
consumed by the agent runtime.

## Event payload reference

The MCP server emits a logging notification with the logger name
`iracing.pass_events`. The JSON payload uses the shape expected by the ElevenLabs
[client-to-server events documentation](https://elevenlabs.io/docs/agents-platform/customization/events/client-to-server-events):

```json
{
  "type": "player_pass",
  "timestamp": "2025-01-09T21:14:36.284911+00:00",
  "message": "Player advanced from P6 to P5",
  "previous_position": 6,
  "current_position": 5,
  "class_position": 3,
  "lap_completed": 42,
  "passed_car": {
    "car_idx": 18,
    "car_number": "22",
    "name": "D. Rival",
    "gap_meters": 1.24
  }
}
```

Everything under `passed_car` is optional because the SDK occasionally returns
empty surroundings data.

## How to wire up the ElevenLabs agent

1. **Open the agent in the Builder.** Go to *Customization → Events →
   Client-to-Server Events*.
2. **Add a new event entry.** Use `player_pass` as the event name. Add a short
   description such as “Notifies the agent when Dustin gains a position on track”.
3. **Author the event response.** ElevenLabs lets you define either a block of
   system instructions or a canned response. A simple template that keeps the
   agent in sync is:

   ```text
   When a `player_pass` event arrives, immediately summarize the pass aloud.
   Mention the old/new positions, lap number, and who got passed if that
   information exists. Keep it to one enthusiastic sentence.
   ```

4. **Save and deploy.** ElevenLabs only fires the event handler after the agent
   is republished.
5. **Verify with live telemetry.** Connect ElevenLabs to the MCP server, start a
   race, and watch the event stream in the Builder’s debug console. You should
   see the raw JSON payload show up at the same moment the agent narrates the
   pass.

## Troubleshooting checklist

- **No events arriving?** Make sure the ElevenLabs session has already issued a
  tool call or a `list_tools` request—otherwise the server never registers the
  session for streaming events.
- **Agent ignores the event?** Double-check that the event name exactly matches
  `player_pass`. The Builder is case-sensitive.
- **Payload missing context?** The underlying iRacing SDK occasionally returns
  empty `cars_behind` data; the event is still valid, but you should write the
  agent response to handle the absence of `passed_car`.
