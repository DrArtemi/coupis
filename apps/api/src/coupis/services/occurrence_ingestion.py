from collections.abc import Iterable

from sqlalchemy.orm import Session

from coupis.db.models.occurrence import Occurrence
from coupis.db.repositories import (
    DatasetRepository,
    OccurrenceRepository,
    SpeciesRepository,
)
from coupis.gbif.occurrences import GbifOccurrence


class OccurrenceIngestionService:
    """Coordinate normalized, batched persistence of GBIF occurrences."""

    def __init__(
        self,
        species_repository: SpeciesRepository,
        dataset_repository: DatasetRepository,
        occurrence_repository: OccurrenceRepository,
    ) -> None:
        self.species_repository = species_repository
        self.dataset_repository = dataset_repository
        self.occurrence_repository = occurrence_repository

    @classmethod
    def from_session(cls, session: Session) -> "OccurrenceIngestionService":
        return cls(
            species_repository=SpeciesRepository(session),
            dataset_repository=DatasetRepository(session),
            occurrence_repository=OccurrenceRepository(session),
        )

    def ingest(
        self,
        occurrences: Iterable[GbifOccurrence],
    ) -> list[Occurrence]:
        occurrences = list(occurrences)
        if not occurrences:
            return []

        species_ids = self.species_repository.upsert_many(occurrences)
        dataset_ids = self.dataset_repository.upsert_many(occurrences)

        entries = [
            (
                occurrence,
                species_ids[
                    self.species_repository.taxon_key_for(occurrence)
                ],
                dataset_ids.get(occurrence.dataset_key),
            )
            for occurrence in occurrences
        ]
        return self.occurrence_repository.upsert_many(entries)
