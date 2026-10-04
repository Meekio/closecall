"""
Vision tagging pipeline.

Sends a clothing image to Gemini and returns structured metadata
matching the WardrobeItem schema.
Uses the current google.genai SDK (replaces deprecated google.generativeai).
"""

import base64
import json
import re
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types as genai_types

from pydantic import BaseModel, Field, field_validator

from src.config import config


# ─── Pydantic schema for structured output ───────────────────────────────────

class ClothingTag(BaseModel):
    category: str = Field(
        description="One of: top, bottom, one_piece, footwear, outerwear"
    )
    subtype: str = Field(
        description=(
            "One of: t-shirt, shirt, kurti, jeans, trousers, leggings, palazzo, "
            "sneakers, formal_shoes, flats, sandals, chappal, jacket, dress, skirt, "
            "shorts, blazer, coat, saree, unknown"
        )
    )
    color: str = Field(description="Primary color of the item, e.g. black, white, navy")
    formality: int = Field(
        description="1=loungewear, 2=casual, 3=smart casual, 4=business casual, 5=formal",
        ge=1,
        le=5,
    )
    season: list[str] = Field(
        description="List from: summer, winter, monsoon, spring, all-season"
    )
    rain_suitable: bool = Field(
        description="True if the item can be worn in rain without being damaged"
    )
    status: str = Field(description="clean or dirty", default="clean")
    confidence: float = Field(
        description="Model confidence 0.0–1.0", ge=0.0, le=1.0
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"top", "bottom", "one_piece", "footwear", "outerwear"}
        v = v.lower().strip()
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}, got '{v}'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in {"clean", "dirty"}:
            return "clean"
        return v


# ─── System prompt ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You catalog clothing items for a wardrobe management app.

You will receive ONE photo of ONE clothing item.

Your job is to return ONLY a valid JSON object with exactly these fields:

{
  "category":     <string>   // top | bottom | one_piece | footwear | outerwear
  "subtype":      <string>   // t-shirt | shirt | kurti | jeans | trousers | leggings |
                             // palazzo | sneakers | formal_shoes | flats | sandals |
                             // chappal | jacket | dress | skirt | shorts | blazer |
                             // coat | saree | unknown
  "color":        <string>   // primary color name
  "formality":    <integer>  // 1=loungewear, 2=casual, 3=smart casual,
                             //  4=business casual, 5=formal
  "season":       <array>    // subset of: ["summer","winter","monsoon","spring","all-season"]
  "rain_suitable":<boolean>  // true if item can be worn in rain
  "status":       <string>   // always "clean"
  "confidence":   <float>    // your confidence 0.0–1.0
}

Rules:
- Return ONLY the JSON object. No markdown, no explanation.
- If you cannot determine a field, use "unknown" for strings or 0.5 for confidence.
- Formality guide:
    1 = pyjamas, loungewear
    2 = casual (t-shirt, jeans, sneakers)
    3 = smart casual (chinos, polo, neat kurti)
    4 = business casual (dress shirt, blazer, trousers)
    5 = formal (suit jacket, formal trousers, formal shoes)
- Rain suitability: sneakers=false, formal_shoes=false, flats=depends on material,
  jacket=true, waterproof outerwear=true. Default to false if unsure.
- Status is always "clean".
"""


# ─── Tagger class ─────────────────────────────────────────────────────────────

class VisionTagger:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._model_name = config.GEMINI_VISION_MODEL

    def _parse_response(self, raw_text: str) -> ClothingTag:
        """Parse JSON from model response text."""
        raw_text = raw_text.strip()
        # Strip markdown code fences if present
        raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text)
        raw_text = raw_text.strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned non-JSON response:\n{raw_text}"
            ) from exc

        return ClothingTag(**data)

    def tag_image(self, image_path: str | Path) -> ClothingTag:
        """
        Analyse a clothing image from a local file path.

        Args:
            image_path: Local file path to the image.

        Returns:
            ClothingTag with structured metadata.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image_bytes = image_path.read_bytes()
        suffix = image_path.suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp",
        }
        mime_type = mime_map.get(suffix, "image/jpeg")
        return self.tag_image_bytes(image_bytes, mime_type=mime_type)

    def tag_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> ClothingTag:
        """
        Tag clothing from raw image bytes (used by the Gradio UI).
        """
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=[
                genai_types.Part.from_text(text=_SYSTEM_PROMPT),
                genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
        )
        return self._parse_response(response.text)


# ─── Module-level singleton ───────────────────────────────────────────────────

_tagger: Optional[VisionTagger] = None


def get_tagger() -> VisionTagger:
    global _tagger
    if _tagger is None:
        _tagger = VisionTagger()
    return _tagger
