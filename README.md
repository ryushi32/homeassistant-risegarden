# Rise Garden Home Assistant Integration

This is a custom Home Assistant integration to connect Rise Gardens devices to Home Assistant using the Rise Garden cloud API.

## Features

- Cloud polling integration using the Rise Garden API
- Sensors per garden: Temperature, Light level, Moisture (when available)
- Light entity per garden with brightness support (0-255 maps to API 0-100)

## Installation

1. Copy the `risegarden` folder into your Home Assistant `custom_components` directory. The path should look like:

   `config/custom_components/risegarden/`

2. Restart Home Assistant.

3. Go to Settings → Devices & Services → Add Integration and search for "Rise Garden". Enter your Rise Garden account email and password when prompted.

## What the integration exposes

For each garden associated with your account the integration will create:

- Sensors (entity ids shown as examples):
  - `sensor.<garden_name>_temperature` — current temperature (°C)
  - `sensor.<garden_name>_light_level` — lamp level (0-100%)
  - `sensor.<garden_name>_moisture` — soil moisture (%) (if available from device)

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
  - Verify the integration is installed in `custom_components/risegarden` and Home Assistant was restarted.
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

- API endpoints and response parsing live in `custom_components/risegarden/api.py`.
- The integration uses a `DataUpdateCoordinator` in `__init__.py` to poll device status and provide data to platforms.
- Sensors are implemented in `sensor.py`. Light control (brightness) is implemented in `light.py` and maps HA brightness to the API's lamp level.

## Tests

Unit tests are not included by default in this README—in the repository there may be a `tests/` folder with pytest tests if provided.

## Contributing

Contributions welcome. Please open an issue or pull request on the repository with changes or fixes.
