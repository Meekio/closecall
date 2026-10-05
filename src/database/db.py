"""
Database engine, session factory, and helper functions.
"""

import sqlite3
import uuid
from pathlib import Path
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import Base, WardrobeItem
from src.config import config


# Resolve absolute path for SQLite
_db_url = config.DATABASE_URL
if _db_url.startswith("sqlite:///"):
    _rel = _db_url[len("sqlite:///"):]
    _abs = Path(__file__).resolve().parent.parent.parent / _rel
    _abs.parent.mkdir(parents=True, exist_ok=True)
    _db_url = f"sqlite:///{_abs}"

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False},  # needed for SQLite + multi-thread
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_connection():
    """Return a raw sqlite3 connection for lightweight tables (preferences, etc.)."""
    # Extract the actual file path from the SQLAlchemy URL
    if _db_url.startswith("sqlite:///"):
        db_path = _db_url[len("sqlite:///"):]
        return sqlite3.connect(db_path)
    raise ValueError(f"get_connection only supports SQLite, got {_db_url}")


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)
    # Also initialize preferences table
    from src.database.preferences import init_preferences_table
    init_preferences_table()


@contextmanager
def get_session():
    """Context manager that provides a SQLAlchemy Session and handles commit/rollback."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── Wardrobe CRUD helpers ───────────────────────────────────────────────────

def add_item(item_data: dict) -> dict:
    """Insert a new WardrobeItem. Generates item_id if not provided. Returns plain dict."""
    if "item_id" not in item_data or not item_data["item_id"]:
        item_data["item_id"] = f"item_{uuid.uuid4().hex[:8]}"
    item = WardrobeItem(**item_data)
    with get_session() as session:
        session.add(item)
        session.flush()
        result = item.to_dict()   # capture while session is open
    return result


def get_item(item_id: str) -> Optional[WardrobeItem]:
    with get_session() as session:
        return session.get(WardrobeItem, item_id)


def update_item(item_id: str, updates: dict) -> Optional[dict]:
    """Update fields on a WardrobeItem. Returns updated dict or None if not found."""
    with get_session() as session:
        item = session.get(WardrobeItem, item_id)
        if item is None:
            return None
        for key, value in updates.items():
            setattr(item, key, value)
        session.flush()
        return item.to_dict()


def delete_item(item_id: str) -> bool:
    with get_session() as session:
        item = session.get(WardrobeItem, item_id)
        if item is None:
            return False
        session.delete(item)
    return True


def get_all_items(user_id: str = "default_user") -> List[dict]:
    """Return all wardrobe items for a user as plain dicts."""
    with get_session() as session:
        items = session.query(WardrobeItem).filter_by(user_id=user_id).all()
        return [i.to_dict() for i in items]


def get_item_dict(item_id: str) -> Optional[dict]:
    """Return a single item as a plain dict, or None."""
    with get_session() as session:
        item = session.get(WardrobeItem, item_id)
        if item is None:
            return None
        return item.to_dict()


def get_items_by_category(user_id: str = "default_user", category: str = "") -> List[dict]:
    """Return items filtered by category (empty string = all)."""
    with get_session() as session:
        q = session.query(WardrobeItem).filter_by(user_id=user_id)
        if category:
            q = q.filter(WardrobeItem.category == category)
        return [i.to_dict() for i in q.all()]


def query_items(user_id: str, filters: dict) -> List[dict]:
    """
    Flexible filtered query.

    Supported filter keys:
        status          str         e.g. "clean"
        category        str         e.g. "top"
        categories      list[str]   e.g. ["top", "bottom"]
        min_formality   int
        max_formality   int
        rain_suitable   bool
        season          str         matches if season is in the item's season list
    """
    with get_session() as session:
        q = session.query(WardrobeItem).filter_by(user_id=user_id)

        if "status" in filters:
            q = q.filter(WardrobeItem.status == filters["status"])

        if "category" in filters:
            q = q.filter(WardrobeItem.category == filters["category"])

        if "categories" in filters:
            q = q.filter(WardrobeItem.category.in_(filters["categories"]))

        if "min_formality" in filters:
            q = q.filter(WardrobeItem.formality >= filters["min_formality"])

        if "max_formality" in filters:
            q = q.filter(WardrobeItem.formality <= filters["max_formality"])

        if "rain_suitable" in filters:
            q = q.filter(WardrobeItem.rain_suitable == filters["rain_suitable"])

        items = q.all()

        # Season filter is post-query (JSON list column)
        if "season" in filters:
            wanted = filters["season"].lower()
            items = [
                i for i in items
                if wanted in [s.lower() for s in (i.season or [])]
                or "all-season" in [s.lower() for s in (i.season or [])]
            ]

        return [i.to_dict() for i in items]
