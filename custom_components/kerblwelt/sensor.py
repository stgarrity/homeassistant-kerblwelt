"""Sensor platform for Kerbl Welt integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ALARM_THRESHOLD,
    ATTR_BATTERY_STATE,
    ATTR_BATTERY_VOLTAGE,
    ATTR_BRAND,
    ATTR_DEVICE_ID,
    ATTR_LAST_ONLINE,
    ATTR_NEW_EVENTS,
    ATTR_REGISTERED_AT,
    ATTR_SERIAL_NUMBER,
    ATTR_SIGNAL_QUALITY,
    DOMAIN,
)
from .coordinator import KerblweltDataUpdateCoordinator

# Import API models
import sys
sys.path.insert(0, "/Users/sgarrity/projects/kerblwelt/kerblwelt-api")
from kerblwelt_api import SmartSatelliteDevice, DeviceEventCount

_LOGGER = logging.getLogger(__name__)


@dataclass
class KerblweltSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[SmartSatelliteDevice], Any]


@dataclass
class KerblweltSensorEntityDescription(
    SensorEntityDescription, KerblweltSensorEntityDescriptionMixin
):
    """Describes Kerbl Welt sensor entity."""

    attributes_fn: Callable[[SmartSatelliteDevice, DeviceEventCount], dict[str, Any]] | None = None


SENSOR_TYPES: tuple[KerblweltSensorEntityDescription, ...] = (
    KerblweltSensorEntityDescription(
        key="fence_voltage",
        name="Fence Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        value_fn=lambda device: device.fence_voltage,
        attributes_fn=lambda device, events: {
            ATTR_ALARM_THRESHOLD: device.fence_voltage_alarm_threshold,
        },
    ),
    KerblweltSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery",
        value_fn=lambda device: device.battery_voltage,
    ),
    KerblweltSensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.battery_state,
        attributes_fn=lambda device, events: {
            ATTR_BATTERY_VOLTAGE: device.battery_voltage,
        },
    ),
    KerblweltSensorEntityDescription(
        key="signal_quality",
        name="Signal Quality",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:signal",
        value_fn=lambda device: device.signal_quality,
    ),
    KerblweltSensorEntityDescription(
        key="event_count",
        name="Event Count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:bell",
        value_fn=lambda device: None,  # Will be set from event count
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kerbl Welt sensors based on a config entry."""
    coordinator: KerblweltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = []

    # Create sensors for each device
    for device_id in coordinator.data:
        device, _ = coordinator.data[device_id]

        for description in SENSOR_TYPES:
            entities.append(
                KerblweltSensor(
                    coordinator,
                    device_id,
                    description,
                )
            )

    async_add_entities(entities)


class KerblweltSensor(CoordinatorEntity[KerblweltDataUpdateCoordinator], SensorEntity):
    """Representation of a Kerbl Welt sensor."""

    entity_description: KerblweltSensorEntityDescription

    def __init__(
        self,
        coordinator: KerblweltDataUpdateCoordinator,
        device_id: str,
        description: KerblweltSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id

        # Get device for initial setup
        device, _ = coordinator.data[device_id]

        # Set unique ID
        self._attr_unique_id = f"{device_id}_{description.key}"

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device.description.strip() or "Kerbl Welt Fence Monitor",
            manufacturer="Kerbl" if device.brand == "ako" else device.brand.title(),
            model="AKO Smart Satellite",
            serial_number=device.identifier,
            sw_version=device.firmware_version,
        )

        # Set entity name
        self._attr_name = f"{device.description.strip()} {description.name}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._device_id not in self.coordinator.data:
            return None

        device, event_count = self.coordinator.data[self._device_id]

        # Special handling for event count
        if self.entity_description.key == "event_count":
            return event_count.new

        return self.entity_description.value_fn(device)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self._device_id not in self.coordinator.data:
            return {}

        device, event_count = self.coordinator.data[self._device_id]

        # Base attributes
        attrs = {
            ATTR_DEVICE_ID: device.id,
            ATTR_SERIAL_NUMBER: device.identifier,
            ATTR_BRAND: device.brand,
            ATTR_REGISTERED_AT: device.registered_at.isoformat(),
        }

        # Add online status
        if device.offline_since:
            attrs[ATTR_LAST_ONLINE] = device.offline_since.isoformat()

        # Add sensor-specific attributes
        if self.entity_description.attributes_fn:
            attrs.update(self.entity_description.attributes_fn(device, event_count))

        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Entity is available if coordinator has data and device is online
        if not self.coordinator.last_update_success:
            return False

        if self._device_id not in self.coordinator.data:
            return False

        device, _ = self.coordinator.data[self._device_id]
        return device.is_online
