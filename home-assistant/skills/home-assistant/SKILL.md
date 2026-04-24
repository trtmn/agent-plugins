---
name: home-assistant
description: Control and query Home Assistant smart home devices via the REST API. Use this skill whenever the user mentions Home Assistant, smart home control, IoT devices, home automation, turning lights on/off, checking sensor readings, thermostat control, door locks, or any task involving their home's connected devices — even if they don't explicitly say "Home Assistant." Also trigger when users ask about their home's state, want to create automations, or reference entity IDs like "light.living_room" or "switch.garage_door."
allowed-tools:
  - Bash(source ~/.config/home-assistant/.env)
  - Bash(curl:*)
  - Bash(bash:*)
---

# Home Assistant Control

This skill enables Claude to interact with a Home Assistant instance via its REST API — querying device states, controlling smart home devices, reviewing history, and working with automations.

## Slash Command

When invoked via `/home-assistant`, ensure authentication is set up (see below), then ask the user what they'd like to do — for example: check device status, control lights, adjust the thermostat, view history, or manage automations.

## Setup & Authentication

Configuration lives in `~/.config/home-assistant/.env`. On first use, check if this file exists:

```bash
cat ~/.config/home-assistant/.env 2>/dev/null || echo "NOT_FOUND"
```

**If the file exists**, source it to load `HA_URL` and `HA_TOKEN`:

```bash
source ~/.config/home-assistant/.env
```

**If the file doesn't exist**, walk the user through setup:

1. Explain what's needed: a Home Assistant URL and a Long-Lived Access Token
2. Ask for their HA URL (e.g., `http://192.168.1.100:8123` or `https://home.example.com`)
3. Guide them to create a token: Go to their HA instance → Profile (bottom-left) → Security tab → scroll to "Long-Lived Access Tokens" → click "Create Token" → give it a name like "Claude" → copy the token
4. Create the config:

```bash
mkdir -p ~/.config/home-assistant
cat > ~/.config/home-assistant/.env << 'EOF'
HA_URL="http://your-ha-address:8123"
HA_TOKEN="your_token_here"
EOF
chmod 600 ~/.config/home-assistant/.env
```

Replace the placeholder values with what the user provides. The `chmod 600` ensures only the user can read the token.

After sourcing, verify connectivity:

```bash
source ~/.config/home-assistant/.env
curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/"
```

Expected response: `{"message": "API running."}`. If it fails, check the URL and token with the user.

## Workflow

Follow this general approach for any Home Assistant task:

### 1. Discover what's available

Before trying to control or query specific devices, find out what entities exist. Run the discovery script to get a formatted overview:

```bash
bash <skill-path>/scripts/discover_entities.sh
```

This lists all entities grouped by domain (lights, switches, sensors, etc.) with their current states. Use this output to map the user's natural language ("the kitchen light") to actual entity IDs (`light.kitchen_ceiling`).

If the user asks about a specific type of device, you can filter:

```bash
bash <skill-path>/scripts/discover_entities.sh light
bash <skill-path>/scripts/discover_entities.sh sensor
bash <skill-path>/scripts/discover_entities.sh climate
```

### 2. Query state

To check the current state of a specific entity:

```bash
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  "$HA_URL/api/states/<entity_id>"
```

The response includes `state` (the primary value) and `attributes` (detailed properties like brightness, temperature, friendly name, etc.).

### 3. Take action (with confirmation)

**Before performing any action that changes device state, describe what you're about to do and ask the user to confirm.** This applies to all service calls — turning things on/off, locking/unlocking, adjusting temperatures, triggering scenes, etc. The reason: smart home actions affect the physical world and can't be undone with ctrl-z.

To call a service:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}' \
  "$HA_URL/api/services/<domain>/<service>"
```

Common examples:
- **Turn on a light**: `domain=light`, `service=turn_on`, data can include `brightness` (0-255), `color_temp`, `rgb_color`
- **Turn off a light**: `domain=light`, `service=turn_off`
- **Toggle a switch**: `domain=switch`, `service=toggle`
- **Set thermostat**: `domain=climate`, `service=set_temperature`, data includes `temperature`
- **Lock/unlock**: `domain=lock`, `service=lock` or `unlock`
- **Trigger a scene**: `domain=scene`, `service=turn_on`
- **Run a script**: `domain=script`, `service=turn_on` (or the script's entity name)

### 4. Review history

To see what happened with an entity over time:

```bash
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/history/period/<timestamp>?filter_entity_id=<entity_id>&end_time=<end_timestamp>&minimal_response"
```

Timestamps use ISO 8601 format (e.g., `2025-01-15T08:00:00+00:00`). The `minimal_response` flag reduces payload size.

For the logbook (human-readable event log):

```bash
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/logbook/<timestamp>?entity=<entity_id>"
```

## Working with automations

Home Assistant automations are entities in the `automation` domain. You can:

- **List automations**: Filter discovery output or query `/api/states` for entities starting with `automation.`
- **Trigger an automation**: Call `automation/trigger` service
- **Enable/disable**: Call `automation/turn_on` or `automation/turn_off`
- **View automation config**: The entity's attributes contain the automation's configuration

To create or modify automations, you'd need to edit the HA configuration files directly (typically `automations.yaml`), which is outside the scope of the REST API. If the user asks for this, let them know and offer to help draft the YAML instead.

## Rendering templates

Home Assistant supports Jinja2 templates for dynamic values. To evaluate a template:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template": "{{ states(\"sensor.temperature\") }}"}' \
  "$HA_URL/api/template"
```

This is useful when the user wants computed values or complex state queries.

## Error handling

- **401 Unauthorized**: Token is invalid or expired. Ask the user to regenerate it.
- **404 Not Found**: Entity doesn't exist. Run discovery to find the correct entity_id.
- **400 Bad Request**: Usually means malformed service data. Check the service's expected parameters by querying `/api/services`.

When a call fails, show the user the error response and suggest what to fix. Don't silently retry.

## Tips for natural language mapping

Users will say things like "turn off the bedroom light" rather than giving you entity IDs. To handle this:

1. Run discovery to get all entities
2. Look at `friendly_name` attributes to match natural language to entity IDs
3. If ambiguous (multiple "bedroom" lights), ask the user which one they mean
4. Cache the entity list mentally within the conversation — no need to re-discover every time

## Reference

For the complete REST API endpoint reference (all endpoints, parameters, and response formats), read `references/rest-api.md`.
