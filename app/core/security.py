import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings

_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=_PBKDF2_ITERATIONS,
        salt=base64.urlsafe_b64encode(salt).decode("ascii"),
        digest=base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "iss", "aud", "exp", "iat"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise InvalidTokenError from exc
