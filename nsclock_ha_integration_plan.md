# NSClock Home Assistant Integration — Implementation Plan

## Purpose

Build a custom Home Assistant integration for the **Nightscout Clock (NSClock)** firmware running on a Ulanzi TC001 or compatible AWTRIX device.

The NSClock remains the authoritative device:

```text
Nightscout / Dexcom / LibreLinkUp / Medtrum
                 ↓
             NSClock firmware
                 ↓
        Clock local HTTP API
                 ↓
      Home Assistant integration
                 ↓
   HA entities, automations, dashboards
```

Home Assistant polls the clock’s local HTTP API. It does **not** connect directly to Nightscout, Dexcom, LibreLinkUp, or Medtrum in the normal operating mode.

## Source of truth

| Concern | Endpoint | Refresh strategy |
|---|---|---|
| Live device and glucose state | `GET /api/status` | Every 15–30 seconds |
| Firmware version | `GET /version.txt` | Startup and every 6–12 hours |
| Persisted configuration | `GET /config.json` | On demand / before settings changes |
| Timezone choices | `GET /tzdata.json` | On demand |
| Authentication state | `GET /api/auth/status` | During setup and after auth failure |
| Hardware telemetry | `GET /api/hardware` | Phase 5; every 60 seconds |
| Control actions | `POST /api/...` | User or automation triggered |

The official web UI polls `/api/status` every 15 seconds and uses exponential backoff up to 60 seconds after a failure.

## Architecture

```text
custom_components/nsclock/
  __init__.py
  api.py
  config_flow.py
  const.py
  coordinator.py
  entity.py
  manifest.json
  strings.json
  translations/en.json
  sensor.py
  binary_sensor.py
  switch.py
  button.py
  services.yaml
```

### Components

- `NightscoutClockApiClient`
  - Async `aiohttp` client.
  - Owns base URL, password, cookie jar, login, retry, and request methods.
  - Must never log passwords, cookies, API secrets, or Wi-Fi credentials.

- `NightscoutClockCoordinator`
  - `DataUpdateCoordinator`.
  - Polls `/api/status` on the configured interval.
  - Refreshes `/version.txt` infrequently.
  - Optionally polls `/api/hardware` in Phase 5.
  - Provides one shared data object to all entities.

- Entities
  - Read from coordinator data.
  - Do not make independent HTTP requests.
  - Use HA device registry and unique IDs.

- Config flow
  - Collect host and optional web password.
  - Validate connectivity using `/api/status`.
  - Ask for password only when `/api/auth/status` reports `enabled: true`.

## Authentication

The clock uses an HttpOnly `auth_token` cookie. Login sets a cookie valid for ten minutes.

Implementation rules:

1. Store the web password in HA config entry data, which is encrypted.
2. Attach the current cookie to authenticated requests.
3. On `401`, call `/api/auth/login`, update the cookie, and retry the original request once.
4. After repeated authentication failure, raise `ConfigEntryAuthFailed` and prompt the user to reauthenticate.
5. Never expose or log credentials.

`/api/status` and `/version.txt` are public. Configuration and control endpoints require authentication only when web authentication is enabled.

## V1 scope

### Goals

- Make the NSClock a first-class HA device.
- Expose its live glucose and connectivity state.
- Provide safe local controls.
- Avoid risky configuration writes.

### V1 entities

| Entity | Object ID | Platform | API source | Notes |
|---|---|---|---|---|
| Blood glucose | `blood_glucose` | Sensor | `/api/status` → `sgv` | Unit: `mg/dL`; `0` means no reading and must become `unknown` |
| Data source | `data_source` | Sensor | `/api/status` → `bgSource` | First-class entity; identifies active upstream source |
| Source status | `source_status` | Sensor | `/api/status` → `bgSourceStatus` | Firmware status code |
| Firmware version | `firmware_version` | Sensor | `/version.txt` | Infrequent refresh |
| Clock connected | `clock_connected` | Binary sensor | `/api/status` → `isConnected` | Device class: `connectivity` |
| Internet available | `internet_available` | Binary sensor | `/api/status` → `hasInternet` | Device class: `connectivity` |
| Access point mode | `access_point_mode` | Binary sensor | `/api/status` → `isInAPMode` | No standard device class |
| Display | `display` | Switch | `POST /api/displaypower` | `on` / `off` |
| Play alarm melody | `play_alarm_melody` | Button | `POST /api/alarm` | Uses configured RTTTL melody |
| Restart clock | `restart` | Button | `POST /api/reset` | Disabled by default |

