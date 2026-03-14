"""Helpers for seeding stable demo users into the database."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


DEMO_USERS = [
    {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Alex Kim",
        "email": "alex@strugglesense.demo",
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Jordan Lee",
        "email": "jordan@strugglesense.demo",
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000003"),
        "name": "Sam Rivera",
        "email": "sam@strugglesense.demo",
    },
]


def seed_demo_users(session: Session) -> list[User]:
    existing = {
        user.id: user
        for user in session.scalars(select(User).where(User.id.in_([item["id"] for item in DEMO_USERS]))).all()
    }

    for item in DEMO_USERS:
        if item["id"] not in existing:
            session.add(User(id=item["id"], name=item["name"], email=item["email"]))

    session.commit()
    return session.scalars(select(User).order_by(User.name)).all()
