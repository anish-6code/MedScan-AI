from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


# Import all models here so Alembic autogenerate can detect them
from app.models import user  # noqa: F401, E402
