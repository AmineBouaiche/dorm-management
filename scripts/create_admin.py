from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def main() -> None:
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password: ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters")

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            raise SystemExit("A user with that email already exists")
        db.add(User(email=email, password_hash=hash_password(password), role=UserRole.ADMIN))
        db.commit()
    print("Admin user created")


if __name__ == "__main__":
    main()
