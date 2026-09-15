import logging
import random
import string

from fastapi import HTTPException, status

from app.config import get_settings
from app.core.redis_client import get_redis
from app.services.mail import send_verification_email

logger = logging.getLogger(__name__)
settings = get_settings()


def _code_key(email: str, purpose: str = "register") -> str:
    return f"yunyun:code:{purpose}:{email.lower()}"


def _cooldown_key(email: str, purpose: str = "register") -> str:
    return f"yunyun:code_cd:{purpose}:{email.lower()}"


def generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def send_code(email: str, purpose: str = "register") -> str | None:
    r = get_redis()
    email = email.lower()
    if r.exists(_cooldown_key(email, purpose)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="发送过于频繁，请稍后再试")

    code = generate_code()
    r.setex(_code_key(email, purpose), settings.code_ttl_seconds, code)
    r.setex(_cooldown_key(email, purpose), settings.code_resend_interval_seconds, "1")

    subject_map = {
        "register": "【云云】注册验证码",
        "reset_password": "【云云】修改密码验证码",
    }
    subject = subject_map.get(purpose, "【云云】验证码")
    sent = send_verification_email(email, code, subject=subject)
    if not sent:
        logger.warning("SMTP 未配置或发送失败，开发验证码 purpose=%s [%s] => %s", purpose, email, code)
        return code
    return None


def verify_code(email: str, code: str, purpose: str = "register") -> None:
    r = get_redis()
    email = email.lower()
    stored = r.get(_code_key(email, purpose))
    if not stored or stored != code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")
    r.delete(_code_key(email, purpose))
