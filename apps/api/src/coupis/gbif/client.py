from typing import Any
from pygbif import species


class GBIFClient:
    """Small adapter around the parts of pygbif used by the project."""

    def match_name(self, scientific_name: str, *, verbose: bool = True) -> dict:
        """Match a scientific name against the GBIF backbone taxonomy."""
        return species.name_backbone(
            scientificName=scientific_name,
            verbose=verbose,
        )
