from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


# Import all models here so Alembic autogenerate can detect them
from app.models import user    # noqa: F401, E402
from app.models import patient  # noqa: F401, E402
from app.models import scan     # noqa: F401, E402
from app.models import scan_result  # noqa: F401, E402
from app.models import doctor_correction  # noqa: F401, E402
from app.models import vitals  # noqa: F401, E402
from app.models import alert   # noqa: F401, E402


