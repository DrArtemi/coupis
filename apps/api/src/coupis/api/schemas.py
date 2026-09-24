from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str


class GeoJSONPolygonGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class GeoJSONMultiPolygonGeometry(BaseModel):
    type: Literal["MultiPolygon"]
    coordinates: list[list[list[list[float]]]]


GeoJSONRegionGeometry = Annotated[
    GeoJSONPolygonGeometry | GeoJSONMultiPolygonGeometry,
    Field(discriminator="type"),
]


class RegionSummaryResponse(BaseModel):
    slug: str
    name: str
    version: int
    source: str | None
    license: str | None
    geometry: GeoJSONRegionGeometry


class RegionDetailResponse(RegionSummaryResponse):
    pass


class OccurrenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gbif_id: int
    occurrence_id: str | None
    species_id: int
    dataset_id: int | None
    observed_at: datetime | None
    latitude: float
    longitude: float
    coordinate_uncertainty_m: float | None
    basis_of_record: str | None
    occurrence_status: str | None
    country_code: str | None
    locality: str | None
    license: str | None
    source_url: str | None
    issues: list[str] | None


class OccurrencePageResponse(BaseModel):
    items: list[OccurrenceResponse]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class SpeciesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gbif_taxon_key: int
    scientific_name: str
    canonical_name: str | None
    vernacular_name: str | None


class SpeciesPageResponse(BaseModel):
    items: list[SpeciesResponse]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
