import unittest

from sqlalchemy.dialects import postgresql

from coupis.db.repositories import SpeciesRepository


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


class SpeciesRepositorySearchTests(unittest.TestCase):
    def test_search_builds_name_and_taxon_key_filters(self):
        session = FakeSession()
        repository = SpeciesRepository(session)

        items, total = repository.search(
            query="grand%tétras",
            gbif_taxon_key=2473577,
            limit=25,
            offset=5,
        )

        sql = str(
            session.search_statement.compile(dialect=postgresql.dialect())
        )
        parameters = session.search_statement.compile(
            dialect=postgresql.dialect()
        ).params
        self.assertEqual(items, ["first", "second"])
        self.assertEqual(total, 2)
        self.assertIn("species.scientific_name ILIKE", sql)
        self.assertIn("species.canonical_name ILIKE", sql)
        self.assertIn("species.vernacular_name ILIKE", sql)
        self.assertIn("species.gbif_taxon_key", sql)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)
        self.assertIn("%grand\\%tétras%", parameters.values())


if __name__ == "__main__":
    unittest.main()
