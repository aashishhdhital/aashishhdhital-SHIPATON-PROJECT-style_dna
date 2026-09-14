"""ORM models package.

Importing this package imports every model class so that SQLAlchemy's declarative
metadata (``app.database.Base.metadata``) is aware of all tables. Anything that
needs the full schema registered (e.g. ``create_all``) should
``import app.models`` first.
"""

from app.models.feedback import Feedback
from app.models.inspiration_source import InspirationSource
from app.models.recommendation_result import RecommendationResult
from app.models.recommendation_session import RecommendationSession
from app.models.style_profile import StyleProfile
from app.models.user import User

__all__ = [
    "User",
    "StyleProfile",
    "InspirationSource",
    "RecommendationSession",
    "RecommendationResult",
    "Feedback",
]
