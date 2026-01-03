from __future__ import annotations

import time
import struct
import logging
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from bleak import BleakClient
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import bluetooth
from homeassistant.exceptions import HomeAssistantError
import homeassistant.util.dt as dt_util

DOMAIN = "lywsd02_time_sync"
_LOGGER = logging.getLogger(__name__)

_UUID_TIME = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'
_UUID_TEMO = 'EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6'

def get_tz_offset(timezone_name):
    """Calculate the offset in hours (e.g., 1 for UTC+1)."""
    try:
        target_tz = ZoneInfo(timezone_name)
        now = datetime.now(target_tz)
        return int(now.utcoffset().total_seconds() / 3600)
    except:
        return 0

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    config_temp_unit = entry.data.get("temperature_unit", "C")
    config_timezone_name = entry.data.get("timezone", dt_util.DEFAULT_TIME_ZONE.key)

    @callback
    async def set_time(call: ServiceCall) -> None:
        mac = call.data['mac'].upper()
        if not mac:
            _LOGGER.error("MAC address missing.")
            return

        # 1. Prepare Settings
        # Calculate Offset (e.g., 1 for France Winter)
        calculated_offset = get_tz_offset(config_timezone_name)
        tz_offset = call.data.get('tz_offset', calculated_offset)

        temo = call.data.get('temp_mode', '')
        if not temo:
            temo = config_temp_unit
        temo = temo.upper()

        temo_set = False
        data_temp_mode = None
        if temo in 'CF':
            data_temp_mode = struct.pack('B', (0x01 if temo == 'F' else 0xFF))
            temo_set = True

        ckmo = call.data.get('clock_mode', 0)
        ckmo_set = False
        data_clock_mode = None
        if ckmo in [12, 24]:
            data_clock_mode = struct.pack('IHB', 0, 0, 0xaa if ckmo == 12 else 0x00)
            ckmo_set = True

        # 2. Find Device
        ble_device = bluetooth.async_ble_device_from_address(hass, mac, connectable=True)
        if not ble_device:
            ble_device = bluetooth.async_ble_device_from_address(hass, mac, connectable=False)
        
        if not ble_device:
            raise HomeAssistantError(f"Device {mac} not found in range.")

        tout = int(call.data.get('timeout', 60))

        # 3. Connect & Write
        try:
            _LOGGER.info(f"Connecting to {mac}...")
            async with BleakClient(ble_device, timeout=tout) as client:
                
                if not client.is_connected:
                    _LOGGER.warning("Waiting for connection...")
                    await asyncio.sleep(1.0)

                _LOGGER.info(f"Connected to {mac}. Preparing to write...")

                # CORRECTED LOGIC: Send UTC Timestamp
                # The device will calculate: Display Time = UTC + Offset
                utc_timestamp = int(time.time())
                
                # Allow manual override if user really wants to force a specific epoch
                if call.data.get('timestamp'):
                    utc_timestamp = int(call.data['timestamp'])

                # Pack Data: UTC Timestamp + Offset
                data = struct.pack('Ib', utc_timestamp, tz_offset)

                # WRITE 1: Time
                _LOGGER.debug(f"Writing Time: {utc_timestamp} (UTC) + Offset: {tz_offset}h")
                await client.write_gatt_char(_UUID_TIME, data)
                
                # WRITE 2: Temp Unit
                if temo_set and data_temp_mode:
                    await asyncio.sleep(0.5)
                    _LOGGER.debug(f"Writing Unit: {temo}")
                    await client.write_gatt_char(_UUID_TEMO, data_temp_mode)

                # WRITE 3: Clock Mode
                if ckmo_set and data_clock_mode:
                    await asyncio.sleep(0.5)
                    _LOGGER.debug(f"Writing Clock Mode: {ckmo}")
                    await client.write_gatt_char(_UUID_TIME, data_clock_mode)

            _LOGGER.info(f"Success: Synced '{mac}' to UTC {utc_timestamp} + {tz_offset}h")

        except Exception as e:
            _LOGGER.error(f"Failed to connect/write to {mac}: {e}")
            raise e

    hass.services.async_register(DOMAIN, 'set_time', set_time)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.services.async_remove(DOMAIN, 'set_time')
    return True
