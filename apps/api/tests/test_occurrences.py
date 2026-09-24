import unittest
from unittest.mock import patch

from coupis.gbif import GBIFOccurrenceClient, GbifOccurrence
from coupis.gbif import occurrences as occurrences_module


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
                            "datasetKey": "6c2dcbb0-6f9e-11de-8226-b8a03c50a862",
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
        with patch.object(occurrences_module, "occurrences", api):
            result = GBIFOccurrenceClient().search(
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

        with patch.object(occurrences_module, "occurrences", api):
            result = GBIFOccurrenceClient().search(
                2473577,
                max_records=1,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(api.calls[0]["limit"], 1)


if __name__ == "__main__":
    unittest.main()
