from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from coupis.db.models.species import Species
from coupis.gbif.occurrences import GbifOccurrence


class SpeciesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def taxon_key_for(occurrence: GbifOccurrence) -> int:
        taxon_key = occurrence.accepted_taxon_key or occurrence.taxon_key
        if taxon_key is None:
            raise ValueError(
                f"GBIF occurrence {occurrence.gbif_id} has no usable taxon key"
            )
        return taxon_key

    def upsert_many(
        self,
        occurrences: Iterable[GbifOccurrence],
    ) -> dict[int, int]:
        rows_by_key: dict[int, dict] = {}

        for occurrence in occurrences:
            taxon_key = self.taxon_key_for(occurrence)
            scientific_name = (
                occurrence.accepted_scientific_name
                or occurrence.scientific_name
            )
            if scientific_name is None:
                raise ValueError(
                    f"GBIF occurrence {occurrence.gbif_id} has no scientific name"
                )

            rows_by_key[taxon_key] = {
                "gbif_taxon_key": taxon_key,
                "scientific_name": scientific_name,
            }

        if not rows_by_key:
            return {}

        insert_statement = insert(Species).values(list(rows_by_key.values()))
        statement = insert_statement.on_conflict_do_update(
            index_elements=[Species.gbif_taxon_key],
            set_={
                "scientific_name": insert_statement.excluded.scientific_name,
            },
        ).returning(Species.id, Species.gbif_taxon_key)

        return {
            gbif_taxon_key: species_id
            for species_id, gbif_taxon_key in self.session.execute(statement)
        }
