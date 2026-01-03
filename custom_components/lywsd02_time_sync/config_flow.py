import voluptuous as vol
from homeassistant import config_entries
import homeassistant.util.dt as dt_util
from homeassistant.helpers import selector
from . import DOMAIN

class Lywsd02TimeSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LYWSD02 Sync."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="LYWSD02 Time Sync", data=user_input)

        # Get the system default timezone name (e.g., "Europe/Paris")
        default_timezone = dt_util.DEFAULT_TIME_ZONE.key

        schema = vol.Schema({
            vol.Required("temperature_unit", default="C"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["C", "F"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="temperature_unit"
                )
            ),
            # New Timezone Selector
            vol.Required("timezone", default=default_timezone): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    # There isn't a native "timezone" selector, so we use a list of strings
                    # We can use pytz.all_timezones or similar if we import it, 
                    # but a simple text input or a limited list is safer if imports vary.
                    # Ideally, for HA, we let the user type it or pick from a known list.
                    # Since we want a UI dropdown, we'll use HA's zone helper if available,
                    # but typically a simple text field or a pre-filled list is used.
                    # For simplicity/reliability in a custom component:
                    options=sorted(list(dt_util.zoneinfo.available_timezones())),
                )
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema)
