from __future__ import annotations

import time
import struct
import logging
from datetime import datetime
from zoneinfo import ZoneInfo # Standard in Python 3.9+

from bleak import BleakClient
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import bluetooth
import homeassistant.util.dt as dt_util

DOMAIN = "lywsd02_time_sync"
_LOGGER = logging.getLogger(__name__)

_UUID_UNITS = 'EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6'
_UUID_TIME = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    config_temp_unit = entry.data.get("temperature_unit", "C")
    # Default to HA system timezone if missing
    config_timezone_name = entry.data.get("timezone", dt_util.DEFAULT_TIME_ZONE.key)

    @callback
    async def set_time(call: ServiceCall) -> None:
        mac = call.data['mac'].upper()
        if not mac:
            return

        # 1. Resolve Timezone Name to Offset (Integer)
        # We need the offset in hours for the device (e.g. +1, -5)
        try:
            # Get current time in the requested timezone
            target_tz = ZoneInfo(config_timezone_name)
            now_in_tz = datetime.now(target_tz)
            
            # Calculate offset in hours (utcoffset returns timedelta)
            # This automatically handles Daylight Saving Time (DST)
            offset_seconds = now_in_tz.utcoffset().total_seconds()
            tz_offset = int(offset_seconds / 3600)
            
            _LOGGER.debug(f"Resolved timezone '{config_timezone_name}' to offset {tz_offset}h")
        except Exception as e:
            _LOGGER.error(f"Error resolving timezone {config_timezone_name}: {e}")
            tz_offset = 0

        # Allow override from service call
        if 'tz_offset' in call.data:
             tz_offset = call.data['tz_offset']

        ble_device = bluetooth.async_ble_device_from_address(hass, mac, connectable=True)
        if not ble_device:
            _LOGGER.error(f"Could not find '{mac}'.")
            return

        # Prepare Temperature Unit
        target_unit = call.data.get('temp_mode', '').upper() or config_temp_unit
        data_temp_mode = b'\x01' if target_unit == 'F' else b'\xff'

        # Calculate Timestamp (Local Time)
        # The device expects a timestamp that matches the "wall clock" time of that timezone
        # NOT UTC timestamp. So if it is 14:00 in Paris, it wants the epoch for 14:00 UTC.
        # This is a quirk of these LYWSD02 devices.
        
        now_ts = int(time.time()) 
        # We need to shift the timestamp by the offset so the device displays "Wall Clock" time
        # Device Time = UTC Epoch + (Offset * 3600)
        device_timestamp = now_ts + (tz_offset * 3600)
        
        # Override if manually provided
        if call.data.get('timestamp'):
            device_timestamp = int(call.data['timestamp'])

        tout = int(call.data.get('timeout', 60))

        try:
            async with BleakClient(ble_device, timeout=tout) as client:
                # Write Time
                data_time = struct.pack('Ib', device_timestamp, tz_offset)
                await client.write_gatt_char(_UUID_TIME, data_time)
                
                # Write Temp Unit
                await client.write_gatt_char(_UUID_UNITS, data_temp_mode, response=True)

                _LOGGER.info(f"Updated '{mac}': Time={device_timestamp}, Offset={tz_offset}h ({config_timezone_name}), Unit={target_unit}")
                
        except Exception as e:
            _LOGGER.error(f"Error connecting to {mac}: {e}")

    hass.services.async_register(DOMAIN, 'set_time', set_time)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.services.async_remove(DOMAIN, 'set_time')
    return True