### Data source values

Expose the firmware values directly:

```text
NO_SOURCE
NIGHTSCOUT
DEXCOM
API
LIBRELINKUP
MEDTRONIC
MEDTRUM
```

The `data_source` entity is essential because future services and automations may need to know whether the clock is using the API source.

### Attributes

Add contextual attributes without creating extra entities:

| Parent entity | Attribute | API field |
|---|---|---|
| `sensor.blood_glucose` | `data_source` | `bgSource` |
| `sensor.blood_glucose` | `source_status` | `bgSourceStatus` |
| `binary_sensor.clock_connected` | `internet_available` | `hasInternet` |
| `binary_sensor.clock_connected` | `access_point_mode` | `isInAPMode` |
| `sensor.firmware_version` | `host` | Config entry |
| `sensor.firmware_version` | `last_update_success` | Coordinator |

## Configuration flow

### Step 1 — Connection

Collect:

- `host`: IP address or hostname
- Optional `password`

Validate by calling:

1. `GET /api/status`
2. `GET /api/auth/status`

If authentication is enabled, require and verify the password.

### Step 2 — Options

Expose:

- Polling interval: default 30 seconds; allowed 10–300 seconds
- Default RTTTL melody for the play-melody button
- Enable restart button: default off
- Enable hardware telemetry: default on when supported; Phase 5

### Unique ID

Use a stable device identifier where available. If none is exposed, derive a unique ID from the configured host and clearly document that changing the device IP requires updating the integration.

## V1 API client methods

```python
async def async_get_status() -> dict
async def async_get_version() -> str
async def async_get_auth_status() -> dict
async def async_login(password: str) -> None
async def async_set_display_power(power: Literal["on", "off"]) -> None
async def async_play_alarm(rtttl: str) -> None
async def async_restart() -> None
async def async_get_config() -> dict
```

Do not implement configuration saving in v1.

## Error handling

| Condition | HA behavior |
|---|---|
| Network timeout | Coordinator update failure; entities become unavailable after repeated failures |
| HTTP 401 | Login and retry once; then `ConfigEntryAuthFailed` |
| `sgv == 0` | Blood-glucose entity state becomes `unknown` |
| Invalid RTTTL | Service/button error; do not save anything |
| Restart requested | Mark restart button as unavailable briefly; poll `/version.txt` for recovery |
| Clock unreachable | Coordinator retry with backoff |
| `/api/hardware` returns 404 | Disable hardware entities gracefully; do not fail the integration |

## Phase 2 — Read-only configuration diagnostics

Add read-only diagnostic entities sourced from `/config.json`.

These entities must not write to the clock.

| Entity | Config key | Platform | Notes |
|---|---|---|---|
| Brightness mode | Derived from `brightnesslevel` | Sensor | `100` = auto balanced, `101` = auto dark room, `1–99` = manual |
| Brightness level | `brightnesslevel` | Sensor | Raw firmware value |
| Glucose units | `units` | Sensor | `mgdl` or `mmol` |
| Time format | `timeformat` | Sensor | `24` or `12` |
| Clock name | `clockname` | Sensor | Useful diagnostics |
| Default face | `defaultface` | Sensor | Face ID |
| Active faces | Derived from `inactivefaces` | Sensor | Comma-separated or attribute list |
| Face cycling | `facecycleenabled` | Binary sensor | On/off |
| Face-cycle interval | `facecycleintervalseconds` | Sensor | Seconds |
| Alarm high enabled | `alarm_high_enabled` | Binary sensor | On/off |
| Alarm low enabled | `alarm_low_enabled` | Binary sensor | On/off |
| Alarm urgent-low enabled | `alarm_urgent_low_enabled` | Binary sensor | On/off |
| Alarm high threshold | `alarm_high_value` | Sensor | mg/dL |
| Alarm low threshold | `alarm_low_value` | Sensor | mg/dL |
| Alarm urgent-low threshold | `alarm_urgent_low_value` | Sensor | mg/dL |

