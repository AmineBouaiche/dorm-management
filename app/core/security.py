import base64
import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import settings

_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 600_000
_ARGON2 = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=4, hash_len=32, salt_len=16)
# Used when an email does not exist so login still performs a real password-hash verification.
_DUMMY_PASSWORD_HASH = _ARGON2.hash("residence-dummy-password-for-timing-equalisation")


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _ARGON2.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    if encoded_hash.startswith("$argon2"):
        try:
            return _ARGON2.verify(encoded_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
    return _verify_legacy_pbkdf2(password, encoded_hash)


def password_needs_rehash(encoded_hash: str) -> bool:
    if not encoded_hash.startswith("$argon2"):
        return True
    try:
        return _ARGON2.check_needs_rehash(encoded_hash)
    except InvalidHashError:
        return True


def verify_dummy_password(password: str) -> None:
    try:
        _ARGON2.verify(_DUMMY_PASSWORD_HASH, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        pass


def _verify_legacy_pbkdf2(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(_PBKDF2_ALGORITHM, password.encode("utf-8"), salt, iterations)
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
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


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
