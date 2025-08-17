from homeassistant.components.sensor import SensorDeviceClass,SensorStateClass,SensorEntityDescription

DOMAIN = "luchtmeetnet"
UPDATE_INTERVAL = 300  # seconden (5 min)
API_URL_STATION_DATA = "https://api.luchtmeetnet.nl/open_api/stations/{station}/measurements?page=1&order=&order_direction=&formula="
API_URL_LKI_DATA = "https://api.luchtmeetnet.nl/open_api/lki?order_by=timestamp_measured&order_direction=desc&station_number={station}&start={fromStr}&end={toStr}"

LMN_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="PM10",
        name="Luchtmeetnet PM10",
        native_unit_of_measurement="μg/m³",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM10,
    ),
    SensorEntityDescription(
        key="PM2.5",
        name="Luchtmeetnet PM2.5",
        native_unit_of_measurement="μg/m³",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM25,
    ),
    SensorEntityDescription(
        key="NO2",
        name="Luchtmeetnet NO₂",
        native_unit_of_measurement="μg/m³",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.NITROGEN_DIOXIDE,
    ),
    SensorEntityDescription(
        key="PM25",
        name="Luchtmeetnet PM25",
        native_unit_of_measurement="μg/m³",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM25,
    ),
    SensorEntityDescription(
        key="LKI",
        name="Air Quality Index",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        key="quality",
        name="Air Quality Status",
    ),
)

# Makkelijk zoeken op key
LMN_SENSOR_TYPES_MAP: dict[str, SensorEntityDescription] = {
    desc.key: desc for desc in LMN_SENSOR_TYPES
}