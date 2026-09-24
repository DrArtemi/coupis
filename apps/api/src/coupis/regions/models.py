from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Region:
    """An immutable, versioned region boundary used for occurrence searches."""

    slug: str
    name: str
    version: int
    geometry_wkt: str
    source: str | None = None
    license: str | None = None

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("A region slug is required")
        if self.version <= 0:
            raise ValueError("A region version must be a positive integer")
        if not self.geometry_wkt:
            raise ValueError("A region geometry is required")