Refresh `/config.json` no more often than every 5–15 minutes because these are persisted settings, not live telemetry.

## Phase 3 — Controlled settings writes

### Critical constraint

`POST /api/save` accepts the complete configuration object. The official UI then restarts the clock and waits for it to return.

Therefore, HA must use a staged draft-and-apply model:

```text
User changes HA config entity
        ↓
Integration updates pending local draft
        ↓
User calls: nsclock.apply_settings
        ↓
GET /config.json
        ↓
Apply only changed, supported keys
        ↓
POST /api/save with complete config
        ↓
POST /api/reset
        ↓
Poll /version.txt until device returns
        ↓
Reload /config.json
        ↓
Refresh entities
```

### Initial writable settings

Start with a small safe subset:

- Brightness mode
- Brightness level
- Time format
- Clock name
- Alarm enabled flags
- Alarm thresholds

### Later writable settings

Only after the save/apply workflow is proven:

- Default face
- Active/inactive faces
- Face cycling
- Face-cycle interval
- Alarm melodies
- Alarm snooze intervals
- Glucose color bands

### Never expose or write from HA

- Wi-Fi SSID or password
- Static IP, gateway, DNS, or MAC settings
- Nightscout API secret
- Dexcom credentials
- LibreLinkUp credentials
- Medtrum credentials
- Web authentication password
- Factory reset

The official UI treats network settings specially because applying another clock’s settings could move the device onto a different network. It also prevents web-auth settings from being imported from a settings file.

## Phase 4 — Optional API-source bridge

Only implement after v1 is stable.

Expose:

```yaml
service: nsclock.report_glucose
data:
  sgv: 118
  direction: Flat
  trend: 4
  timestamp: "2026-10-19T14:39:00+00:00"
```

Behavior:

- Convert timestamp to Unix milliseconds.
- Build one `GlucoseEntry`.
- POST a single-entry array to `/api/v1/entries`.
- Allow the call only when `sensor.data_source` is `API`, or return a clear error otherwise.
- Do not expose `DELETE /api/v1/entries` as a normal HA service.

The API source endpoint is only registered when the clock’s data source is `API`.

## Phase 5 — Hardware telemetry

The Ulanzi TC001 hardware includes sensors that could be useful in Home Assistant, but the current NSClock OpenAPI does not expose them. This phase adds firmware API support where needed, then exposes the telemetry through HA.

### Hardware capabilities

| Hardware | Measurement | HA value | Reliability |
|---|---|---|---|
| Battery + ADC | Battery voltage | Battery voltage, estimated percentage, charging/on-battery state | Voltage is real; percentage is an estimate |
| SHT3x temperature/humidity sensor | Temperature and relative humidity | Device temperature and device humidity | Biased by internal heat; diagnostic only |
| Ambient-light sensor | Light level | Raw light level or estimated illuminance | Useful for brightness context; not a calibrated room sensor |
| Buttons | Physical button presses | Event / button entities | Only if firmware exposes debounced events |
| Buzzer | Audio output | Already used for RTTTL alarms | No new sensor entity needed |

The TC001 is an ESP32-based 8×32 RGB pixel clock with a 4400 mAh battery, three buttons, a buzzer, an ambient-light sensor, and an SHT3x temperature/humidity sensor.

### Firmware API design

Add a single hardware-telemetry endpoint rather than scattering values across multiple routes:

```http
GET /api/hardware
```

Proposed response:

```json
{
  "battery": {
    "voltage": 4.08,
    "percent": 87,
    "charging": false,
    "onBattery": false
  },
  "environment": {
    "temperature": 31.4,
    "humidity": 42.1
  },
  "light": {
    "raw": 812,
    "lux": 145
  },
  "buttons": {
    "supported": true
  }
}
```

Alternatively, extend `/api/status` with a nested `hardware` object. A separate `/api/hardware` endpoint is preferable because hardware readings change at a different rate from glucose/connectivity state and may require different polling.

