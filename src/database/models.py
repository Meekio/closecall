"""
SQLAlchemy ORM models for CloseCall.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, JSON, Text, DateTime
)
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class WardrobeItem(Base):
    """
    Represents a single clothing item in the wardrobe.

    Formality scale:
        1 = loungewear
        2 = casual
        3 = smart casual
        4 = business casual
        5 = formal
    """
    __tablename__ = "wardrobe_items"

    # Primary key
    item_id = Column(String, primary_key=True)

    # User association (single-user prototype, but prepared for multi-user)
    user_id = Column(String, nullable=False, default="default_user", index=True)

    # Core classification
    category = Column(String, nullable=False)       # top / bottom / one_piece / footwear / outerwear
    subtype = Column(String, nullable=False)         # t-shirt / jeans / sneakers / …
    color = Column(String, nullable=False)
    formality = Column(Integer, nullable=False)      # 1–5
    season = Column(JSON, nullable=False)            # list of seasons e.g. ["summer", "all-season"]
    rain_suitable = Column(Boolean, nullable=False, default=False)

    # Status
    status = Column(String, nullable=False, default="clean")  # clean / dirty

    # Vision confidence
    confidence = Column(Float, nullable=True)

    # Storage
    image_path = Column(Text, nullable=True)        # local path or remote URL

    # User-supplied name/label (optional override)
    label = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "user_id": self.user_id,
            "category": self.category,
            "subtype": self.subtype,
            "color": self.color,
            "formality": self.formality,
            "season": self.season,
            "rain_suitable": self.rain_suitable,
            "status": self.status,
            "confidence": self.confidence,
            "image_path": self.image_path,
            "label": self.label,
        }

    def __repr__(self) -> str:
        return (
            f"<WardrobeItem id={self.item_id} "
            f"category={self.category} subtype={self.subtype} "
            f"color={self.color} status={self.status}>"
        )
