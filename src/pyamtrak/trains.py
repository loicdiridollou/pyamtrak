"""Tools to retrieve data for the different train positions."""

from collections import defaultdict
from collections.abc import Sequence

import requests

from pyamtrak.crypto import decrypt_data, get_crypto_parameters

TRAINS_DATA_URL = "https://maps.amtrak.com/services/MapDataService/trains/getTrainsData"


def get_trains() -> dict[str, Sequence[int]]:
    """Retrieve all routes from the API."""
    # Fetch the encrypted data
    response = requests.get(TRAINS_DATA_URL)
    encrypted_data = response.text

    # Decrypt it
    PUBLIC_KEY, S_VALUE, I_VALUE = get_crypto_parameters(None)
    vv = decrypt_data(encrypted_data, PUBLIC_KEY, s_value=S_VALUE, i_value=I_VALUE)[
        "features"
    ]

    all_sta = [uu["properties"] for uu in vv]

    trains_by_route = defaultdict(list)

    for val in all_sta:
        trains_by_route[val["RouteName"]].append(int(val["TrainNum"]))

    return dict(trains_by_route)
