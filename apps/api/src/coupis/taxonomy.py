from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .gbif import GBIFClient
from .wikidata import WikidataClient


@dataclass(frozen=True, slots=True)
class SpeciesResolution:
    matched: bool
    taxon_key: int | None
    scientific_name: str | None
    canonical_name: str | None
    rank: str | None
    status: str | None
    match_type: str | None
    confidence: float
    synonym: bool
    classification: list[dict]


class SpeciesResolver:
    """Resolve a user's species query to the best matching GBIF taxon."""

    _MATCH_PRIORITY = {
        "NONE": 0,
        "HIGHERRANK": 1,
        "FUZZY": 2,
        "EXACT": 3,
    }

    def __init__(
        self,
        *,
        wikidata_client: WikidataClient | None = None,
        gbif_client: GBIFClient | None = None,
    ) -> None:
        self._owns_wikidata_client = wikidata_client is None
        self.wikidata = wikidata_client or WikidataClient()
        self.gbif = gbif_client or GBIFClient()

    @staticmethod
    def normalize_query(query: str) -> str:
        normalized = unicodedata.normalize("NFD", query)
        normalized = normalized.encode("ascii", "ignore").decode("utf-8")
        normalized = re.sub(r"[-_'’]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip().lower()

    def find_scientific_names(
        self,
        query: str,
        *,
        languages: Sequence[str] | None = None,
        limit: int = 5,
    ) -> list[str]:
        hits = self.wikidata.search_multilingual(
            self.normalize_query(query),
            languages=languages,
            limit=limit,
        )
        names_by_qid = self.wikidata.get_scientific_names(
            hit["id"] for hit in hits
        )
        return list(dict.fromkeys(
            names_by_qid[hit["id"]]
            for hit in hits
            if hit["id"] in names_by_qid
        ))

    def validate_candidates(
        self,
        scientific_names: Iterable[str],
    ) -> list[SpeciesResolution]:
        resolutions = []
        for scientific_name in scientific_names:
            match = self.gbif.match_name(scientific_name, verbose=True)
            usage = match.get("usage", {})
            diagnostics = match.get("diagnostics", {})
            resolutions.append(
                SpeciesResolution(
                    matched=bool(usage.get("key")),
                    taxon_key=int(usage.get("key")),
                    scientific_name=usage.get("name"),
                    canonical_name=usage.get("canonicalName"),
                    rank=usage.get("rank"),
                    status=usage.get("status"),
                    match_type=diagnostics.get("matchType"),
                    confidence=diagnostics.get("confidence", 0.0),
                    synonym=bool(match.get("synonym", False)),
                    classification=match.get("classification", []),
                )
            )
        return resolutions

    @classmethod
    def _selection_score(cls, candidate: SpeciesResolution) -> tuple:
        return (
            candidate.matched,
            cls._MATCH_PRIORITY.get(candidate.match_type or "NONE", 0),
            candidate.status == "ACCEPTED",
            candidate.rank in {"SPECIES", "SUBSPECIES"},
            candidate.confidence,
        )

    def select_taxon(
        self,
        candidates: Iterable[SpeciesResolution],
    ) -> SpeciesResolution | None:
        matched_candidates = [candidate for candidate in candidates if candidate.matched]
        if not matched_candidates:
            return None
        return max(matched_candidates, key=self._selection_score)

    def search(
        self,
        query: str,
        languages: Sequence[str] | None = None,
        wikidata_limit: int = 5,
    ) -> SpeciesResolution | None:
        scientific_names = self.find_scientific_names(
            query,
            languages=languages,
            limit=wikidata_limit,
        )
        return self.select_taxon(self.validate_candidates(scientific_names))

    def close(self) -> None:
        if self._owns_wikidata_client:
            self.wikidata.close()
