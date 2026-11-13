# NSClock Home Assistant Integration

This is a Home Assistant integration for
[Nightscout Clock](https://github.com/ktomy/nightscout-clock).

> **Early beta:** This integration is under active development. Features may be
> incomplete or may not work as expected, and compatibility is not guaranteed.

## Installation

<!-- ha-marketplace:exclude-start -->

### Home Assistant Marketplace (2026.11 and newer)

[![Open this repository in the Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=0m4r&repository=nightscout-clock-ha-integration&category=integration)

In Home Assistant, open **Settings → Marketplace**, add this repository from
the link above, install **Nightscout Clock**, then add it under **Settings →
Devices & services**.

### HACS (Home Assistant 2026.10 and older)

1. In Home Assistant, open **HACS → Integrations**.
2. Select the three-dot menu, then **Custom repositories**.
3. Add `https://github.com/0m4r/nightscout-clock-ha-integration` with the
   category **Integration**.
4. Find **Nightscout Clock** in HACS and download it.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and search for
   **Nightscout Clock**.

### Manual installation

1. Copy the `custom_components/nsclock` directory from this repository into
   the Home Assistant configuration directory at
   `/config/custom_components/nsclock`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for
   **Nightscout Clock**.

<!-- ha-marketplace:exclude-end -->

### Configuration

After adding the integration:

1.  Enter the clock's IP address or hostname (e.g., `192.168.1.50` or `nsclock.local`).
2.  If your clock has web authentication enabled, enter the password.
3.  Configure optional settings:
    - **Polling interval**: How often Home Assistant polls the clock (default: 30 seconds, range 10–300).
    - **Default melody**: RTTTL string for the "Play Alarm Melody" button (default: `high:d=4,o=5,b=125:4e7,p,4e7`).
    - **Enable restart button**: Toggle to show a restart button (disabled by default).

Use the **Display On** and **Display Off** buttons to control the screen. The
firmware does not report its current display power state, so these are action
buttons rather than a stateful switch.

## Device settings

Brightness mode and level, time format, clock name, alarm enable switches, and
alarm thresholds are editable in Home Assistant. Changes are staged locally;
they are not sent to the clock until `nsclock.apply_settings` is called. Target
an entity from the clock being configured:

```yaml
action: nsclock.apply_settings
data:
  entity_id: select.brightness_mode_setting
```

Applying settings saves the full clock configuration to preserve fields that
Home Assistant does not expose, restarts the clock, and waits for it to return.

## Reporting glucose to an API-source clock

The `nsclock.report_glucose` service can send one glucose reading to a clock
whose configured data source is `API`. The service checks the clock's current
source immediately before sending; it fails rather than writing if the source
is not `API`. Values must be positive integers in mg/dL, and timestamps must
include a timezone:

```yaml
action: nsclock.report_glucose
data:
  entity_id: sensor.data_source
  sgv: 118
  direction: Flat
  trend: 4
  timestamp: "2026-10-19T14:39:00+00:00"
```

The selected entity identifies which clock receives the entry. The timestamp
is converted to UTC and sent to the firmware as Unix milliseconds. Do not use
this service as a substitute for validating the reading at its source.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Test Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
ruff check --isolated --select E4,E7,E9,F custom_components/nsclock tests
pytest -vv
```
