import unittest

from coupis.regions import (
    DEFAULT_REGION_CATALOG,
    InMemoryRegionCatalog,
    Region,
    RegionNotFoundError,
)
from coupis.services import OccurrenceSearchService


class RegionCatalogTests(unittest.TestCase):
    def test_default_catalog_contains_poc_regions(self):
        self.assertEqual(DEFAULT_REGION_CATALOG.get("pyrenees").version, 1)
        self.assertEqual(DEFAULT_REGION_CATALOG.get("alps").version, 1)

    def test_latest_revision_is_used_by_default(self):
        catalog = InMemoryRegionCatalog(
            [
                Region("test", "Test", 1, "POLYGON((0 0,1 0,1 1,0 0))"),
                Region("test", "Test", 2, "POLYGON((0 0,2 0,2 2,0 0))"),
            ]
        )

        self.assertEqual(catalog.get("test").version, 2)
        self.assertEqual(catalog.get("test", 1).version, 1)

    def test_unknown_region_has_a_clear_error(self):
        with self.assertRaisesRegex(RegionNotFoundError, "Unknown region"):
            DEFAULT_REGION_CATALOG.get("unknown")


class FakeGBIFClient:
    def __init__(self):
        self.calls = []

    def search(self, taxon_key, **params):
        self.calls.append((taxon_key, params))
        return ["occurrence"]


class OccurrenceSearchServiceTests(unittest.TestCase):
    def test_region_geometry_and_filters_are_forwarded(self):
        client = FakeGBIFClient()
        service = OccurrenceSearchService(client)

        result = service.search(
            2473577,
            region_slug="pyrenees",
            region_version=1,
            max_records=10,
            year="2020,2026",
        )

        region = DEFAULT_REGION_CATALOG.get("pyrenees", 1)
        self.assertEqual(result, ["occurrence"])
        self.assertEqual(client.calls[0][0], 2473577)
        self.assertEqual(client.calls[0][1]["geometry"], region.geometry_wkt)
        self.assertEqual(client.calls[0][1]["max_records"], 10)
        self.assertEqual(client.calls[0][1]["year"], "2020,2026")


if __name__ == "__main__":
    unittest.main()
