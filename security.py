import os
import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ENV = os.getenv("ENV", "development").lower()
INSECURE_SECRET_KEYS = {
    "",
    "change-me-to-a-long-random-string-in-production",
    "change-me-in-production",
    "changeme-use-a-long-random-secret-in-production",
}


def _get_secret_key() -> str:
    configured = os.getenv("SECRET_KEY", "")
    if configured not in INSECURE_SECRET_KEYS:
        return configured
    if ENV == "production":
        raise RuntimeError("SECRET_KEY must be set to a strong value when ENV=production")
    logger.warning("Using development SECRET_KEY; configure a strong value before production use")
    return "dev-insecure-secret-key"


SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
