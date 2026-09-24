from collections.abc import Iterable
from importlib import resources
from typing import Protocol

from .models import Region


class RegionCatalog(Protocol):
    """Boundary implemented by both in-memory and future database catalogs."""

    def get(self, slug: str, version: int | None = None) -> Region:
        """Return a specific revision, or the latest one when omitted."""
        ...

    def list(self, *, latest_only: bool = True) -> list[Region]:
        """Return the available regions in a deterministic order."""
        ...


class RegionNotFoundError(KeyError):
    pass


class InMemoryRegionCatalog:
    def __init__(self, regions: Iterable[Region]) -> None:
        self._regions: dict[tuple[str, int], Region] = {}
        for region in regions:
            key = (region.slug, region.version)
            if key in self._regions:
                raise ValueError(
                    f"Duplicate region revision: {region.slug} v{region.version}"
                )
            self._regions[key] = region

    def get(self, slug: str, version: int | None = None) -> Region:
        if version is not None:
            try:
                return self._regions[(slug, version)]
            except KeyError as error:
                raise RegionNotFoundError(
                    f"Unknown region revision: {slug} v{version}"
                ) from error

        candidates = [
            region
            for (region_slug, _), region in self._regions.items()
            if region_slug == slug
        ]
        if not candidates:
            raise RegionNotFoundError(f"Unknown region: {slug}")
        return max(candidates, key=lambda region: region.version)

    def list(self, *, latest_only: bool = True) -> list[Region]:
        """Return the latest regions, or every revision when requested."""
        regions = sorted(
            self._regions.values(),
            key=lambda region: (region.slug, region.version),
        )
        if not latest_only:
            return regions

        latest_by_slug: dict[str, Region] = {}
        for region in regions:
            latest_by_slug[region.slug] = region
        return list(latest_by_slug.values())


def _load_wkt(filename: str) -> str:
    return (
        resources.files("coupis.regions.data")
        .joinpath(filename)
        .read_text(encoding="utf-8")
        .strip()
    )


DEFAULT_REGION_CATALOG = InMemoryRegionCatalog(
    [
        Region(
            slug="pyrenees",
            name="Pyrenees",
            version=1,
            geometry_wkt=_load_wkt("pyrenees-v1.wkt"),
            source="Hand-drawn Coupis PoC approximation; not authoritative",
            license="CC0-1.0",
        ),
        Region(
            slug="alps",
            name="Alps",
            version=1,
            geometry_wkt=_load_wkt("alps-v1.wkt"),
            source="Hand-drawn Coupis PoC approximation; not authoritative",
            license="CC0-1.0",
        ),
    ]
)
