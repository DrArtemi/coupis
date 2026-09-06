import unittest
from uuid import UUID

from coupis.gbif.occurrences import GbifOccurrence
from coupis.services import OccurrenceIngestionService


DATASET_KEY = UUID("6c2dcbb0-6f9e-11de-8226-b8a03c50a862")


def make_occurrence(
    gbif_id: int,
    *,
    dataset_key: UUID | None = DATASET_KEY,
) -> GbifOccurrence:
    return GbifOccurrence.from_gbif_record(
        {
            "key": gbif_id,
            "occurrenceID": f"source:{gbif_id}",
            "taxonKey": 2473577,
            "acceptedTaxonKey": 2473577,
            "scientificName": "Tetrao urogallus Linnaeus, 1758",
            "acceptedScientificName": "Tetrao urogallus Linnaeus, 1758",
            "decimalLatitude": 42.7,
            "decimalLongitude": 0.5,
            "datasetKey": str(dataset_key) if dataset_key else None,
            "datasetName": "Bird observations",
        }
    )


class FakeSpeciesRepository:
    def __init__(self):
        self.calls = []

    @staticmethod
    def taxon_key_for(occurrence):
        return occurrence.accepted_taxon_key or occurrence.taxon_key

    def upsert_many(self, occurrences):
        self.calls.append(list(occurrences))
        return {2473577: 10}


class FakeDatasetRepository:
    def __init__(self):
        self.calls = []

    def upsert_many(self, occurrences):
        self.calls.append(list(occurrences))
        return {DATASET_KEY: 20}


class FakeOccurrenceRepository:
    def __init__(self):
        self.calls = []

    def upsert_many(self, entries):
        entries = list(entries)
        self.calls.append(entries)
        return [f"saved:{entry[0].gbif_id}" for entry in entries]


class OccurrenceIngestionServiceTests(unittest.TestCase):
    def setUp(self):
        self.species_repository = FakeSpeciesRepository()
        self.dataset_repository = FakeDatasetRepository()
        self.occurrence_repository = FakeOccurrenceRepository()
        self.service = OccurrenceIngestionService(
            self.species_repository,
            self.dataset_repository,
            self.occurrence_repository,
        )

    def test_ingest_resolves_foreign_keys_before_occurrence_upsert(self):
        occurrences = [make_occurrence(1), make_occurrence(2, dataset_key=None)]

        saved = self.service.ingest(occurrences)

        self.assertEqual(saved, ["saved:1", "saved:2"])
        self.assertEqual(len(self.species_repository.calls), 1)
        self.assertEqual(len(self.dataset_repository.calls), 1)
        self.assertEqual(len(self.occurrence_repository.calls), 1)
        self.assertEqual(
            self.occurrence_repository.calls[0],
            [
                (occurrences[0], 10, 20),
                (occurrences[1], 10, None),
            ],
        )

    def test_ingest_empty_batch_does_not_call_repositories(self):
        self.assertEqual(self.service.ingest([]), [])
        self.assertEqual(self.species_repository.calls, [])
        self.assertEqual(self.dataset_repository.calls, [])
        self.assertEqual(self.occurrence_repository.calls, [])


if __name__ == "__main__":
    unittest.main()
