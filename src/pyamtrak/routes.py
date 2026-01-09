"""Tools to retrieve data for the different train routes."""

import pandas as pd
import requests

from pyamtrak.crypto import decrypt_data, get_crypto_parameters

TRAINS_DATA_URL = "https://maps.amtrak.com/services/MapDataService/trains/getTrainsData"


def get_routes() -> pd.DataFrame:
    """Retrieve all routes from the API."""
    # Fetch the encrypted data
    response = requests.get(TRAINS_DATA_URL)
    encrypted_data = response.text

    # Decrypt it
    PUBLIC_KEY, S_VALUE, I_VALUE = get_crypto_parameters(None)
    vv = decrypt_data(encrypted_data, PUBLIC_KEY, s_value=S_VALUE, i_value=I_VALUE)[
        "features"
    ]

    services = {uu["properties"]["RouteName"] for uu in vv}

    dic = {}
    for service in sorted(services):
        if "Michigan" in service or "Illinois Service" in service:
            service_str = " / ".join([service.split("/")[1], service.split("/")[0]])
        else:
            service_str = service
        dic[service_str] = {
            "Active": len(
                [
                    uu["properties"]
                    for uu in vv
                    if uu["properties"]["RouteName"] == service
                    and uu["properties"]["TrainState"] == "Active"
                ]
            ),
            "Pending": len(
                [
                    uu["properties"]
                    for uu in vv
                    if uu["properties"]["RouteName"] == service
                    and uu["properties"]["TrainState"] == "Predeparture"
                ]
            ),
            "Completed": len(
                [
                    uu["properties"]
                    for uu in vv
                    if uu["properties"]["RouteName"] == service
                    and uu["properties"]["TrainState"] == "Completed"
                ]
            ),
        }

    return pd.DataFrame.from_dict(dic, orient="index").sort_index()
