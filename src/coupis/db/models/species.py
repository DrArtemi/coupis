from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    gbif_taxon_key: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )

    scientific_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    canonical_name: Mapped[str | None] = mapped_column(
        String,
    )

    vernacular_name: Mapped[str | None] = mapped_column(
        String,
    )
