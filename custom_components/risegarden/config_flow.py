from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD


class RiseGardenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # basic validation will be handled on setup
            return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
