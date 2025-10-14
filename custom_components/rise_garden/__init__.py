from __future__ import annotations
import logging
from datetime import timedelta

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RiseGardenClient, RiseGardenAPIError
from .const import DOMAIN, PLATFORMS, CONF_EMAIL, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	# Use Home Assistant's shared aiohttp session to avoid managing lifecycle
	session = async_get_clientsession(hass)
	client = RiseGardenClient(session, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])

	async def async_update_data():
		try:
			devices = await client.get_devices()
			device_data = {}
			for d in devices:
				device_id = d.get("id")
				try:
					status = await client.get_device_data(device_id)
					if status is None:
						_LOGGER.debug("Device %s returned no status, normalizing to empty dict", device_id)
						status = {}
					# Normalize status and ensure 'data' node is a dict
					if status is None:
						_LOGGER.debug("Device %s returned no status, normalizing to empty dict", device_id)
						status = {}
					elif isinstance(status, dict) and status.get("data") is None:
						_LOGGER.debug("Device %s returned status with null 'data' node; normalizing to empty dict", device_id)
						status["data"] = {}
					device_data[device_id] = status
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

	# Fetch initial data (schedule refresh in background to avoid blocking HA startup)
	hass.async_create_task(coordinator.async_config_entry_first_refresh())

	# Debug: log a summary of fetched data so we can verify what the coordinator returned
	try:
		data = coordinator.data or {}
		devices = data.get("devices")
		device_data = data.get("device_data")
		_LOGGER.debug("Rise Garden coordinator fetched devices: %s", devices)
		_LOGGER.debug("Rise Garden coordinator fetched device_data keys: %s", list(device_data.keys()) if isinstance(device_data, dict) else device_data)

		# Per-device details (keys in status.data)
		if isinstance(device_data, dict):
			for dev_id, status in device_data.items():
				try:
					data_node = status.get("data") if isinstance(status, dict) else None
					if isinstance(data_node, dict):
						_LOGGER.debug("Device %s status keys: %s", dev_id, list(data_node.keys()))
					else:
						_LOGGER.debug("Device %s has non-dict data node: %s", dev_id, type(data_node))
				except Exception as err:
					_LOGGER.debug("Error logging device %s details: %s", dev_id, err)
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
	hass.data[DOMAIN].pop(entry.entry_id, None)
	# Don't close Home Assistant's shared session
	return unload_ok

