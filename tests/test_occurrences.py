import unittest

from src.biodiversity_explorer.gbif import GBIFOccurrenceClient, GbifOccurrence


class FakeOccurrencesAPI:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.calls = []

    def search(self, **params):
        self.calls.append(params)
        return next(self.pages)


class GBIFOccurrenceClientTests(unittest.TestCase):
    def test_search_maps_records_and_paginates(self):
        api = FakeOccurrencesAPI(
            [
                {
                    "results": [
                        {
                            "key": 123,
                            "scientificName": "Tetrao urogallus",
                            "decimalLatitude": 42.7,
                            "decimalLongitude": 0.5,
                            "eventDate": "2024-05-02",
                            "coordinateUncertaintyInMeters": 25,
                            "datasetKey": "dataset-id",
                            "datasetTitle": "Bird observations",
                            "license": "http://creativecommons.org/licenses/by/4.0/",
                        }
                    ],
                    "endOfRecords": False,
                },
                {
                    "results": [
                        {
                            "key": 124,
                            "scientificName": "Tetrao urogallus",
                            "decimalLatitude": 42.8,
                            "decimalLongitude": 0.6,
                        }
                    ],
                    "endOfRecords": True,
                },
            ]
        )
        client = GBIFOccurrenceClient(occurrences_api=api)

        result = client.search(
            2473577,
            geometry="POLYGON((0 42,1 42,1 43,0 43,0 42))",
            page_size=1,
            country="FR",
        )

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], GbifOccurrence)
        self.assertEqual(result[0].gbif_id, 123)
        self.assertEqual(result[0].coordinate_uncertainty_m, 25)
        self.assertEqual(api.calls[0]["taxonKey"], 2473577)
        self.assertTrue(api.calls[0]["hasCoordinate"])
        self.assertFalse(api.calls[0]["hasGeospatialIssue"])
        self.assertEqual(api.calls[0]["offset"], 0)
        self.assertEqual(api.calls[1]["offset"], 1)

    def test_search_honors_max_records(self):
        api = FakeOccurrencesAPI(
            [
                {
                    "results": [
                        {
                            "key": 123,
                            "decimalLatitude": 42.7,
                            "decimalLongitude": 0.5,
                        }
                    ],
                    "endOfRecords": False,
                }
            ]
        )

        result = GBIFOccurrenceClient(occurrences_api=api).search(
            2473577,
            max_records=1,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(api.calls[0]["limit"], 1)


if __name__ == "__main__":
    unittest.main()
