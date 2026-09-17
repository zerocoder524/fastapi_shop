from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).where(User.email == email)
    )


def add(db: Session, user: User) -> None:
    db.add(user)
