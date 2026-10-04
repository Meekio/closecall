"""
Wardrobe item upload handler.

Saves the uploaded image to disk, runs vision tagging,
and persists the resulting metadata to the database.
"""

import io
import uuid
import shutil
from pathlib import Path
from typing import Optional

from PIL import Image

from src.config import config
from src.vision.tagger import get_tagger
from src.database.db import add_item


def _ensure_storage() -> Path:
    path = config.IMAGE_STORAGE_PATH
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def upload_from_path(
    image_path: str | Path,
    user_id: str = "default_user",
    label: Optional[str] = None,
) -> dict:
    """
    Process a clothing image from a local file path.

    Steps:
    1. Copy image to storage directory.
    2. Run Gemini vision tagging.
    3. Save metadata to database.

    Returns the created item dict.
    """
    src_path = Path(image_path)
    storage = _ensure_storage()

    item_id = f"item_{uuid.uuid4().hex[:8]}"
    dest_name = f"{item_id}{src_path.suffix.lower()}"
    dest_path = storage / dest_name
    shutil.copy2(src_path, dest_path)

    tagger = get_tagger()
    tag = tagger.tag_image(dest_path)

    item_data = {
        "item_id": item_id,
        "user_id": user_id,
        "category": tag.category,
        "subtype": tag.subtype,
        "color": tag.color,
        "formality": tag.formality,
        "season": tag.season,
        "rain_suitable": tag.rain_suitable,
        "status": tag.status,
        "confidence": tag.confidence,
        "image_path": str(dest_path),
        "label": label,
    }

    add_item(item_data)
    return item_data


def upload_from_pil(
    pil_image: Image.Image,
    user_id: str = "default_user",
    label: Optional[str] = None,
    original_filename: str = "upload.jpg",
) -> dict:
    """
    Process a clothing image from a PIL Image object (from Gradio).

    Saves as JPEG, runs tagging, persists to DB.
    Returns the created item dict.
    """
    storage = _ensure_storage()
    item_id = f"item_{uuid.uuid4().hex[:8]}"
    dest_path = storage / f"{item_id}.jpg"

    # Convert to RGB (handle RGBA PNGs gracefully)
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    pil_image.save(dest_path, format="JPEG", quality=90)

    # Get bytes for tagging
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    tagger = get_tagger()
    tag = tagger.tag_image_bytes(image_bytes, mime_type="image/jpeg")

    item_data = {
        "item_id": item_id,
        "user_id": user_id,
        "category": tag.category,
        "subtype": tag.subtype,
        "color": tag.color,
        "formality": tag.formality,
        "season": tag.season,
        "rain_suitable": tag.rain_suitable,
        "status": tag.status,
        "confidence": tag.confidence,
        "image_path": str(dest_path),
        "label": label,
    }

    add_item(item_data)
    return item_data
