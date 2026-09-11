from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InspectionTemplate(Base):
    __tablename__ = "inspection_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    template_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    industry: Mapped[str] = mapped_column(String, index=True, nullable=False)
    company_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    inspection_type: Mapped[str] = mapped_column(String, index=True, nullable=False)

    category: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, default="1.0")
    status: Mapped[str] = mapped_column(String, default="Active")

    template_info: Mapped[str] = mapped_column(Text, nullable=False)
    sections: Mapped[str] = mapped_column(Text, nullable=False)