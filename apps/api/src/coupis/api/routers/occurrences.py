from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from coupis.api.dependencies import (
    OccurrenceRepositoryDependency,
    RegionCatalogDependency,
)
from coupis.api.schemas import (
    OccurrencePageResponse,
    OccurrenceResponse,
    OccurrenceTemporalExtentResponse,
    OccurrenceYearCountResponse,
    OccurrenceYearlyCountsResponse,
)
from coupis.regions import RegionCatalog, RegionNotFoundError


router = APIRouter(prefix="/occurrences", tags=["occurrences"])


def _region_geometry_wkt(
    region_catalog: RegionCatalog,
    region_slug: str,
    region_version: int | None,
) -> str:
    try:
        return region_catalog.get(region_slug, region_version).geometry_wkt
    except RegionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.args[0],
        ) from error


def _parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        coordinates = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="bbox must contain four numbers: west,south,east,north",
        ) from error
    if len(coordinates) != 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="bbox must contain four numbers: west,south,east,north",
        )

    west, south, east, north = coordinates
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "bbox must satisfy -180 <= west < east <= 180 and "
                "-90 <= south < north <= 90"
            ),
        )
    return west, south, east, north


@router.get(
    "/temporal-extent",
    response_model=OccurrenceTemporalExtentResponse,
)
async def get_occurrence_temporal_extent(
    repository: OccurrenceRepositoryDependency,
    region_catalog: RegionCatalogDependency,
    species_id: Annotated[int, Query(ge=1)],
    region_slug: str,
    region_version: Annotated[int | None, Query(ge=1)] = None,
) -> OccurrenceTemporalExtentResponse:
    observed_from, observed_until = repository.temporal_extent(
        species_id=species_id,
        region_geometry_wkt=_region_geometry_wkt(
            region_catalog,
            region_slug,
            region_version,
        ),
    )
    return OccurrenceTemporalExtentResponse(
        observed_from=observed_from,
        observed_until=observed_until,
    )


@router.get(
    "/yearly-counts",
    response_model=OccurrenceYearlyCountsResponse,
)
async def get_occurrence_yearly_counts(
    repository: OccurrenceRepositoryDependency,
    region_catalog: RegionCatalogDependency,
    species_id: Annotated[int, Query(ge=1)],
    region_slug: str,
    region_version: Annotated[int | None, Query(ge=1)] = None,
) -> OccurrenceYearlyCountsResponse:
    rows = repository.yearly_counts(
        species_id=species_id,
        region_geometry_wkt=_region_geometry_wkt(
            region_catalog,
            region_slug,
            region_version,
        ),
    )
    return OccurrenceYearlyCountsResponse(
        items=[
            OccurrenceYearCountResponse(year=year, count=count)
            for year, count in rows
        ]
    )


@router.get("", response_model=OccurrencePageResponse)
async def list_occurrences(
    repository: OccurrenceRepositoryDependency,
    region_catalog: RegionCatalogDependency,
    species_id: Annotated[int | None, Query(ge=1)] = None,
    gbif_taxon_key: Annotated[int | None, Query(ge=1)] = None,
    dataset_id: Annotated[int | None, Query(ge=1)] = None,
    region_slug: str | None = None,
    region_version: Annotated[int | None, Query(ge=1)] = None,
    bbox: str | None = None,
    observed_from: datetime | None = None,
    observed_until: datetime | None = None,
    basis_of_record: str | None = None,
    occurrence_status: str | None = None,
    country_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OccurrencePageResponse:
    if region_version is not None and region_slug is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="region_version requires region_slug",
        )
    if (
        observed_from is not None
        and observed_until is not None
        and observed_from > observed_until
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="observed_from must be before or equal to observed_until",
        )

    region_geometry_wkt = (
        _region_geometry_wkt(region_catalog, region_slug, region_version)
        if region_slug is not None
        else None
    )

    items, total = repository.search(
        species_id=species_id,
        gbif_taxon_key=gbif_taxon_key,
        dataset_id=dataset_id,
        region_geometry_wkt=region_geometry_wkt,
        bbox=_parse_bbox(bbox),
        observed_from=observed_from,
        observed_until=observed_until,
        basis_of_record=basis_of_record,
        occurrence_status=occurrence_status,
        country_code=country_code.upper() if country_code else None,
        limit=limit,
        offset=offset,
    )
    return OccurrencePageResponse(
        items=[OccurrenceResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
