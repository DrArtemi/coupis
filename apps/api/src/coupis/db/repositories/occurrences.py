from collections.abc import Iterable
from datetime import datetime

from geoalchemy2.elements import WKTElement
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from coupis.db.models.occurrence import Occurrence
from coupis.db.models.species import Species
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

    def search(
        self,
        *,
        species_id: int | None = None,
        gbif_taxon_key: int | None = None,
        dataset_id: int | None = None,
        region_geometry_wkt: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        observed_from: datetime | None = None,
        observed_until: datetime | None = None,
        basis_of_record: str | None = None,
        occurrence_status: str | None = None,
        country_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Occurrence], int]:
        """Return a filtered page and the total number of matching rows."""
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")

        conditions = []
        if species_id is not None:
            conditions.append(Occurrence.species_id == species_id)
        if gbif_taxon_key is not None:
            species_ids = select(Species.id).where(
                Species.gbif_taxon_key == gbif_taxon_key
            )
            conditions.append(Occurrence.species_id.in_(species_ids))
        if dataset_id is not None:
            conditions.append(Occurrence.dataset_id == dataset_id)
        if observed_from is not None:
            conditions.append(Occurrence.observed_at >= observed_from)
        if observed_until is not None:
            conditions.append(Occurrence.observed_at <= observed_until)
        if basis_of_record is not None:
            conditions.append(Occurrence.basis_of_record == basis_of_record)
        if occurrence_status is not None:
            conditions.append(Occurrence.occurrence_status == occurrence_status)
        if country_code is not None:
            conditions.append(Occurrence.country_code == country_code)
        if region_geometry_wkt is not None:
            region_geometry = func.ST_GeomFromText(region_geometry_wkt, 4326)
            conditions.append(func.ST_Covers(region_geometry, Occurrence.geom))
        if bbox is not None:
            west, south, east, north = bbox
            envelope = func.ST_MakeEnvelope(west, south, east, north, 4326)
            conditions.append(func.ST_Intersects(Occurrence.geom, envelope))

        total = self.session.scalar(
            select(func.count())
            .select_from(Occurrence)
            .where(*conditions)
        )
        statement = (
            select(Occurrence)
            .where(*conditions)
            .order_by(
                Occurrence.observed_at.desc().nulls_last(),
                Occurrence.gbif_id,
            )
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement)), int(total or 0)

    def temporal_extent(
        self,
        *,
        species_id: int,
        region_geometry_wkt: str,
    ) -> tuple[datetime | None, datetime | None]:
        """Return the first and last dated observations for a selection."""
        region_geometry = func.ST_GeomFromText(region_geometry_wkt, 4326)
        statement = select(
            func.min(Occurrence.observed_at),
            func.max(Occurrence.observed_at),
        ).where(
            Occurrence.species_id == species_id,
            func.ST_Covers(region_geometry, Occurrence.geom),
            Occurrence.observed_at.is_not(None),
        )
        row = self.session.execute(statement).one()
        return row[0], row[1]

    def yearly_counts(
        self,
        *,
        species_id: int,
        region_geometry_wkt: str,
    ) -> list[tuple[int, int]]:
        """Count dated observations per calendar year for a selection."""
        region_geometry = func.ST_GeomFromText(region_geometry_wkt, 4326)
        year = cast(
            func.extract("year", Occurrence.observed_at),
            Integer,
        ).label("year")
        statement = (
            select(year, func.count())
            .where(
                Occurrence.species_id == species_id,
                func.ST_Covers(region_geometry, Occurrence.geom),
                Occurrence.observed_at.is_not(None),
            )
            .group_by(year)
            .order_by(year)
        )
        return [
            (int(row[0]), int(row[1]))
            for row in self.session.execute(statement)
        ]

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
