import unittest

from backend.app.services import cwa_service
from backend.app.config import settings


class TestTemperatureService(unittest.TestCase):
    def setUp(self):
        cwa_service._cache.update({"payload": None, "fetched_at": None})

    def test_fallback_returns_valid_station_payload(self):
        original_key = settings.cwa_api_key
        settings.cwa_api_key = ""
        try:
            payload = cwa_service.get_latest_station_observations()
        finally:
            settings.cwa_api_key = original_key

        self.assertEqual(payload["source"], "CWA")
        self.assertEqual(payload["status"], "stale")
        self.assertGreater(payload["count"], 0)
        self.assertTrue(all(-20 <= station["temperature_c"] <= 50 for station in payload["stations"]))

    def test_geojson_contains_station_coordinates(self):
        geojson = cwa_service.get_geojson()

        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertGreater(len(geojson["features"]), 0)
        feature = geojson["features"][0]
        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(len(feature["geometry"]["coordinates"]), 2)


if __name__ == "__main__":
    unittest.main()