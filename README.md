# Rise Garden Home Assistant Integration

> ⚠️ Work in progress
>
> This integration is still under active development. It may be incomplete, change frequently, or contain bugs. Use at your own risk and check the repository for the latest updates.

This is a custom Home Assistant integration to connect Rise Garden devices to Home Assistant using the Rise Garden cloud API.

Features
--

- Cloud polling integration using the Rise Garden API
- Sensors per garden: Temperature, Light level, Water volume, Firmware, WiFi signal/rssi
- Light entity per garden with brightness support (0-255 maps to API 0-100)

Installation (development)
--

1. Copy the `rise_garden` folder into your Home Assistant `custom_components` directory. The path should look like:

   `config/custom_components/rise_garden/`

2. Restart Home Assistant.

3. Go to Settings → Devices & Services → Add Integration and search for "Rise Garden". Enter your Rise Garden account email and password when prompted.

Running tests locally
--

This repository includes fast unit tests. The integration imports Home Assistant types which normally require installing the full Home Assistant package. To avoid that and keep tests simple, the repository provides lightweight test-only stubs under `tests/_stubs/homeassistant/`.

These stubs are automatically injected into test time `sys.path` by `tests/conftest.py`, so you can run tests without installing Home Assistant.

Create a virtual environment and run tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pytest ruff
pytest -q
```

Linting
--

Run ruff:

```bash
ruff check .
```

Notes about test stubs and CI
--

- The `tests/_stubs/homeassistant` package contains minimal stub implementations used purely for unit tests and is NOT included in the integration package. This keeps tests fast and avoids requiring a newer system Python for installing modern Home Assistant releases.
- For CI and integration-level validation, add a GitHub Actions workflow that installs an appropriate Home Assistant version on a Python matrix and runs pytest there. This gives higher fidelity than the stubs-based unit tests.

Contributing
--

Contributions welcome. Please open an issue or pull request on the repository with changes or fixes.
# Rise Garden Home Assistant Integration

> ⚠️ Work in progress
>
> This integration is still under active development. It may be incomplete, change frequently, or contain bugs. Use at your own risk and check the repository for the latest updates.

This is a custom Home Assistant integration to connect Rise Gardens devices to Home Assistant using the Rise Garden cloud API.

## Features

- Cloud polling integration using the Rise Garden API
- Sensors per garden: Temperature, Light level, Moisture (when available)
- Light entity per garden with brightness support (0-255 maps to API 0-100)

## Installation

1. Copy the `rise_garden` folder into your Home Assistant `custom_components` directory. The path should look like:

  `config/custom_components/rise_garden/`

2. Restart Home Assistant.

3. Go to Settings → Devices & Services → Add Integration and search for "Rise Garden". Enter your Rise Garden account email and password when prompted.

## What the integration exposes

For each garden associated with your account the integration will create:

- Sensors (entity ids shown as examples):
  - `sensor.<garden_name>_temperature` — current temperature (°C)

- Light entity:
  - `light.<garden_name>_light` — full brightness control. Brightness is a 0-255 Home Assistant value mapped linearly to the device lamp level (0-100).

Entity names use the garden name provided by the Rise Garden API (e.g., "My Herb Garden Temperature"). Unique IDs are stable and based on garden ID plus metric.

## Configuration options

The integration currently supports setup via the UI with the following fields:

- Email: your Rise Garden account email
- Password: your Rise Garden account password

The integration stores tokens returned by the API for polling. No additional configuration is required.

## Troubleshooting

- If entities don't appear after setup:
  - Verify the integration is installed in `custom_components/rise_garden` and Home Assistant was restarted.
  - Check the Home Assistant logs for errors: `Settings → System → Logs`.

- Authentication failures:
  - Confirm your email/password are correct by logging into the Rise Garden app/website.
  - Check logs for authentication or token refresh error messages.

- API/network errors:
  - The client uses the Rise Garden cloud API. Ensure Home Assistant has internet connectivity and DNS is working.
  - If you see DNS or connection errors in logs, check your network and DNS settings.

- Token refresh:
  - The integration attempts to refresh expired tokens. If refresh fails, it will try to log in again. Re-enter credentials in the integration config if required.

## Developer notes

- API endpoints and response parsing live in `custom_components/rise_garden/api.py`.
- The integration uses a `DataUpdateCoordinator` in `__init__.py` to poll device status and provide data to platforms.
- Sensors are implemented in `sensor.py`. Light control (brightness) is implemented in `light.py` and maps HA brightness to the API's lamp level.

## Tests

Unit tests are not included by default in this README—in the repository there may be a `tests/` folder with pytest tests if provided.

## Contributing

Contributions welcome. Please open an issue or pull request on the repository with changes or fixes.
