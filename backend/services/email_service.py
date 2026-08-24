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
import html as html_lib
import logging
import os
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_DEFAULT_FROM = "EleutherIA <no-reply@free-will.app>"
_DEFAULT_ACCOUNT_REQUEST_RECIPIENT = "romain-girardi@hotmail.fr"


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


def _account_request_recipient() -> str:
    """Mailbox used for human review of public account requests."""
    return os.getenv(
        "ACCOUNT_REQUEST_RECIPIENT", _DEFAULT_ACCOUNT_REQUEST_RECIPIENT
    ).strip()


def _account_request_copy(
    request_id: str,
    request_info: dict[str, Any],
) -> tuple[str, str, str]:
    """Build plain-text and escaped HTML notification bodies."""
    full_name = str(request_info["full_name"])
    email = str(request_info["email"])
    affiliation = str(request_info.get("affiliation") or "Not provided")
    role = str(request_info["role"])
    research_focus = str(request_info["research_focus"])
    intended_use = ", ".join(str(item) for item in request_info["intended_use"])
    locale = str(request_info.get("locale") or "unknown")
    submitted_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    subject = f"[EleutherIA] Account request — {full_name}"
    text = (
        "A new EleutherIA account request is ready for review.\n\n"
        f"Request ID: {request_id}\n"
        f"Submitted: {submitted_at}\n"
        f"Name: {full_name}\n"
        f"Email: {email}\n"
        f"Affiliation: {affiliation}\n"
        f"Role: {role}\n"
        f"Intended use: {intended_use}\n"
        f"Interface language: {locale}\n\n"
        "Research context:\n"
        f"{research_focus}\n\n"
        "Privacy notice acknowledged: yes\n"
        f"Privacy notice version: {request_info['privacy_notice_version']}\n\n"
        "Reply to this message to contact the applicant."
    )

    def escaped(value: str) -> str:
        return html_lib.escape(value).replace("\n", "<br>")

    html = (
        '<div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;'
        'color:#292524;line-height:1.55">'
        '<p style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;'
        'color:#9a3412">EleutherIA access desk</p>'
        '<h2 style="font-family:Georgia,serif;font-weight:600;margin-top:0">'
        "New account request</h2>"
        '<table role="presentation" style="width:100%;border-collapse:collapse;'
        'background:#fcf9f4;border:1px solid #f1e4d0">'
        f'<tr><td style="padding:9px 12px;color:#78716c">Request ID</td><td style="padding:9px 12px"><strong>{escaped(request_id)}</strong></td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Submitted</td><td style="padding:9px 12px">{escaped(submitted_at)}</td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Name</td><td style="padding:9px 12px">{escaped(full_name)}</td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Email</td><td style="padding:9px 12px"><a href="mailto:{escaped(email)}">{escaped(email)}</a></td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Affiliation</td><td style="padding:9px 12px">{escaped(affiliation)}</td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Role</td><td style="padding:9px 12px">{escaped(role)}</td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Use</td><td style="padding:9px 12px">{escaped(intended_use)}</td></tr>'
        f'<tr><td style="padding:9px 12px;color:#78716c">Language</td><td style="padding:9px 12px">{escaped(locale)}</td></tr>'
        "</table>"
        '<h3 style="font-family:Georgia,serif;font-weight:600">Research context</h3>'
        f'<p style="padding:16px;background:#f5f5f4;border-left:3px solid #c2410c">{escaped(research_focus)}</p>'
        '<p style="font-size:12px;color:#78716c">Privacy notice acknowledged · '
        f'version {escaped(str(request_info["privacy_notice_version"]))}</p>'
        '<p style="font-size:13px;color:#57534e">Reply to this message to contact the applicant.</p>'
        "</div>"
    )
    return subject, text, html


async def send_account_request_notification(
    request_id: str,
    request_info: dict[str, Any],
) -> bool:
    """Notify the account reviewer through the configured email provider."""
    recipient = _account_request_recipient()
    if not recipient:
        logger.error("ACCOUNT_REQUEST_RECIPIENT is empty")
        return False

    subject, text, html = _account_request_copy(request_id, request_info)
    reply_to = str(request_info["email"])

    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    _RESEND_ENDPOINT,
                    headers={"Authorization": f"Bearer {resend_key}"},
                    json={
                        "from": _from_address(),
                        "to": [recipient],
                        "reply_to": reply_to,
                        "subject": subject,
                        "text": text,
                        "html": html,
                    },
                )
            if resp.status_code < 300:
                return True
            logger.error(
                "Resend rejected account request notification: HTTP %s",
                resp.status_code,
            )
            return False
        except Exception:
            logger.exception("Resend account request delivery failed")
            return False

    if os.getenv("SMTP_HOST"):
        try:
            await asyncio.to_thread(
                _send_smtp,
                recipient,
                subject,
                text,
                html,
                reply_to,
            )
            return True
        except Exception:
            logger.exception("SMTP account request delivery failed")
            return False

    logger.warning(
        "No email provider configured (RESEND_API_KEY / SMTP_HOST). "
        "Account request %s from %s was not delivered.",
        request_id,
        reply_to,
    )
    return False


def _send_smtp(
    to_email: str,
    subject: str,
    text: str,
    html: str,
    reply_to: str | None = None,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _from_address()
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to
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
