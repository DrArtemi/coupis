from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from coupis.db.engine import SessionFactory
from coupis.db.repositories import OccurrenceRepository, SpeciesRepository
from coupis.regions import DEFAULT_REGION_CATALOG, RegionCatalog


async def get_region_catalog() -> RegionCatalog:
    return DEFAULT_REGION_CATALOG


RegionCatalogDependency = Annotated[
    RegionCatalog,
    Depends(get_region_catalog),
]


async def get_db_session() -> AsyncIterator[Session]:
    with SessionFactory() as session:
        yield session


DatabaseSessionDependency = Annotated[Session, Depends(get_db_session)]


async def get_occurrence_repository(
    session: DatabaseSessionDependency,
) -> OccurrenceRepository:
    return OccurrenceRepository(session)


OccurrenceRepositoryDependency = Annotated[
    OccurrenceRepository,
    Depends(get_occurrence_repository),
]


async def get_species_repository(
    session: DatabaseSessionDependency,
) -> SpeciesRepository:
    return SpeciesRepository(session)


SpeciesRepositoryDependency = Annotated[
    SpeciesRepository,
    Depends(get_species_repository),
]
