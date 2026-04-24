# Home Assistant REST API Reference

All requests require:
- Header: `Authorization: Bearer $HA_TOKEN`
- Header: `Content-Type: application/json` (for POST requests)
- Base URL: `$HA_URL`

## Table of Contents

- [Health & Config](#health--config)
- [Entity States](#entity-states)
- [Services](#services)
- [Events](#events)
- [History & Logbook](#history--logbook)
- [Calendars](#calendars)
- [Templates](#templates)
- [Config Validation](#config-validation)
- [Camera](#camera)
- [Intents](#intents)

---

## Health & Config

### GET /api/
Verify the API is running.
**Response:** `{"message": "API running."}`

### GET /api/config
Returns current configuration: components, location, timezone, unit system, version.

### GET /api/components
Returns array of loaded component strings (e.g., `["light", "switch", "automation"]`).

### GET /api/error_log
Returns plaintext error log for the current session.

---

## Entity States

### GET /api/states
Returns array of all entity state objects.

**State object structure:**
```json
{
  "entity_id": "light.kitchen",
  "state": "on",
  "attributes": {
    "friendly_name": "Kitchen Light",
    "brightness": 200,
    "color_temp": 370,
    "supported_features": 44
  },
  "last_changed": "2025-01-15T10:30:00+00:00",
  "last_updated": "2025-01-15T10:30:00+00:00"
}
```

### GET /api/states/{entity_id}
Returns state object for a specific entity. Returns 404 if entity doesn't exist.

### POST /api/states/{entity_id}
Create or update an entity's state directly. Returns 200 for updates, 201 for creation.

**Request body:**
```json
{
  "state": "25.5",
  "attributes": {
    "unit_of_measurement": "°C",
    "friendly_name": "Custom Sensor"
  }
}
```

### DELETE /api/states/{entity_id}
Remove an entity state. Useful for cleaning up stale entities.

---

## Services

### GET /api/services
Returns all available services grouped by domain.

**Response structure:**
```json
[
  {
    "domain": "light",
    "services": {
      "turn_on": {
        "description": "Turn on a light",
        "fields": {
          "brightness": {"description": "Brightness (0-255)"},
          "color_temp": {"description": "Color temperature in mireds"},
          "rgb_color": {"description": "RGB color [r, g, b]"}
        }
      },
      "turn_off": {},
      "toggle": {}
    }
  }
]
```

### POST /api/services/{domain}/{service}
Call a service action. Returns array of affected entity states.

**Request body examples:**

Turn on a light with brightness:
```json
{
  "entity_id": "light.living_room",
  "brightness": 200
}
```

Set thermostat temperature:
```json
{
  "entity_id": "climate.hallway",
  "temperature": 22
}
```

Target multiple entities:
```json
{
  "entity_id": ["light.kitchen", "light.dining_room"]
}
```

Target by area (if areas are configured in HA):
```json
{
  "area_id": "living_room"
}
```

**Query parameter:** Add `?return_response` to get service response data (for services that return data).

---

## Events

### GET /api/events
Returns array of event types with listener counts.
```json
[
  {"event": "state_changed", "listener_count": 15},
  {"event": "call_service", "listener_count": 3}
]
```

### POST /api/events/{event_type}
Fire a custom event. Request body becomes the event data.

```json
{
  "custom_key": "custom_value"
}
```

---

## History & Logbook

### GET /api/history/period/{timestamp}
Retrieve historical state changes starting from the given timestamp.

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `filter_entity_id` | Recommended | Comma-separated entity IDs to filter |
| `end_time` | No | End timestamp (ISO 8601) |
| `minimal_response` | No | Reduces response size (no attributes) |
| `no_attributes` | No | Excludes all attributes |
| `significant_changes_only` | No | Only includes significant state changes |

**Timestamp format:** ISO 8601, e.g., `2025-01-15T08:00:00+00:00`

**Example:**
```
/api/history/period/2025-01-15T00:00:00+00:00?filter_entity_id=sensor.temperature&end_time=2025-01-15T23:59:59+00:00&minimal_response
```

### GET /api/logbook/{timestamp}
Returns human-readable logbook entries.

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `entity` | No | Filter to specific entity_id |
| `end_time` | No | End timestamp (ISO 8601) |

---

## Calendars

### GET /api/calendars
List all calendar entities with IDs and names.

### GET /api/calendars/{entity_id}
Get calendar events.

**Required parameters:**
| Parameter | Description |
|-----------|-------------|
| `start` | Start timestamp (ISO 8601) |
| `end` | End timestamp (ISO 8601) |

---

## Templates

### POST /api/template
Render a Jinja2 template against Home Assistant state.

**Request body:**
```json
{
  "template": "The kitchen light is {{ states('light.kitchen') }} and the temperature is {{ states('sensor.temperature') }}°C"
}
```

Returns the rendered string as plain text.

Useful for complex queries that combine multiple entity states or do calculations.

---

## Config Validation

### POST /api/config/core/check_config
Validates the current `configuration.yaml`. No request body needed.

Returns result with errors if any are found.

---

## Camera

### GET /api/camera_proxy/{entity_id}
Fetch the latest camera image.

**Parameter:** `time` — timestamp to bypass caching (use current Unix timestamp).

Returns the image binary data.

---

## Intents

### POST /api/intent/handle
Process a Home Assistant intent (similar to voice commands).

**Request body:**
```json
{
  "name": "HassLightSet",
  "data": {
    "name": "kitchen",
    "brightness_pct": 80
  }
}
```

---

## Common Domains and Services

Quick reference for frequently used service calls:

| Domain | Service | Common Data Fields |
|--------|---------|-------------------|
| `light` | `turn_on` | `brightness` (0-255), `color_temp`, `rgb_color`, `transition` |
| `light` | `turn_off` | `transition` |
| `switch` | `turn_on` / `turn_off` / `toggle` | — |
| `climate` | `set_temperature` | `temperature`, `hvac_mode` |
| `climate` | `set_hvac_mode` | `hvac_mode` (heat, cool, auto, off) |
| `lock` | `lock` / `unlock` | — |
| `cover` | `open_cover` / `close_cover` / `stop_cover` | `position` (0-100) |
| `media_player` | `play_media` | `media_content_id`, `media_content_type` |
| `media_player` | `volume_set` | `volume_level` (0.0-1.0) |
| `scene` | `turn_on` | — |
| `script` | `turn_on` | (script-specific variables) |
| `automation` | `trigger` | — |
| `automation` | `turn_on` / `turn_off` | — |
| `fan` | `turn_on` | `speed`, `percentage` |
| `vacuum` | `start` / `stop` / `return_to_base` | — |
| `notify` | `notify` | `message`, `title`, `target` |

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (state updated) |
| 201 | Created (new entity state) |
| 400 | Bad request — malformed data |
| 401 | Unauthorized — bad or expired token |
| 404 | Not found — entity doesn't exist |
| 405 | Method not allowed |
