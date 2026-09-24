from typing import Any

from coupis.gbif import GBIFOccurrenceClient, GbifOccurrence
from coupis.regions import DEFAULT_REGION_CATALOG, RegionCatalog


class OccurrenceSearchService:
    """Resolve a versioned region and use it in a GBIF occurrence search."""

    def __init__(
        self,
        gbif_client: GBIFOccurrenceClient,
        region_catalog: RegionCatalog = DEFAULT_REGION_CATALOG,
    ) -> None:
        self.gbif_client = gbif_client
        self.region_catalog = region_catalog

    def search(
        self,
        taxon_key: int,
        *,
        region_slug: str,
        region_version: int | None = None,
        **filters: Any,
    ) -> list[GbifOccurrence]:
        if "geometry" in filters:
            raise ValueError(
                "geometry is supplied by the selected region and cannot be overridden"
            )

        region = self.region_catalog.get(region_slug, region_version)
        return self.gbif_client.search(
            taxon_key,
            geometry=region.geometry_wkt,
            **filters,
        )
