from typing import Annotated

from fastapi import APIRouter, Query

from coupis.api.dependencies import SpeciesRepositoryDependency
from coupis.api.schemas import SpeciesPageResponse, SpeciesResponse


router = APIRouter(prefix="/species", tags=["species"])


@router.get("", response_model=SpeciesPageResponse)
async def list_species(
    repository: SpeciesRepositoryDependency,
    q: Annotated[str | None, Query(max_length=200)] = None,
    gbif_taxon_key: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SpeciesPageResponse:
    query = q.strip() if q and q.strip() else None
    items, total = repository.search(
        query=query,
        gbif_taxon_key=gbif_taxon_key,
        limit=limit,
        offset=offset,
    )
    return SpeciesPageResponse(
        items=[SpeciesResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
