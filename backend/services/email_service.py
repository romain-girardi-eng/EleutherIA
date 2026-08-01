"""
Transactional email — provider-agnostic sender for login codes.

Resolution order (first configured provider wins):
  1. Resend      — set RESEND_API_KEY (+ EMAIL_FROM)
  2. SMTP        — set SMTP_HOST (+ SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM)
  3. Dev fallback — no provider configured: the code is logged at WARNING so
                    local development still works. NEVER relied on in production.

No third-party infrastructure is assumed; everything is driven by env vars.
"""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

import httpx

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_DEFAULT_FROM = "EleutherIA <no-reply@free-will.app>"


def _from_address() -> str:
    return os.getenv("EMAIL_FROM", _DEFAULT_FROM)


def _subject() -> str:
    return "Votre code de connexion EleutherIA"


def _plain_body(code: str, ttl_minutes: int) -> str:
    # French copy;   = narrow no-break space before : and !
    return (
        f"Bonjour !\n\n"
        f"Voici votre code de connexion : {code}\n\n"
        f"Ce code est valable {ttl_minutes} minutes et ne peut servir qu'une fois.\n"
        f"Si vous n'avez pas demandé cette connexion, ignorez cet e-mail.\n\n"
        f"— EleutherIA · free-will.app\n"
    )


def _html_body(code: str, ttl_minutes: int) -> str:
    return (
        f'<div style="font-family:Georgia,serif;max-width:480px;margin:auto;'
        f'color:#292524">'
        f'<h2 style="font-weight:600">Code de connexion</h2>'
        f"<p>Voici votre code de connexion&#8239;:</p>"
        f'<p style="font-size:32px;font-weight:700;letter-spacing:8px;'
        f'font-family:monospace;color:#1c1917">{code}</p>'
        f'<p style="color:#57534e;font-size:14px">Valable {ttl_minutes} minutes, '
        f"à usage unique. Si vous n’avez pas demandé cette connexion, "
        f"ignorez cet e-mail.</p>"
        f'<p style="color:#a8a29e;font-size:12px">— EleutherIA · free-will.app</p>'
        f"</div>"
    )


async def send_login_code(to_email: str, code: str, ttl_minutes: int) -> bool:
    """Send a login code to ``to_email``. Returns True if a provider accepted it.

    Never raises — a delivery failure must not leak (via a 500) whether the
    address is registered. The caller returns a uniform response regardless.
    """
    subject = _subject()
    text = _plain_body(code, ttl_minutes)
    html = _html_body(code, ttl_minutes)

    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    _RESEND_ENDPOINT,
                    headers={"Authorization": f"Bearer {resend_key}"},
                    json={
                        "from": _from_address(),
                        "to": [to_email],
                        "subject": subject,
                        "text": text,
                        "html": html,
                    },
                )
            if resp.status_code < 300:
                return True
            logger.error("Resend rejected login code: HTTP %s", resp.status_code)
            return False
        except Exception:
            logger.exception("Resend delivery failed")
            return False

    if os.getenv("SMTP_HOST"):
        try:
            await asyncio.to_thread(_send_smtp, to_email, subject, text, html)
            return True
        except Exception:
            logger.exception("SMTP delivery failed")
            return False

    # Dev fallback — never in production. Surfaces the code to the operator.
    logger.warning(
        "No email provider configured (RESEND_API_KEY / SMTP_HOST). "
        "Login code for %s is: %s",
        to_email,
        code,
    )
    return False


def _send_smtp(to_email: str, subject: str, text: str, html: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _from_address()
    msg["To"] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
