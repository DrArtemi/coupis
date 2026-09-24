import unittest
from datetime import datetime

from sqlalchemy.dialects import postgresql

from coupis.db.repositories import OccurrenceRepository


class FakeSession:
    def __init__(self):
        self.count_statement = None
        self.search_statement = None

    def scalar(self, statement):
        self.count_statement = statement
        return 2

    def scalars(self, statement):
        self.search_statement = statement
        return ["first", "second"]


class FakeExtentResult:
    def one(self):
        return datetime(1998, 4, 3), datetime(2024, 11, 8)


class FakeExtentSession:
    def __init__(self):
        self.statement = None

    def execute(self, statement):
        self.statement = statement
        return FakeExtentResult()


class FakeYearlyCountsSession:
    def __init__(self):
        self.statement = None

    def execute(self, statement):
        self.statement = statement
        return [(2022, 3), (2024, 7)]


class OccurrenceRepositorySearchTests(unittest.TestCase):
    def test_search_builds_spatial_and_relational_filters(self):
        session = FakeSession()
        repository = OccurrenceRepository(session)

        items, total = repository.search(
            gbif_taxon_key=2473577,
            dataset_id=20,
            region_geometry_wkt="POLYGON((0 42,1 42,1 43,0 42))",
            bbox=(-1.9, 42.2, 3.2, 43.5),
            observed_from=datetime(2020, 1, 1),
            basis_of_record="HUMAN_OBSERVATION",
            limit=25,
            offset=5,
        )

        sql = str(
            session.search_statement.compile(dialect=postgresql.dialect())
        )
        self.assertEqual(items, ["first", "second"])
        self.assertEqual(total, 2)
        self.assertIn("ST_Covers", sql)
        self.assertIn("ST_Intersects", sql)
        self.assertIn("species.gbif_taxon_key", sql)
        self.assertIn("occurrences.dataset_id", sql)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)

    def test_temporal_extent_aggregates_dated_spatial_records(self):
        session = FakeExtentSession()
        repository = OccurrenceRepository(session)

        extent = repository.temporal_extent(
            species_id=10,
            region_geometry_wkt="POLYGON((0 42,1 42,1 43,0 42))",
        )

        sql = str(session.statement.compile(dialect=postgresql.dialect()))
        self.assertEqual(
            extent,
            (datetime(1998, 4, 3), datetime(2024, 11, 8)),
        )
        self.assertIn("min(occurrences.observed_at)", sql)
        self.assertIn("max(occurrences.observed_at)", sql)
        self.assertIn("ST_Covers", sql)

    def test_yearly_counts_group_dated_spatial_records(self):
        session = FakeYearlyCountsSession()
        repository = OccurrenceRepository(session)

        counts = repository.yearly_counts(
            species_id=10,
            region_geometry_wkt="POLYGON((0 42,1 42,1 43,0 42))",
        )

        sql = str(session.statement.compile(dialect=postgresql.dialect()))
        self.assertEqual(counts, [(2022, 3), (2024, 7)])
        self.assertIn("GROUP BY", sql)
        self.assertIn("extract", sql.lower())
        self.assertIn("ST_Covers", sql)


if __name__ == "__main__":
    unittest.main()
