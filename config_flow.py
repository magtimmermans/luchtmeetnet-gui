from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import voluptuous as vol

import aiohttp
from geopy.distance import geodesic
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from .const import DOMAIN
import logging


_LOGGER = logging.getLogger(__name__)


async def get_closest_station(home_coords):
    """Find the closest station to the given coordinates using luchtmeetnet API."""
    stations = []
    page = 1
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"https://api.luchtmeetnet.nl/open_api/stations?page={page}&order_by=number",
                    timeout=10,
                ) as resp:
                    _LOGGER.debug(
                        "Request stations page %s, status: %s", page, resp.status
                    )
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
                        stationNum = item.get("number")
                        _LOGGER.debug("Station number: %s", stationNum)

                        async with session.get(
                            f"https://api.luchtmeetnet.nl/open_api/stations/{stationNum}/",
                            timeout=10,
                        ) as respStation:
                            _LOGGER.debug(
                                "Request station %s, status: %s",
                                stationNum,
                                respStation.status,
                            )
                            if respStation.status == 429:
                                _LOGGER.error(
                                    "Too many requests to station %s (HTTP 429)",
                                    stationNum,
                                )
                                continue
                            if respStation.status != 200:
                                _LOGGER.error(
                                    "HTTP error with getting data from station: %s: %s",
                                    stationNum,
                                    respStation.status,
                                )
                                continue
                            stationData = await respStation.json()
                            element = {
                                "number": stationNum,
                                "coords": (
                                    stationData["data"]["geometry"]["coordinates"][1],
                                    stationData["data"]["geometry"]["coordinates"][0],
                                ),
                            }
                            stations.append(element)

                    # Stop als we op de laatste pagina zijn
                    if page >= data.get("pagination", {}).get("last_page", page):
                        break
                    page += 1

            if not stations:
                _LOGGER.error("No stations found for coordinates: %s", home_coords)
                return None

            # Zoek het dichtstbijzijnde station
            closest_station = min(
                stations,
                key=lambda x: geodesic(home_coords, x["coords"]).meters,
            )
            _LOGGER.info(
                "Found closest station: %s at %.1f meters",
                closest_station["number"],
                geodesic(home_coords, closest_station["coords"]).meters,
            )
            return closest_station["number"]

    except aiohttp.ClientError as e:
        _LOGGER.exception("Network error in get_closest_station: %s", e)
        return None
    except Exception as e:
        _LOGGER.exception("Unexpected error in get_closest_station: %s", e)
        return None


class LuchtmeetnetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Luchtmeetnet integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the user step of the config flow."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Station {user_input['station']}", data=user_input
            )

        lat = self.hass.config.latitude
        lon = self.hass.config.longitude
        station = await get_closest_station((lat, lon))

        if not station:
            return self.async_abort(reason="no_station_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("station", default=station): str}),
            description_placeholders={"station": station},
        )

    async def async_step_reconfigure(self, user_input=None) -> ConfigFlowResult:
        """Handle reconfiguration of the integration (e.g. station change)."""
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            # Update the config entry with the new station
            return self.async_update_reload_and_abort(
                reconfigure_entry,
                data_updates={"station": user_input["station"]},
            )

        # Use current station as default
        current_station = reconfigure_entry.data["station"] if reconfigure_entry else None
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({vol.Required("station", default=current_station): str}),
            description_placeholders={"station": current_station},
        )
