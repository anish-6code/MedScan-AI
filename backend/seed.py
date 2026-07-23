"""
seed.py — Seeds the database with a default doctor account.
Run from inside the container:  python seed.py
(alembic upgrade head must have run first)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.crud.user import get_user_by_email, create_user
from app.schemas.user import UserCreate


SEED_USERS = [
    UserCreate(
        name="Dr. Alice Smith",
        email="doctor@example.com",
        password="secret123",
        role="doctor",
    ),
    UserCreate(
        name="Admin User",
        email="admin@example.com",
        password="admin123",
        role="admin",
    ),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for user_data in SEED_USERS:
            existing = get_user_by_email(db, user_data.email)
            if existing:
                print(f"[seed] Skipping {user_data.email} — already exists")
            else:
                user = create_user(db, user_data)
                print(f"[seed] Created {user.role}: {user.email}  (id={user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("[seed] Done.")
