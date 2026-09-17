from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import User
from ..repositories import user_repository
from ..schemas import Token, UserCreate
from ..security import create_access_token, hash_password, verify_password


class AuthServiceError(Exception):
    """Base exception for authentication service failures."""


class UserAlreadyExistsError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class AuthPersistenceError(AuthServiceError):
    pass


def register_user(
    *,
    db: Session,
    data: UserCreate,
) -> User:
    if user_repository.get_by_email(db, data.email) is not None:
        raise UserAlreadyExistsError("User with this email already exists")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )

    try:
        user_repository.add(db, user)
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as exc:
        db.rollback()
        raise AuthPersistenceError("Could not register user") from exc


def login_user(
    *,
    db: Session,
    email: str,
    password: str,
) -> Token:
    user = user_repository.get_by_email(db, email)

    if user is None or not verify_password(
        password,
        user.hashed_password,
    ):
        raise InvalidCredentialsError("Incorrect email or password")

    return Token(
        access_token=create_access_token(user.email)
    )
