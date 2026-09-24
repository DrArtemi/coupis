from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon, mapping

from coupis.api.dependencies import RegionCatalogDependency
from coupis.api.schemas import RegionDetailResponse, RegionSummaryResponse
from coupis.regions import Region, RegionNotFoundError


router = APIRouter(prefix="/regions", tags=["regions"])


def _region_response_data(region: Region) -> dict[str, object]:
    geometry = wkt.loads(region.geometry_wkt)
    if not isinstance(geometry, (Polygon, MultiPolygon)):
        raise ValueError(
            f"Region {region.slug} v{region.version} must be a polygon"
        )

    return {
        "slug": region.slug,
        "name": region.name,
        "version": region.version,
        "source": region.source,
        "license": region.license,
        "geometry": mapping(geometry),
    }


@router.get("", response_model=list[RegionSummaryResponse])
async def list_regions(
    catalog: RegionCatalogDependency,
    include_all_versions: bool = False,
) -> list[RegionSummaryResponse]:
    return [
        RegionSummaryResponse.model_validate(_region_response_data(region))
        for region in catalog.list(latest_only=not include_all_versions)
    ]


@router.get("/{slug}", response_model=RegionDetailResponse)
async def get_region(
    slug: str,
    catalog: RegionCatalogDependency,
    version: Annotated[int | None, Query(ge=1)] = None,
) -> RegionDetailResponse:
    try:
        region = catalog.get(slug, version)
    except RegionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.args[0],
        ) from error
    return RegionDetailResponse.model_validate(_region_response_data(region))
