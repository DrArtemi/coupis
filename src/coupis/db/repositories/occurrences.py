from collections.abc import Iterable

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from coupis.db.models.occurrence import Occurrence
from coupis.gbif.occurrences import GbifOccurrence


class OccurrenceRepository:
    _FIELDS_TO_UPDATE = (
        "occurrence_id",
        "species_id",
        "dataset_id",
        "observed_at",
        "latitude",
        "longitude",
        "coordinate_uncertainty_m",
        "basis_of_record",
        "occurrence_status",
        "country_code",
        "locality",
        "license",
        "source_url",
        "issues",
        "geom",
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _values(
        occurrence: GbifOccurrence,
        species_id: int,
        dataset_id: int | None,
    ) -> dict:
        return {
            "gbif_id": occurrence.gbif_id,
            "occurrence_id": occurrence.occurrence_id,
            "species_id": species_id,
            "dataset_id": dataset_id,
            "observed_at": occurrence.event_date,
            "latitude": occurrence.latitude,
            "longitude": occurrence.longitude,
            "coordinate_uncertainty_m": occurrence.coordinate_uncertainty_m,
            "basis_of_record": occurrence.basis_of_record,
            "occurrence_status": occurrence.occurrence_status,
            "country_code": occurrence.country_code,
            "locality": occurrence.locality,
            "license": occurrence.license,
            "source_url": occurrence.references,
            "issues": occurrence.issues,
            "geom": WKTElement(
                f"POINT({occurrence.longitude} {occurrence.latitude})",
                srid=4326,
            ),
        }

    def upsert_many(
        self,
        entries: Iterable[tuple[GbifOccurrence, int, int | None]],
    ) -> list[Occurrence]:
        # Dict to make sure we don't insert duplicates in the same batch
        rows_by_gbif_id = {
            occurrence.gbif_id: self._values(
                occurrence,
                species_id,
                dataset_id,
            )
            for occurrence, species_id, dataset_id in entries
        }
        if not rows_by_gbif_id:
            return []

        insert_statement = insert(Occurrence).values(
            list(rows_by_gbif_id.values())
        )
        statement = insert_statement.on_conflict_do_update(
            index_elements=[Occurrence.gbif_id],
            set_={
                field: getattr(insert_statement.excluded, field)
                for field in self._FIELDS_TO_UPDATE
            },
        ).returning(Occurrence)

        return list(self.session.scalars(statement))
