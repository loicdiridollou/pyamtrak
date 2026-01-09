"""Tools to retrieve data for the different train stations."""

import requests

from pyamtrak.crypto import decrypt_data, get_crypto_parameters

STATIONS_DATA_URL = (
    "https://maps.amtrak.com/services/MapDataService/stations/trainStations"
)


def get_stations() -> list[str]:
    """Retrieve all stations from the API."""
    # Fetch the encrypted data
    response = requests.get(STATIONS_DATA_URL)
    encrypted_data = response.text

    # Decrypt it
    PUBLIC_KEY, S_VALUE, I_VALUE = get_crypto_parameters(None)
    vv = decrypt_data(encrypted_data, PUBLIC_KEY, s_value=S_VALUE, i_value=I_VALUE)[
        "StationsDataResponse"
    ]["features"]

    return sorted([uu["properties"]["StationName"] for uu in vv])
