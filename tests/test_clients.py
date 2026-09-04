import unittest
from unittest.mock import patch

from src.biodiversity_explorer.gbif import client as gbif_client_module
from src.biodiversity_explorer.gbif import GBIFClient
from src.biodiversity_explorer.wikidata import WikidataClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.headers = {}
        self.payload = payload
        self.calls = []
        self.closed = False

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse(self.payload)

    def close(self):
        self.closed = True


class FakeSpeciesAPI:
    def name_backbone(self, **kwargs):
        self.kwargs = kwargs
        return {"usage": {"key": 2473577}}


class ClientTests(unittest.TestCase):
    def test_wikidata_client_identifies_and_batches_requests(self):
        session = FakeSession(
            {
                "entities": {
                    "Q1": {
                        "claims": {
                            "P225": [
                                {
                                    "mainsnak": {
                                        "datavalue": {"value": "Tetrao urogallus"}
                                    }
                                }
                            ]
                        }
                    },
                    "Q2": {"claims": {}},
                }
            }
        )
        client = WikidataClient(
            session=session,
            user_agent="test-client/1.0 (test@example.com)",
        )

        names = client.get_scientific_names(["Q1", "Q2", "Q1"])

        self.assertEqual(names, {"Q1": "Tetrao urogallus"})
        self.assertEqual(session.headers["User-Agent"], "test-client/1.0 (test@example.com)")
        self.assertEqual(session.calls[0][1]["ids"], "Q1|Q2")
        client.close()
        self.assertFalse(session.closed)

    def test_gbif_client_delegates_name_matching(self):
        species_api = FakeSpeciesAPI()
        with patch.object(gbif_client_module, "species", species_api):
            result = GBIFClient().match_name("Tetrao urogallus")

        self.assertEqual(result["usage"]["key"], 2473577)
        self.assertEqual(
            species_api.kwargs,
            {"scientificName": "Tetrao urogallus", "verbose": True},
        )


if __name__ == "__main__":
    unittest.main()
