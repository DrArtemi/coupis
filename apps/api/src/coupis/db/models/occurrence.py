from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from coupis.db.base import Base


class Occurrence(Base):
    __tablename__ = "occurrences"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    gbif_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    occurrence_id: Mapped[str | None] = mapped_column(
        String,
        index=True,
    )

    species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id"),
        nullable=False,
        index=True,
    )

    dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("datasets.id"),
    )

    observed_at: Mapped[datetime | None]

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    coordinate_uncertainty_m: Mapped[float | None] = mapped_column(
        Float,
    )

    basis_of_record: Mapped[str | None] = mapped_column(
        String,
    )

    occurrence_status: Mapped[str | None] = mapped_column(
        String,
    )

    country_code: Mapped[str | None] = mapped_column(
        String(2),
    )

    locality: Mapped[str | None] = mapped_column(
        String,
    )

    license: Mapped[str | None] = mapped_column(
        String,
    )

    source_url: Mapped[str | None] = mapped_column(
        String,
    )

    issues: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
    )

    geom: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )
