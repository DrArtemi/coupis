import unittest

from coupis.taxonomy import SpeciesResolver


class FakeWikidataClient:
    def search_multilingual(self, query, *, languages=None, limit=5):
        self.query = query
        return [{"id": "Q1"}, {"id": "Q2"}, {"id": "Q3"}]

    def get_scientific_names(self, qids):
        assert list(qids) == ["Q1", "Q2", "Q3"]
        return {
            "Q1": "Tetrao urogallus",
            "Q2": "Tetrao urogallus",
        }


class FakeGBIFClient:
    def match_name(self, scientific_name, *, verbose=True):
        return {
            "usage": {
                "key": 2473577,
                "name": "Tetrao urogallus Linnaeus, 1758",
                "canonicalName": scientific_name,
                "rank": "SPECIES",
                "status": "ACCEPTED",
            },
            "diagnostics": {"matchType": "EXACT", "confidence": 100},
            "synonym": False,
            "classification": [{"key": 1, "name": "Animalia"}],
        }


class SpeciesResolverTests(unittest.TestCase):
    def setUp(self):
        self.wikidata = FakeWikidataClient()
        self.resolver = SpeciesResolver(
            wikidata_client=self.wikidata,
            gbif_client=FakeGBIFClient(),
        )

    def test_search_normalizes_deduplicates_and_resolves(self):
        result = self.resolver.search("  Grand   Tétras ")

        self.assertEqual(self.wikidata.query, "grand tetras")
        self.assertIsNotNone(result)
        self.assertEqual(result.taxon_key, 2473577)
        self.assertEqual(result.canonical_name, "Tetrao urogallus")

    def test_search_returns_none_when_wikidata_has_no_taxon_names(self):
        self.wikidata.get_scientific_names = lambda qids: {}

        self.assertIsNone(self.resolver.search("unknown"))


if __name__ == "__main__":
    unittest.main()
