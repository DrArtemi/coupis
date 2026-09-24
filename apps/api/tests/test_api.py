import unittest
from datetime import datetime
from types import SimpleNamespace

import httpx2

from coupis.api.dependencies import (
    get_occurrence_repository,
    get_species_repository,
)
from coupis.api.main import app


class FakeOccurrenceRepository:
    def __init__(self):
        self.calls = []
        self.result = (
            [
                SimpleNamespace(
                    id=1,
                    gbif_id=123,
                    occurrence_id="source:123",
                    species_id=10,
                    dataset_id=20,
                    observed_at=datetime(2024, 5, 2, 10, 30),
                    latitude=42.7,
                    longitude=0.5,
                    coordinate_uncertainty_m=25.0,
                    basis_of_record="HUMAN_OBSERVATION",
                    occurrence_status="PRESENT",
                    country_code="FR",
                    locality="Pyrenees",
                    license="CC_BY_4_0",
                    source_url="https://example.test/123",
                    issues=[],
                )
            ],
            1,
        )

    def search(self, **filters):
        self.calls.append(filters)
        return self.result

    def temporal_extent(self, **filters):
        self.calls.append(filters)
        return datetime(1998, 4, 3), datetime(2024, 11, 8, 14, 30)

    def yearly_counts(self, **filters):
        self.calls.append(filters)
        return [(2022, 3), (2024, 7)]


class FakeSpeciesRepository:
    def __init__(self):
        self.calls = []
        self.result = (
            [
                SimpleNamespace(
                    id=10,
                    gbif_taxon_key=2473577,
                    scientific_name="Tetrao urogallus Linnaeus, 1758",
                    canonical_name="Tetrao urogallus",
                    vernacular_name="Grand Tétras",
                )
            ],
            1,
        )

    def search(self, **filters):
        self.calls.append(filters)
        return self.result


class APITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.occurrence_repository = FakeOccurrenceRepository()
        self.species_repository = FakeSpeciesRepository()

        async def override_occurrence_repository():
            return self.occurrence_repository

        async def override_species_repository():
            return self.species_repository

        app.dependency_overrides[get_occurrence_repository] = (
            override_occurrence_repository
        )
        app.dependency_overrides[get_species_repository] = (
            override_species_repository
        )
        self.client = httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://test",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.clear()

    async def test_health(self):
        response = await self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    async def test_list_regions_returns_latest_revisions_with_geojson(self):
        response = await self.client.get("/api/v1/regions")

        self.assertEqual(response.status_code, 200)
        regions = response.json()
        self.assertEqual(
            {region["slug"] for region in regions},
            {"alps", "pyrenees"},
        )
        self.assertEqual(regions[0]["geometry"]["type"], "Polygon")
        self.assertIsInstance(regions[0]["geometry"]["coordinates"], list)
        self.assertNotIn("geometry_wkt", regions[0])

    async def test_get_region_returns_requested_revision_and_geometry(self):
        response = await self.client.get(
            "/api/v1/regions/pyrenees?version=1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["slug"], "pyrenees")
        self.assertEqual(response.json()["version"], 1)
        self.assertEqual(response.json()["geometry"]["type"], "Polygon")
        self.assertIsInstance(
            response.json()["geometry"]["coordinates"],
            list,
        )
        self.assertNotIn("geometry_wkt", response.json())

    async def test_get_unknown_region_returns_404(self):
        response = await self.client.get("/api/v1/regions/unknown")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Unknown region: unknown")

    async def test_list_occurrences_returns_a_paginated_database_result(self):
        response = await self.client.get(
            "/api/v1/occurrences",
            params={
                "gbif_taxon_key": 2473577,
                "region_slug": "pyrenees",
                "region_version": 1,
                "bbox": "-1.9,42.2,3.2,43.5",
                "country_code": "fr",
                "limit": 25,
                "offset": 5,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["limit"], 25)
        self.assertEqual(payload["offset"], 5)
        self.assertEqual(payload["items"][0]["gbif_id"], 123)

        filters = self.occurrence_repository.calls[0]
        self.assertEqual(filters["gbif_taxon_key"], 2473577)
        self.assertEqual(filters["bbox"], (-1.9, 42.2, 3.2, 43.5))
        self.assertEqual(filters["country_code"], "FR")
        self.assertTrue(filters["region_geometry_wkt"].startswith("POLYGON"))

    async def test_list_occurrences_rejects_an_invalid_bbox(self):
        response = await self.client.get(
            "/api/v1/occurrences?bbox=3,43,-2,42"
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.occurrence_repository.calls, [])

    async def test_occurrence_temporal_extent_uses_species_and_region(self):
        response = await self.client.get(
            "/api/v1/occurrences/temporal-extent",
            params={
                "species_id": 10,
                "region_slug": "pyrenees",
                "region_version": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["observed_from"], "1998-04-03T00:00:00")
        self.assertEqual(
            response.json()["observed_until"],
            "2024-11-08T14:30:00",
        )
        filters = self.occurrence_repository.calls[0]
        self.assertEqual(filters["species_id"], 10)
        self.assertTrue(filters["region_geometry_wkt"].startswith("POLYGON"))

    async def test_occurrence_yearly_counts_use_species_and_region(self):
        response = await self.client.get(
            "/api/v1/occurrences/yearly-counts",
            params={
                "species_id": 10,
                "region_slug": "pyrenees",
                "region_version": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "items": [
                    {"year": 2022, "count": 3},
                    {"year": 2024, "count": 7},
                ]
            },
        )
        filters = self.occurrence_repository.calls[0]
        self.assertEqual(filters["species_id"], 10)
        self.assertTrue(filters["region_geometry_wkt"].startswith("POLYGON"))

    async def test_list_species_returns_a_searchable_paginated_result(self):
        response = await self.client.get(
            "/api/v1/species",
            params={
                "q": "  grand tétras  ",
                "gbif_taxon_key": 2473577,
                "limit": 20,
                "offset": 5,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["canonical_name"], "Tetrao urogallus")
        self.assertEqual(payload["items"][0]["vernacular_name"], "Grand Tétras")

        filters = self.species_repository.calls[0]
        self.assertEqual(filters["query"], "grand tétras")
        self.assertEqual(filters["gbif_taxon_key"], 2473577)
        self.assertEqual(filters["limit"], 20)
        self.assertEqual(filters["offset"], 5)

    async def test_region_version_requires_a_region_slug(self):
        response = await self.client.get(
            "/api/v1/occurrences?region_version=1"
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.occurrence_repository.calls, [])


if __name__ == "__main__":
    unittest.main()
