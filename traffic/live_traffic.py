"""Live traffic-aware route-matrix client.

The optimizer works with a pairwise distance/time matrix.  This module keeps
the provider-specific HTTP calls at that boundary, so optimizers never handle
credentials or vendor response formats.  TomTom is used because its routing
response reports both route length and traffic-aware travel time.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


TOMTOM_ROUTE_URL = "https://api.tomtom.com/routing/1/calculateRoute"


class LiveTrafficError(RuntimeError):
    """Raised when a live traffic matrix cannot be obtained safely."""


def _api_key():
    key = os.environ.get("TOMTOM_API_KEY", "").strip()
    if not key:
        raise LiveTrafficError(
            "Live traffic is not configured. Set TOMTOM_API_KEY before "
            "running the kothrud_live scenario."
        )
    return key


def _route_summary(origin, destination, api_key, timeout=15):
    coordinates = (
        f"{origin['latitude']},{origin['longitude']}:"
        f"{destination['latitude']},{destination['longitude']}"
    )
    query = urlencode({
        "key": api_key,
        "traffic": "true",
        "routeType": "fastest",
        "computeTravelTimeFor": "all",
    })
    url = f"{TOMTOM_ROUTE_URL}/{coordinates}/json?{query}"

    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        if error.code == 429:
            raise LiveTrafficError(
                "TomTom rate limit or account quota reached. Wait and try "
                "again, or check the TomTom developer portal quota."
            ) from error
        raise LiveTrafficError(
            f"TomTom routing request failed ({error.code}). Check TOMTOM_API_KEY "
            "and the account quota."
        ) from error
    except (URLError, TimeoutError) as error:
        raise LiveTrafficError(
            "Could not reach TomTom live traffic service. Try again shortly."
        ) from error

    try:
        summary = payload["routes"][0]["summary"]
        return {
            "distance": float(summary["lengthInMeters"]),
            "travel_time": float(summary["travelTimeInSeconds"]),
            "traffic_delay": float(summary.get("trafficDelayInSeconds", 0)),
        }
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise LiveTrafficError("TomTom returned an invalid routing response.") from error


def build_tomtom_live_matrix(locations, max_workers=2):
    """Return pairwise road distance and current-traffic travel-time matrices.

    A small worker pool avoids making the API request one pair at a time while
    remaining conservative with provider rate limits for this five-stop demo.
    """
    if not locations:
        raise LiveTrafficError("At least one location is required for live traffic.")

    api_key = _api_key()
    count = len(locations)
    distance_matrix = [[0.0] * count for _ in range(count)]
    travel_time_matrix = [[0.0] * count for _ in range(count)]
    traffic_delays = []

    pairs = [
        (origin_index, destination_index)
        for origin_index in range(count)
        for destination_index in range(count)
        if origin_index != destination_index
    ]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _route_summary,
                locations[origin_index],
                locations[destination_index],
                api_key,
            ): (origin_index, destination_index)
            for origin_index, destination_index in pairs
        }
        for future in as_completed(futures):
            origin_index, destination_index = futures[future]
            summary = future.result()
            distance_matrix[origin_index][destination_index] = summary["distance"]
            travel_time_matrix[origin_index][destination_index] = summary["travel_time"]
            traffic_delays.append(summary["traffic_delay"])

    return {
        "distance_matrix": distance_matrix,
        "travel_time_matrix": travel_time_matrix,
        "metadata": {
            "source": "TomTom live traffic-aware routing",
            "traffic_provider": "TomTom Routing API",
            "traffic_snapshot_utc": datetime.now(timezone.utc).isoformat(),
            "distance_unit": "metres",
            "travel_time_unit": "seconds",
            "traffic_delay_seconds": sum(traffic_delays),
            "location_count": count,
        },
    }
