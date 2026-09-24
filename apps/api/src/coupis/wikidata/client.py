from collections.abc import Iterable, Sequence
from typing import Any

import requests


class WikidataClient:
    API_URL = "https://www.wikidata.org/w/api.php"
    DEFAULT_LANGUAGES = ("fr", "en", "es")

    def __init__(
        self,
        *,
        user_agent: str = "coupis/0.1 (adrien.milcent@drartemi.com)",
        timeout: float = 10,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self._owns_session = session is None
        self.session = session if session is not None else requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _get(self, params: dict[str, Any]) -> dict:
        response = self.session.get(
            self.API_URL,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def search(self, query: str, language: str, limit: int = 10) -> list[dict]:
        payload = self._get(
            {
                "action": "wbsearchentities",
                "search": query,
                "language": language,
                "uselang": language,
                "type": "item",
                "limit": limit,
                "format": "json",
            }
        )
        return payload.get("search", [])

    def search_multilingual(
        self,
        query: str,
        languages: Sequence[str] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search several languages and merge duplicate Wikidata entities."""
        selected_languages = languages or self.DEFAULT_LANGUAGES
        results_by_id: dict[str, dict] = {}

        for language in selected_languages:
            for hit in self.search(query, language, limit=limit):
                qid = hit["id"]
                if qid not in results_by_id:
                    results_by_id[qid] = {
                        **hit,
                        "matched_languages": [language],
                    }
                else:
                    results_by_id[qid]["matched_languages"].append(language)

        return list(results_by_id.values())

    def get_scientific_names(self, qids: Iterable[str]) -> dict[str, str]:
        """Return the P225 taxon name for each entity that defines one."""
        unique_qids = list(dict.fromkeys(qids))
        if not unique_qids:
            return {}

        payload = self._get(
            {
                "action": "wbgetentities",
                "ids": "|".join(unique_qids),
                "props": "claims",
                "format": "json",
            }
        )

        names: dict[str, str] = {}
        for qid in unique_qids:
            claims = payload.get("entities", {}).get(qid, {}).get("claims", {})
            taxon_name_claims = claims.get("P225", [])
            if not taxon_name_claims:
                continue

            value = (
                taxon_name_claims[0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value")
            )
            if isinstance(value, str):
                names[qid] = value

        return names

    def get_scientific_name(self, qid: str) -> str | None:
        return self.get_scientific_names([qid]).get(qid)

    def close(self) -> None:
        if self._owns_session:
            self.session.close()
