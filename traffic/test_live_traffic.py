import io
import os
import unittest
from unittest.mock import patch

from traffic.live_traffic import LiveTrafficError, build_tomtom_live_matrix


class _Response(io.StringIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class LiveTrafficMatrixTests(unittest.TestCase):
    def test_requires_server_side_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(LiveTrafficError, "TOMTOM_API_KEY"):
                build_tomtom_live_matrix([{"latitude": 18.5, "longitude": 73.8}])

    def test_builds_matrix_from_traffic_aware_route_summaries(self):
        payload = (
            '{"routes":[{"summary":{"lengthInMeters":1250,'
            '"travelTimeInSeconds":180,"trafficDelayInSeconds":30}}]}'
        )
        locations = [
            {"latitude": 18.50, "longitude": 73.80},
            {"latitude": 18.51, "longitude": 73.81},
        ]

        with patch.dict(os.environ, {"TOMTOM_API_KEY": "test-key"}, clear=True):
            with patch(
                "traffic.live_traffic.urlopen",
                side_effect=[_Response(payload), _Response(payload)],
            ):
                matrix = build_tomtom_live_matrix(locations, max_workers=1)

        self.assertEqual(matrix["distance_matrix"], [[0.0, 1250.0], [1250.0, 0.0]])
        self.assertEqual(matrix["travel_time_matrix"], [[0.0, 180.0], [180.0, 0.0]])
        self.assertEqual(matrix["metadata"]["traffic_delay_seconds"], 60.0)
        self.assertEqual(matrix["metadata"]["traffic_provider"], "TomTom Routing API")


if __name__ == "__main__":
    unittest.main()
