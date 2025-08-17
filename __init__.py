import logging
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import datetime, timedelta, timezone
from homeassistant.exceptions import ConfigEntryNotReady
import aiohttp

PLATFORMS = [Platform.SENSOR]


from .const import DOMAIN, UPDATE_INTERVAL, API_URL_STATION_DATA, API_URL_LKI_DATA

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Algemene setup (YAML) — minimalistisch, zorg dat hass.data bestaat."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Wordt aangeroepen zodra de gebruiker de integratie toevoegt via de UI
    (config_flow/ConfigEntry). Hier maak je shared resources aan en forward je
    de platforms (sensoren, lights, etc.).
    """
    station = entry.data["station"]

    async def async_update_data():
        """Fetch data from API."""
        sensors = {}
        url = API_URL_STATION_DATA.format(station=station)
        try:
            async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 429:
                            _LOGGER.error("Too many requests to stations API (HTTP 429)")
                            return None
                        if resp.status != 200:
                            _LOGGER.error(
                                "HTTP error with getting stations from the API: %s",
                                resp.status,
                            )
                            return None
                        data = await resp.json()

                        for item in data.get("data", []):
                            formula = item.get("formula")
                            if formula not in sensors:
                                sensors[formula] = item.get("value")

                    fromTime = datetime.now(timezone.utc).replace(minute=0,second=0,microsecond=0) - timedelta(hours=2)
                    fromStr = fromTime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    toTime = datetime.now(timezone.utc).replace(minute=0,second=0,microsecond=0) + timedelta(hours=2)
                    toStr = toTime.strftime("%Y-%m-%dT%H:%M:%SZ")

                    url = API_URL_LKI_DATA.format(station=station, fromStr=fromStr, toStr=toStr)
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 429:
                            _LOGGER.error("Too many requests to API (HTTP 429)")
                            return None
                        if resp.status != 200:
                            _LOGGER.error(
                                "HTTP error with getting LKI data from the API: %s",
                                resp.status,
                            )
                            return None
                        data = await resp.json()

                        for item in data.get("data", []):
                            formula = item.get("formula")
                            if formula not in sensors:
                                sensors[formula] = item.get("value")

                    quality = "Geen data beschikbaar"
                    if "LKI" in sensors:
                            lki = sensors["LKI"]
                            if lki <= 3:
                                quality = "goed"
                            elif lki <= 6:
                                quality = "matig"
                            elif lki <= 8:
                                quality = "onvoldoende"
                            elif lki <= 10:
                                quality = "slecht"
                            elif lki <= 11:
                                quality = "zeer slecht"

                    sensors["quality"] = quality

            # Print the sensors dictionary to see the results
            _LOGGER.info("Sensors: %s", sensors)

            return sensors

        except Exception as ex:
             raise ConfigEntryNotReady(f"Error fetching data: {ex}") from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="luchtmeetnet",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    # Eerste keer data ophalen
    await coordinator.async_config_entry_first_refresh()

    # Opslaan zodat sensor.py er ook bij kan
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])











    # 1) Zorg voor opslagplek per integration
    #hass.data.setdefault(DOMAIN, {})
    # 2) (optioneel) maak en start API-client / DataUpdateCoordinator
    # client = MyApiClient(entry.data["api_key"])
    # coordinator = MyCoordinator(hass, client)
    # await coordinator.async_config_entry_first_refresh()
    # hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coordinator}

    # 3) Laat Home Assistant de platform-modules (sensor.py) laden:
    #await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 4) (optioneel) registreer listeners voor option updates of unload:
    # entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Oprollen bij verwijderen/unload: platforms uitladen en cleanup doen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
