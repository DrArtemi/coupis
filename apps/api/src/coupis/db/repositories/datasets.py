from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from coupis.db.models.dataset import Dataset
from coupis.gbif.occurrences import GbifOccurrence


class DatasetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(
        self,
        occurrences: Iterable[GbifOccurrence],
    ) -> dict[UUID, int]:
        rows_by_key: dict[UUID, dict] = {}

        for occurrence in occurrences:
            dataset_key = occurrence.dataset_key
            if dataset_key is None:
                continue

            row = rows_by_key.setdefault(
                dataset_key,
                {
                    "gbif_dataset_key": dataset_key,
                    "name": None,
                    "license": None,
                },
            )
            if occurrence.dataset_name is not None:
                row["name"] = occurrence.dataset_name
            if occurrence.license is not None:
                row["license"] = occurrence.license

        if not rows_by_key:
            return {}

        insert_statement = insert(Dataset).values(list(rows_by_key.values()))
        statement = insert_statement.on_conflict_do_update(
            index_elements=[Dataset.gbif_dataset_key],
            set_={
                "name": func.coalesce(
                    insert_statement.excluded.name,
                    Dataset.name,
                ),
                "license": func.coalesce(
                    insert_statement.excluded.license,
                    Dataset.license,
                ),
            },
        ).returning(Dataset.id, Dataset.gbif_dataset_key)

        return {
            gbif_dataset_key: dataset_id
            for dataset_id, gbif_dataset_key in self.session.execute(statement)
        }
