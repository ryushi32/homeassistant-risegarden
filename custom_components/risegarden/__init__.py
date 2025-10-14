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

	hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
		"client": client,
		"coordinator": coordinator,
		"session": session,
	}

	# forward setup of platforms
	for platform in PLATFORMS:
		hass.async_create_task(
			hass.config_entries.async_forward_entry_setup(entry, platform)
		)

	return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
	data = hass.data[DOMAIN].pop(entry.entry_id)
	# close session
	session = data.get("session")
	if session and not session.closed:
		await session.close()
	return unload_ok

