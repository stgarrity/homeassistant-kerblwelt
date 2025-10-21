"""Constants for the Kerbl Welt integration."""

from datetime import timedelta

# Integration domain
DOMAIN = "kerblwelt"

# Config flow
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Default values
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_NAME = "Kerbl Welt"

# Attributes
ATTR_DEVICE_ID = "device_id"
ATTR_SERIAL_NUMBER = "serial_number"
ATTR_BRAND = "brand"
ATTR_SIGNAL_QUALITY = "signal_quality"
ATTR_BATTERY_STATE = "battery_state"
ATTR_BATTERY_VOLTAGE = "battery_voltage"
ATTR_ALARM_THRESHOLD = "alarm_threshold"
ATTR_REGISTERED_AT = "registered_at"
ATTR_LAST_ONLINE = "last_online"
ATTR_NEW_EVENTS = "new_events"

# Platforms
PLATFORMS = ["sensor"]