### Firmware implementation tasks

1. Confirm which sensors the current NSClock firmware already reads.
2. Add battery-voltage reading through the existing ADC path.
3. Calculate battery percentage only if a reliable voltage-to-charge mapping exists.
4. Detect charging or USB-powered versus battery-powered state if hardware/firmware supports it.
5. Add SHT3x temperature and humidity reads if the sensor driver is present or can be added.
6. Add ambient-light reading; expose raw ADC value first, and estimated lux only if calibration is practical.
7. Add debounce and event handling for the three physical buttons if button integration is desired.
8. Add the `/api/hardware` endpoint.
9. Update the OpenAPI specification with schemas for all new fields.
10. Keep hardware telemetry read-only; do not add controls that could affect charging or power behavior.

### Proposed API schemas

```yaml
HardwareTelemetry:
  type: object
  properties:
    battery:
      type: object
      properties:
        voltage:
          type: number
          description: Battery voltage in volts.
        percent:
          type: integer
          minimum: 0
          maximum: 100
          description: Estimated charge percentage; omit if unavailable.
        charging:
          type: boolean
        onBattery:
          type: boolean
    environment:
      type: object
      properties:
        temperature:
          type: number
          description: Device internal temperature in degrees Celsius.
        humidity:
          type: number
          description: Device internal relative humidity in percent.
    light:
      type: object
      properties:
        raw:
          type: integer
        lux:
          type: number
          description: Optional estimated illuminance; omit if uncalibrated.
    buttons:
      type: object
      properties:
        supported:
          type: boolean
```

### HA entities

Add these only after the firmware endpoint exists.

| Entity | Object ID | Platform | Unit / class | Notes |
|---|---|---|---|---|
| Battery voltage | `battery_voltage` | Sensor | V | Raw measured value |
| Battery level | `battery_level` | Sensor | % | Firmware-estimated |
| Charging | `charging` | Binary sensor | `battery_charging` | Only if detectable |
| On battery | `on_battery` | Binary sensor | `power` | Useful power-outage automation trigger |
| Device temperature | `device_temperature` | Sensor | °C, `temperature` | Diagnostic; internal heat bias expected |
| Device humidity | `device_humidity` | Sensor | %, `humidity` | Diagnostic; affected by device temperature |
| Light level | `light_level` | Sensor | Raw value or lx | Use `illuminance` only if calibrated |
| Left button | `button_left` | Button / event entity | — | Only if firmware exposes press events |
| Middle button | `button_middle` | Button / event entity | — | Only if firmware exposes press events |
| Right button | `button_right` | Button / event entity | — | Only if firmware exposes press events |

### Polling strategy

- Poll `/api/hardware` every 60 seconds by default.
- Poll battery-related values more frequently only if charging-state changes matter.
- Do not poll temperature/humidity faster than 60 seconds; internal thermal changes are slow.
- Make hardware telemetry optional in the integration options flow.
- If `/api/hardware` returns `404`, disable the hardware entities cleanly rather than treating the integration as broken.

### HA behavior rules

- Battery percentage should be `unknown` if firmware cannot provide a reliable estimate.
- Device temperature and humidity should be clearly labeled as device diagnostics.
- Ambient-light raw values should not be presented as lux unless the firmware calibrates them.
- Button events should be event entities or diagnostic buttons, not actions that alter clock configuration.
- Hardware entities must never be allowed to trigger configuration saves or restarts.

### Acceptance criteria

- [ ] `/api/hardware` returns stable JSON.
- [ ] OpenAPI documents every exposed field.
- [ ] Missing optional fields do not break HA entity creation.
- [ ] Battery voltage and percentage are plausible across charge states.
- [ ] Charging/on-battery state is accurate if exposed.
- [ ] Device temperature and humidity are marked as diagnostics.
- [ ] Light level is either raw or explicitly calibrated.
- [ ] HA disables hardware entities gracefully on older firmware that lacks `/api/hardware`.
- [ ] No hardware endpoint permits configuration changes or factory reset.

## Testing checklist

### Connection

