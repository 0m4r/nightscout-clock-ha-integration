# Contributing to NSClock Home Assistant Integration

## Development Setup

### 1. Prerequisites

- Python 3.10+ or 3.11+ (the project uses Python 3.13 in the test environment)
- Home Assistant 2026.2+ (the test environment runs HA 2026.2.3)
- Git

### 2. Fork and Clone

```bash
git clone https://github.com/your-username/nightscout-clock-ha-integration.git
cd nightscout-clock-ha-integration
```

### 3. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Development Dependencies

```bash
pip install -r requirements_test.txt
# Also install the integration in development mode
pip install -e .
```

### 5. Run the Test Suite

```bash
pytest -vv
```

All 21 tests should pass. If tests fail, check the test errors section below.

### 6. Code Style

- Follow the existing code style in the repository (PEP 8 with Home Assistant conventions).
- Use type annotations (`from __future__ import annotations`, `str | None` patterns).
- Never log passwords, cookies, API secrets, or Wi-Fi credentials.
- Use `ConfigEntryAuthFailed` for authentication errors (as defined in `api.py`).
- Use `CoordinatorEntity` for all entities with `_attr_has_entity_name = False`.
- Capture class-level `_attr_*` attributes **before** calling `super().__init__()` in `__init__`, because HA's `Entity.__init__` resets them to `None`.

### 7. Adding a New Entity

If you want to add a new entity:

1. Create a new file in `custom_components/nsclock/` (or add to an existing platform file).
2. Subclass `NightscoutClockEntity` (from `entity.py`).
3. Define class-level `_attr_*` attributes (e.g., `_attr_object_id`, `_attr_name`, `_attr_device_class`, `_attr_icon`, `_attr_state_class`, `_attr_native_unit_of_measurement`, `_attr_entity_category`).
4. Implement an `__init__` that calls `super().__init__(coordinator, config_entry, object_id=..., name=..., device_class=..., icon=..., state_class=..., native_unit_of_measurement=..., entity_category=...)` — **capture class attributes before `super().__init__()`**.
5. Register the platform in `PLATFORMS` list in `__init__.py` if it's a new platform type.
6. Add a test in `tests/` following the existing patterns.

### 8. Adding a New API Endpoint

If the clock firmware adds a new endpoint:

1. Add the method to `NightscoutClockApiClient` in `api.py` following the existing patterns:
   - Use `self._request("POST", "/new-endpoint", {...})` or `self._request("GET", "/new-endpoint")`.
   - Handle 401 → login → retry in `_request`.
   - Raise `NightscoutClockApiError` or `ConfigEntryAuthFailed` on failure.
   - Never log the response body/credentials.
2. Add a test mock in `tests/conftest.py` under `mock_api_client`.
3. Add a test in the appropriate `tests/test_*.py` file.

### 9. Adding a New Entity Sensor/Attribute

If you need to expose a new field from `/api/status`:

1. Read the status JSON structure from the clock's API documentation or `/api/status` response.
2. Add a new sensor class in `sensor.py` following the pattern of existing sensors (e.g., `NightscoutClockGlucoseSensor`).
3. Map the API field to the sensor's `native_value` property.
4. Add extra attributes in the `extra_state_attributes` property if needed.
5. Add a test asserting the new state/attribute.

### 10. CI / Pre-commit

The project uses `pytest` for testing. No pre-commit hooks are configured yet, but you can add:

- `ruff` for linting
- `mypy` for type checking
- `pytest` as the test runner

Ensure `pytest -vv` passes before submitting a pull request.

## Project Structure

```
nightscout-clock-ha-integration/
├── custom_components/nsclock/    # Home Assistant integration
│   ├── __init__.py                # Entry point (setup/unload/reload)
│   ├── api.py                     # HTTP API client (session, cookie, 401 retry)
│   ├── entity.py                  # Base entity class
│   ├── coordinator.py             # Data update coordinator
│   ├── sensor.py                  # Sensor entities (4 sensors)
│   ├── binary_sensor.py           # Binary sensor entities (3 sensors)
│   ├── switch.py                  # Switch entities (display power)
│   ├── button.py                  # Button entities (melody, restart)
│   ├── config_flow.py             # Config flow & options
│   ├── manifest.json              # Integration manifest
│   ├── const.py                   # Constants (DOMAIN, CONF_HOST, etc.)
│   ├── services.yaml              # Service definitions
│   └── strings.json / translations/  # UI strings
├── tests/                         # Test suite
│   ├── conftest.py                # Shared fixtures (mock_api_client, etc.)
│   ├── test_init.py               # Setup/unload tests
│   ├── test_config_flow.py        # Config flow tests
│   ├── test_coordinator.py        # Coordinator tests
│   ├── test_sensors.py            # Sensor entity tests
│   ├── test_switch.py             # Switch entity tests
│   ├── test_button.py             # Button entity tests
│   └── fixtures/                  # Test fixtures (status.json)
├── README.md                      # User documentation
├── CONTRIBRISE.md                 # These contribution guidelines
├── pytest.ini                     # Pytest configuration
└── openapi.yaml                   # OpenAPI spec of the clock API
```