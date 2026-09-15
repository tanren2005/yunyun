import logging
import smtplib
import ssl
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, code: str, subject: str = "【云云】注册验证码") -> bool:
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_pass:
        return False

    from_addr = settings.smtp_from or settings.smtp_user
    body = (
        f"【云云】您的验证码是：{code}\n\n"
        f"有效期 {settings.code_ttl_seconds // 60} 分钟，请勿泄露给他人。\n"
        f"如非本人操作，请忽略本邮件。"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context) as server:
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(from_addr, [to_email], msg.as_string())
        return True
    except Exception:
        logger.exception("发送邮件失败")
        return False
