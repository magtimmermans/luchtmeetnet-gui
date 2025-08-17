from homeassistant.components.sensor import SensorEntity,SensorEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, LMN_SENSOR_TYPES_MAP,LMN_SENSOR_TYPES
import requests
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station = entry.data["station"]

    # Dit is de eerste dataset, opgehaald in _init_.py
    entities = []
    for sensor_type, value in coordinator.data.items():
        if sensor_type in LMN_SENSOR_TYPES_MAP:
            description = LMN_SENSOR_TYPES_MAP[sensor_type]
            entities.append(LuchtmeetnetSensor(coordinator, description, station))


    async_add_entities(entities, update_before_add=False)


class LuchtmeetnetSensor(CoordinatorEntity, SensorEntity):
    """Representation of an LuchtmeetNet sensor."""

    def __init__(self, coordinator, description: SensorEntityDescription, station: str):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.pollutant = description.key
        self._attr_unique_id = f"luchtmeetnet_{self.pollutant.lower()}_{station}"
        self.station = station
        self.icon = description.icon
        self._attr_state_class = description.state_class
        self._attr_device_class = description.device_class
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_info = {
            "identifiers": {(DOMAIN, station)},
            "name": f"Luchtmeetnet Station {station}",
            "manufacturer": "Luchtmeetnet",
            "model": "Luchtkwaliteitsensor",
        }

    @property
    def should_poll(self):
        return False  # Coordinator pusht updates

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        _LOGGER.info("Fetching value for pollutant: %s", self.pollutant)
        data = self.coordinator.data
        if not data:
            return None
        if self.pollutant in data:
            # En haal daar de waarde uit
            return data[self.pollutant]

        return None

    async def async_update(self):
        """Vraag een update aan via de coordinator."""
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """Zorg dat we updates ontvangen."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

