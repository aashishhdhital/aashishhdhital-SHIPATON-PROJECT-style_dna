"""MOCK structured style analyzer.

============================ TEMPORARY MOCK ============================
This is a DETERMINISTIC, hard-coded stand-in for the real (future) AI
fashion analyzer. It ignores the actual inspiration content and always
returns the same valid ``StyleDNA`` fixture. Its only jobs are to:
  * behave deterministically,
  * return a schema-valid ``StyleDNA``,
  * be isolated so it can be replaced by a real AI analyzer with no
    changes to routing or persistence.

Later this becomes:
    inspiration (image bytes / resolved Pinterest media)
        -> AI vision analysis
        -> validated StyleDNA
=======================================================================
"""

from __future__ import annotations

from app.schemas.style import StyleDNA, StyleScore


def analyze_inspiration() -> StyleDNA:
    """Return a deterministic mock ``StyleDNA``.

    Takes no inputs on purpose: the mock does not look at the uploaded images
    or Pinterest URLs. Returning a fresh instance each call avoids any shared
    mutable state.
    """
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
