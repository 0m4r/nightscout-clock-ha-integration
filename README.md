# NSClock Home Assistant Integration

## Installation

### Option 1: Manual Installation via HACS (recommended)

1.  Download the contents of the `custom_components/nsclock` directory.
2.  Place the `nsclock` folder in your Home Assistant `custom_components` directory:
    - HassOS: `addons/ hassio_host/share/ha/core_addons/` (or via SSH: `~/addons/configuration.yaml` location)
    - Home Assistant OS: `share/addons/` → `custom_components/`
    - Home Assistant Container: `/config/config_files/`
3.  Restart Home Assistant.
4.  Go to **Settings → Devices and Services → Add Integration** and search for "Nightscout Clock".

### Option 2: Manual Installation via File Editor

1.  Create a virtual environment and install dependencies:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install homeassistant pytest pytest-asyncio pytest-homeassistant-custom-component aiohttp
    ```

2.  Copy the `custom_components/nsclock` directory to your Home Assistant configuration's `custom_components` folder.
3.  Restart Home Assistant.
4.  Go to **Settings → Devices and Services → Add Integration** and search for "Nightscout Clock".

### Configuration

After adding the integration:

1.  Enter the clock's IP address or hostname (e.g., `192.168.1.50` or `nsclock.local`).
2.  If your clock has web authentication enabled, enter the password.
3.  Configure optional settings:
    - **Polling interval**: How often Home Assistant polls the clock (default: 30 seconds, range 10–300).
    - **Default melody**: RTTTL string for the "Play Alarm Melody" button (default: `high:d=4,o=5,b=125:4e7,p,4e7`).
    - **Enable restart button**: Toggle to show a restart button (disabled by default).

## Development

See [CONTRIBRISE.md](CONTRIBRISE.md) for development guidelines.

## Test Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
pytest -vv
```
