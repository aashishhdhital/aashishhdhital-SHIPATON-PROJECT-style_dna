"""Gemini Vision fashion analyzer.

Used only when ANALYZER_PROVIDER=gemini. Multiple inspiration images are sent
together so Gemini produces ONE StyleDNA for the collection -- not one profile
per photo.

Output is requested as JSON matching the StyleDNA Pydantic schema. We always
re-validate with StyleDNA.model_validate before returning; malformed output
fails explicitly (never falls back to mock).
"""

from __future__ import annotations

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.schemas.style import StyleDNA

_PROMPT = """You are a fashion stylist analyzing a collection of inspiration photos.

Treat ALL images as ONE wardrobe/inspiration collection (not separate outfits).
Identify recurring aesthetics and garments that actually appear.

Return a Style DNA object:
- styles: 1-5 aesthetics with scores 0-100 that sum to roughly 100
- colors: dominant colors as simple lowercase words
- garments: concrete clothing items
- fits: e.g. oversized, relaxed, tailored
- patterns: e.g. solid, stripe, plaid
- materials: e.g. cotton, denim, leather
- traits: short descriptive phrases

Do not invent items that are not supported by the photos.
Use lowercase English words/phrases. No prose outside the JSON schema.
"""


class GeminiAnalyzerError(Exception):
    """Gemini is misconfigured, unreachable, or returned invalid StyleDNA."""


def analyze_images(images: list[tuple[bytes, str]]) -> StyleDNA:
    """Analyze image bytes (data, mime) as one collection -> validated StyleDNA."""
    if not settings.gemini_api_key:
        raise GeminiAnalyzerError("GEMINI_API_KEY is not configured")
    if not images:
        raise GeminiAnalyzerError("Gemini analyzer requires at least one image")

    parts: list[types.Part] = []
    for data, mime in images:
        parts.append(types.Part.from_bytes(data=data, mime_type=mime))
    parts.append(types.Part.from_text(text=_PROMPT))

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=parts,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StyleDNA,
            ),
        )
    except GeminiAnalyzerError:
        raise
    except Exception as exc:
        raise GeminiAnalyzerError(f"Gemini API failure: {exc}") from exc

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, StyleDNA):
        return parsed

    text = getattr(response, "text", None)
    if not text:
        raise GeminiAnalyzerError("Gemini returned empty structured output")
    try:
        return StyleDNA.model_validate_json(text)
    except ValidationError as exc:
        raise GeminiAnalyzerError(
            f"Gemini output failed StyleDNA validation: {exc}"
        ) from exc
