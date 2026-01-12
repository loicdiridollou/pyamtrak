"""Flask application for the pyamtrak web interface."""

from urllib.parse import unquote

import requests
from flask import Blueprint, Flask, render_template

from pyamtrak.crypto import decrypt_data, get_crypto_parameters
from pyamtrak.routes import get_routes
from pyamtrak.stations import get_stations
from pyamtrak.trains import get_trains

TRAINS_DATA_URL = "https://maps.amtrak.com/services/MapDataService/trains/getTrainsData"

# Create blueprints
routes_bp = Blueprint("routes", __name__, url_prefix="/routes")
trains_bp = Blueprint("trains", __name__, url_prefix="/trains")
stations_bp = Blueprint("stations", __name__, url_prefix="/stations")


def get_all_train_data() -> list[dict]:
    """Fetch and decrypt all train data from the API."""
    response = requests.get(TRAINS_DATA_URL)
    encrypted_data = response.text
    PUBLIC_KEY, S_VALUE, I_VALUE = get_crypto_parameters(None)
    data = decrypt_data(encrypted_data, PUBLIC_KEY, s_value=S_VALUE, i_value=I_VALUE)
    return [feature["properties"] for feature in data["features"]]


def get_train_by_number(train_num: int) -> dict | None:
    """Get details for a specific train by its number."""
    all_trains = get_all_train_data()
    for train in all_trains:
        if int(train["TrainNum"]) == train_num:
            return train
    return None


@routes_bp.route("/")
def list_routes() -> str:
    """Display all Amtrak routes with train counts by status."""
    df = get_routes()
    routes_dict = df.to_dict(orient="index")
    return render_template("routes.html", routes=routes_dict)


@routes_bp.route("/<path:route_name>")
def route_detail(route_name: str) -> str:
    """Display details for a specific route."""
    route_name = unquote(route_name)
    df = get_routes()
    routes_dict = df.to_dict(orient="index")
    trains_by_route = get_trains()

    # Find matching route (handle the Michigan/Illinois naming)
    status = routes_dict.get(route_name, {"Active": 0, "Pending": 0, "Completed": 0})

    # Find trains for this route
    trains = []
    for name, train_nums in trains_by_route.items():
        if route_name in name or name in route_name:
            trains.extend(train_nums)
    if not trains and route_name in trains_by_route:
        trains = trains_by_route[route_name]

    # Try reverse lookup for Michigan/Illinois routes
    if len(trains) == 0:
        for name, train_nums in trains_by_route.items():
            parts = route_name.split(" / ")
            if len(parts) == 2 and (parts[0] in name or parts[1] in name):
                trains.extend(train_nums)

    return render_template(
        "route_detail.html",
        route_name=route_name,
        trains=sorted(set(trains)),
        status=status,
    )


@trains_bp.route("/")
def list_trains() -> str:
    """Display all trains grouped by route."""
    trains_dict = get_trains()
    return render_template("trains.html", trains=trains_dict)


@trains_bp.route("/<int:train_num>")
def train_detail(train_num: int) -> str:
    """Display details for a specific train."""
    train = get_train_by_number(train_num)
    if train is None:
        return render_template(
            "train_detail.html",
            train_num=train_num,
            train={"RouteName": "Unknown", "TrainState": "Not Found"},
        )
    return render_template("train_detail.html", train_num=train_num, train=train)


@stations_bp.route("/")
def list_stations() -> str:
    """Display all Amtrak stations."""
    stations_list = get_stations()
    return render_template("stations.html", stations=stations_list)


def create_app() -> Flask:
    """Application factory for the Flask app."""
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(routes_bp)
    app.register_blueprint(trains_bp)
    app.register_blueprint(stations_bp)

    @app.route("/")
    def index() -> str:
        df = get_routes()
        routes_dict = df.to_dict(orient="index")
        return render_template("index.html", routes=routes_dict)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
