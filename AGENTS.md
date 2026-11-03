# Project Guidelines

## Scope and architecture

- This repository provides the `nsclock` Home Assistant custom integration.
  Its implementation lives in `custom_components/nsclock/`; tests are in
  `tests/`.
- Preserve the integration domain `nsclock` and keep it consistent with the
  component directory and `manifest.json`.
- Follow the existing async API-client, coordinator, config-entry, and entity
  patterns. Prefer extending existing helpers and platform modules over
  introducing parallel abstractions.

## Changes and documentation

- Add or update tests for behavior changes. For firmware API changes, keep
  `openapi.yaml`, the API client, and related tests aligned.
- Update user-facing documentation, service descriptions, and translations
  when changing setup, services, or exposed entities.
- Follow `CONTRIBUTING.md` for development setup, entity/API implementation
  details, and project conventions.
- Never log passwords, cookies, API secrets, or Wi-Fi credentials.

## Validation

Install development dependencies with `pip install -r requirements_test.txt`.
Before completing code changes, run:

```bash
ruff check --isolated --select E4,E7,E9,F custom_components/nsclock tests
pytest -vv
```

GitHub Actions also runs Hassfest and HACS validation; run or inspect those
checks when changing integration metadata, packaging, or HACS configuration.
