"""Solakon sensor platform."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolakonCoordinator


@dataclass(frozen=True)
class SolakonInverterSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = lambda d: None


INVERTER_SENSORS: tuple[SolakonInverterSensorDescription, ...] = (
    SolakonInverterSensorDescription(
        key="current_power",
        name="Current Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _safe_float(d.get("realtimeData", {}).get("currentPower")),
    ),
    SolakonInverterSensorDescription(
        key="today_energy",
        name="Today's Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _safe_float(d.get("realtimeData", {}).get("today")),
    ),
    SolakonInverterSensorDescription(
        key="total_energy",
        name="Total Lifetime Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _safe_float(d.get("realtimeData", {}).get("totalLifetimeKwh")),
    ),
    SolakonInverterSensorDescription(
        key="status",
        name="Status",
        device_class=None,
        value_fn=lambda d: d.get("realtimeData", {}).get("status"),
    ),
)


@dataclass(frozen=True)
class SolakonBatterySensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = lambda d: None


BATTERY_SENSORS: tuple[SolakonBatterySensorDescription, ...] = (
    SolakonBatterySensorDescription(
        key="current_power",
        name="Current Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _safe_float(d.get("wPpv")),
    ),
    SolakonBatterySensorDescription(
        key="today_energy",
        name="Today's Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _safe_float(d.get("kwhPowerToday")),
    ),
)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolakonCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for group in coordinator.data.get("groups", []):
        inverter = group.get("inverter")
        if inverter and inverter.get("deviceId"):
            device_id = inverter["deviceId"]
            device_info = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                name=group.get("name", f"Solakon Inverter {device_id}"),
                manufacturer="Growatt / Solakon",
                model=inverter.get("model", "Neo-800M"),
                sw_version=inverter.get("firmwareVersion"),
            )
            for description in INVERTER_SENSORS:
                entities.append(
                    SolakonInverterSensor(coordinator, description, device_id, device_info)
                )

        for battery in group.get("batteries", []):
            if battery.get("deviceId"):
                device_id = battery["deviceId"]
                device_info = DeviceInfo(
                    identifiers={(DOMAIN, device_id)},
                    name=f"Solakon Battery {device_id}",
                    manufacturer="Growatt / Solakon",
                    model=battery.get("model", "Battery"),
                )
                for description in BATTERY_SENSORS:
                    entities.append(
                        SolakonBatterySensor(coordinator, description, device_id, device_info)
                    )

    async_add_entities(entities)


class SolakonInverterSensor(CoordinatorEntity[SolakonCoordinator], SensorEntity):
    entity_description: SolakonInverterSensorDescription

    def __init__(
        self,
        coordinator: SolakonCoordinator,
        description: SolakonInverterSensorDescription,
        device_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data.get("inverters", {}).get(self._device_id, {})
        return self.entity_description.value_fn(data)


class SolakonBatterySensor(CoordinatorEntity[SolakonCoordinator], SensorEntity):
    entity_description: SolakonBatterySensorDescription

    def __init__(
        self,
        coordinator: SolakonCoordinator,
        description: SolakonBatterySensorDescription,
        device_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data.get("batteries", {}).get(self._device_id, {})
        return self.entity_description.value_fn(data)
