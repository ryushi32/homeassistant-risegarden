from __future__ import annotations
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RiseGardenClient, RiseGardenAPIError
from .const import DOMAIN, PLATFORMS, CONF_EMAIL, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	session = aiohttp.ClientSession()
	client = RiseGardenClient(session, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])

	async def async_update_data():
		try:
			devices = await client.get_devices()
			device_data = {}
			for d in devices:
				device_id = d.get("id")
				try:
					device_data[device_id] = await client.get_device_data(device_id)
				except RiseGardenAPIError as err:
					_LOGGER.debug("Failed to get data for %s: %s", device_id, err)
			return {"devices": devices, "device_data": device_data}
		except RiseGardenAPIError:
			raise

	coordinator = DataUpdateCoordinator(
		hass,
		_LOGGER,
		name=DOMAIN,
		update_method=async_update_data,
		update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
	)

	# Fetch initial data
	await coordinator.async_config_entry_first_refresh()

	# Debug: log a summary of fetched data so we can verify what the coordinator returned
	try:
		data = coordinator.data or {}
		devices = data.get("devices")
		device_data = data.get("device_data")
		_LOGGER.debug("Rise Garden coordinator fetched devices: %s", devices)
		_LOGGER.debug("Rise Garden coordinator fetched device_data keys: %s", list(device_data.keys()) if isinstance(device_data, dict) else device_data)
	except Exception as err:
		_LOGGER.debug("Error while logging coordinator data: %s", err)

	hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
		"client": client,
		"coordinator": coordinator,
		"session": session,
	}

	# forward setup of platforms using the batch API
	# async_forward_entry_setups accepts a list of platforms
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

	return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
	data = hass.data[DOMAIN].pop(entry.entry_id)
	# close session
	session = data.get("session")
	if session and not session.closed:
		await session.close()
	return unload_ok

