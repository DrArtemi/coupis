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


if __name__ == "__main__":
    unittest.main()
