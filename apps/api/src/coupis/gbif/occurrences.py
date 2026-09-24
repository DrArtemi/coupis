from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator
from pygbif import occurrences


class GbifOccurrence(BaseModel):
    gbif_id: int

    taxon_key: int | None
    accepted_taxon_key: int | None

    scientific_name: str | None
    accepted_scientific_name: str | None
    taxon_rank: str | None

    latitude: float
    longitude: float
    coordinate_uncertainty_m: float | None
    geodetic_datum: str | None

    event_date: datetime | None
    year: int | None
    month: int | None
    day: int | None

    basis_of_record: str | None
    occurrence_status: str | None

    country_code: str | None
    state_province: str | None
    locality: str | None

    dataset_key: UUID | None
    dataset_name: str | None
    publishing_org_key: UUID | None

    license: str | None
    references: str | None
    occurrence_id: str | None

    recorded_by: str | None
    identified_by: str | None

    issues: list[str] = []

    @classmethod
    def from_gbif_record(cls, record: dict[str, Any]) -> "GbifOccurrence":
        """Translate an occurrence-search record returned by GBIF."""
        return cls(
            gbif_id=int(record.get("key") or record.get("gbifID")),

            taxon_key=record.get("taxonKey"),
            accepted_taxon_key=record.get("acceptedTaxonKey"),

            scientific_name=record.get("scientificName"),
            accepted_scientific_name=record.get("acceptedScientificName"),
            taxon_rank=record.get("taxonRank"),

            latitude=record.get("decimalLatitude"),
            longitude=record.get("decimalLongitude"),
            coordinate_uncertainty_m=record.get("coordinateUncertaintyInMeters"),
            geodetic_datum=record.get("geodeticDatum"),

            event_date=record.get("eventDate"),
            year=record.get("year"),
            month=record.get("month"),
            day=record.get("day"),

            basis_of_record=record.get("basisOfRecord"),
            occurrence_status=record.get("occurrenceStatus"),

            country_code=record.get("countryCode"),
            state_province=record.get("stateProvince"),
            locality=record.get("locality") or record.get("verbatimLocality"),

            dataset_key=record.get("datasetKey"),
            dataset_name=record.get("datasetName"),
            publishing_org_key=record.get("publishingOrgKey"),

            license=record.get("license"),
            references=record.get("references"),
            occurrence_id=record.get("occurrenceID"),

            recorded_by=record.get("recordedBy"),
            identified_by=record.get("identifiedBy"),

            issues=record.get("issues", []),
        )

    @field_validator("event_date", mode="before")
    @classmethod
    def parse_event_date(cls, value):
        # We only want to keep the beginning of the observation
        if isinstance(value, str) and "/" in value:
            value = value.split("/", maxsplit=1)[0]
        return value


class GBIFOccurrenceClient:
    """Search and normalize georeferenced GBIF occurrence records."""

    MAX_PAGE_SIZE = 300
    _RESERVED_FILTERS = {
        "geometry",
        "hasCoordinate",
        "hasGeospatialIssue",
        "limit",
        "offset",
        "taxonKey",
    }

    def search(
        self,
        taxon_key: int,
        *,
        geometry: str | None = None,
        max_records: int | None = None,
        page_size: int = MAX_PAGE_SIZE,
        exclude_geospatial_issues: bool = True,
        **filters: Any,
    ) -> list[GbifOccurrence]:
        """
        Return normalized occurrences for a taxon, fetching all result pages.

        Additional filters use pygbif/GBIF names, for example ``country``,
        ``year``, ``eventDate``, ``basisOfRecord`` or ``mediatype``.
        """
        if taxon_key <= 0:
            raise ValueError("taxon_key must be a positive integer")
        if not 1 <= page_size <= self.MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size must be between 1 and {self.MAX_PAGE_SIZE}"
            )
        if max_records is not None and max_records < 0:
            raise ValueError("max_records cannot be negative")

        conflicting_filters = self._RESERVED_FILTERS.intersection(filters)
        if conflicting_filters:
            names = ", ".join(sorted(conflicting_filters))
            raise ValueError(f"These filters are managed by the client: {names}")
        if max_records == 0:
            return []

        base_params: dict[str, Any] = {
            **filters,
            "taxonKey": taxon_key,
            "hasCoordinate": True,
        }
        if geometry is not None:
            base_params["geometry"] = geometry
        if exclude_geospatial_issues:
            base_params["hasGeospatialIssue"] = False

        occurrences_list: list[GbifOccurrence] = []
        offset = 0

        while True:
            request_limit = page_size
            if max_records is not None:
                request_limit = min(request_limit, max_records - len(occurrences_list))

            response = occurrences.search(
                **base_params,
                limit=request_limit,
                offset=offset,
            )
            records = response.get("results", [])
            occurrences_list.extend(
                GbifOccurrence.from_gbif_record(record) for record in records
            )

            offset += len(records)
            reached_requested_limit = (
                max_records is not None and len(occurrences_list) >= max_records
            )
            if (
                reached_requested_limit
                or response.get("endOfRecords", False)
                or len(records) < request_limit
                or not records
            ):
                break

        return occurrences_list
