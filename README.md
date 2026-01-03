# Xiaomi Miija LYWSD02 Time Sync for Home Assistant

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Component-orange)

A native Home Assistant custom component to synchronize **Time** and **Timezone** on Xiaomi Miija LYWSD02 BLE Clock/Thermometers.

This component communicates directly with the device via Bluetooth Low Energy (BLE), ensuring your clocks always display the correct local time. It solves the common issue of these devices drifting or resetting time when batteries are changed. It includes full UI configuration for timezones and temperature units.

## ✨ Features

*   **⚡ Native Async**: Built using Home Assistant's native `bleak` library for reliable Bluetooth communication without blocking the system.
*   **🛠️ Zero Config YAML**: Fully configurable via the Home Assistant UI.
*   **⚙️ Smart Defaults**: Automatically detects your Home Assistant's timezone, or lets you override it per device.
*   **🌍 Complete Sync**: Synchronizes:
    *   Time Zone (Wall clock offset)
    *   Current Time (Unix Timestamp)
    *   Temperature Unit (Celsius/Fahrenheit)

## 📥 Installation

### Option 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Loweack&repository=Xiaomi-LYWSD02-Time-Sync&category=integration)

1.  Open **HACS** in Home Assistant.
2.  Go to the **Integrations** section.
3.  Click the menu (three dots) in the top right corner and select **Custom repositories**.
4.  Paste the URL of your GitHub repository.
5.  Select **Integration** as the category and click **Add**.
6.  Click **Download** on the new "LYWSD02 Time Sync" card.
7.  **Restart Home Assistant**.

### Option 2: Manual Installation

1.  Download the repository.
2.  Copy the `custom_components/lywsd02_time_sync` folder into your Home Assistant's `homeassistant/custom_components/` directory.
3.  **Restart Home Assistant**.

---

## ⚙️ Configuration

1.  Navigate to **Settings** > **Devices & Services**.
2.  Click **+ Add Integration**.
3.  Search for **LYWSD02 Time Sync**.
4.  Enter your global defaults (these apply if you don't override them in the service call):
    *   **Temperature Unit**: Select `C` (Celsius) or `F` (Fahrenheit).
    *   **Timezone**: Select your local timezone (e.g., `Europe/Paris`, `America/New_York`).
5.  Click **Submit**.

---

## 🚀 Usage

You can sync time on your devices using the `lywsd02_time_sync.set_time` service in Automations, Scripts, or Developer Tools.

### Service: `lywsd02_time_sync.set_time`

**Parameters:**
*   `mac` (Required): The BLE MAC address of the device (e.g., `A4:C1:38:XX:XX:XX`).
*   `temp_mode` (Optional): Override the unit (`C` or `F`).
*   `tz_offset` (Optional): Manually force a specific hour offset (e.g., `1`). If omitted, it calculates automatically based on the configured Timezone.

### Example: Automation (YAML)

Synchronizes time every night at 03:00 AM to ensure the clock stays accurate:

```yaml
alias: "[TIME] Sync Xiaomi Miija LYWSD02"
description: >-
  Synchronizes the time on the Xiaomi Miija LYWSD02 in the bedroom every night
  to correct any drift.
triggers:
  - at: "03:15:00"
    trigger: time
actions:
  - action: lywsd02_time_sync.set_time
    data:
      mac: "A4:C1:38:12:34:56"
mode: single
