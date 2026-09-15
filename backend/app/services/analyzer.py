"""Style analyzer dispatcher.

ANALYZER_PROVIDER=mock  -> deterministic fixture (original behavior)
ANALYZER_PROVIDER=gemini -> Gemini Vision over actual image bytes

The mock is preserved so local development does not require API keys.
Real mode never silently falls back to mock.
"""

from __future__ import annotations

from app.config import settings
from app.schemas.style import StyleDNA, StyleScore
from app.services.gemini_analyzer import GeminiAnalyzerError, analyze_images

# Re-export so routers can map the Gemini failure without importing gemini_analyzer.
__all__ = ["analyze_inspiration", "GeminiAnalyzerError"]


def _mock_style_dna() -> StyleDNA:
    """DETERMINISTIC MOCK -- ignores image content on purpose."""
    return StyleDNA(
        styles=[
            StyleScore(name="streetwear", score=45),
            StyleScore(name="minimalist", score=35),
            StyleScore(name="vintage", score=20),
        ],
        colors=["black", "cream", "gray"],
        garments=["oversized jacket", "wide-leg trousers"],
        fits=["oversized", "relaxed"],
        patterns=["solid"],
        materials=["denim", "cotton"],
        traits=["neutral palette", "relaxed silhouette"],
    )


def analyze_inspiration(
    images: list[tuple[bytes, str]] | None = None,
) -> StyleDNA:
    """Return a StyleDNA. ``images`` is a list of (bytes, mime_type)."""
    provider = settings.analyzer_provider
    if provider == "mock":
        return _mock_style_dna()
    if provider == "gemini":
        return analyze_images(images or [])
    raise GeminiAnalyzerError(f"Unknown ANALYZER_PROVIDER: {provider}")