- [ ] Discovers and connects using IP or hostname.
- [ ] Handles unreachable clock gracefully.
- [ ] Detects whether web authentication is enabled.
- [ ] Logs in when password is supplied.
- [ ] Prompts reauthentication after invalid or expired credentials.

### Sensors

- [ ] Blood glucose updates from `/api/status`.
- [ ] `sgv = 0` becomes `unknown`.
- [ ] Data source reflects firmware enum exactly.
- [ ] Source status reflects firmware status code.
- [ ] Firmware version is read correctly.

### Binary sensors

- [ ] Clock connected state follows `isConnected`.
- [ ] Internet state follows `hasInternet`.
- [ ] AP mode follows `isInAPMode`.

### Controls

- [ ] Display switch sends `on` and `off`.
- [ ] Melody button sends valid RTTTL.
- [ ] Invalid RTTTL produces a clear error.
- [ ] Restart is disabled by default.
- [ ] Restart recovers and refreshes firmware version.

### Hardware telemetry

- [ ] Hardware entities are created only when `/api/hardware` is available.
- [ ] Battery voltage and percentage update correctly.
- [ ] Missing battery percentage becomes `unknown`.
- [ ] Device temperature and humidity are exposed as diagnostics.
- [ ] Light level does not claim lux calibration unless supported.
- [ ] Older firmware without `/api/hardware` does not break the integration.

### Security

- [ ] Diagnostics do not leak passwords, cookies, API secrets, or Wi-Fi credentials.
- [ ] No credential field is exposed as a readable entity.
- [ ] No factory-reset control is exposed.

## Implementation order

1. Create integration skeleton and manifest.
2. Implement async API client.
3. Implement config flow.
4. Implement status coordinator.
5. Add glucose, data-source, source-status, and firmware sensors.
6. Add connectivity and AP-mode binary sensors.
7. Add display switch.
8. Add melody and restart buttons.
9. Add diagnostics.
10. Add tests for API parsing, coordinator behavior, auth retry, and entity states.
11. Add README with installation, configuration, entities, and automation examples.
12. Release v1.
13. Implement read-only config diagnostics.
14. Implement staged settings apply workflow.
15. Optionally implement API-source glucose reporting.
16. Add `/api/hardware` firmware endpoint and OpenAPI schema.
17. Add HA hardware-telemetry coordinator and entities.
18. Release hardware-telemetry support.

## Automation examples

### Alert when clock disconnects

```yaml
automation:
  - alias: "NSClock disconnected"
    triggers:
      - trigger: state
        entity_id: binary_sensor.clock_connected
        to: "off"
        for:
          minutes: 5
    actions:
      - action: notify.persistent_notification
        data:
          title: "NSClock offline"
          message: "The NSClock has been disconnected for 5 minutes."
```

### Alert when clock enters AP mode

```yaml
automation:
  - alias: "NSClock access point mode"
    triggers:
      - trigger: state
        entity_id: binary_sensor.access_point_mode
        to: "on"
    actions:
      - action: notify.persistent_notification
        data:
          message: "NSClock entered access-point/setup mode."
```

### Alert when clock switches to battery

```yaml
automation:
  - alias: "NSClock running on battery"
    triggers:
      - trigger: state
        entity_id: binary_sensor.on_battery
        to: "on"
    actions:
      - action: notify.persistent_notification
        data:
          message: "NSClock is now running on battery power."
```

### Turn display off at night

```yaml
automation:
  - alias: "NSClock display off at night"
    triggers:
      - trigger: time
        at: "23:00:00"
    actions:
      - action: switch.turn_off
        target:
          entity_id: switch.display
```

### Turn display on in the morning

```yaml
automation:
  - alias: "NSClock display on in the morning"
    triggers:
      - trigger: time
        at: "07:00:00"
    actions:
      - action: switch.turn_on
        target:
          entity_id: switch.display
```

## Release criteria for v1

- Stable connection and polling.
- Correct glucose, source, source-status, and connectivity entities.
- Safe display and melody controls.
- Robust authentication retry.
- No credentials exposed.
- No direct configuration writes.
- Clear setup, error, and diagnostics experience.
