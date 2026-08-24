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
from email.utils import formatdate, make_msgid, parseaddr
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_DEFAULT_FROM = "EleutherIA <no-reply@free-will.app>"
_DEFAULT_ACCOUNT_REQUEST_RECIPIENT = "romain-girardi@hotmail.fr"
_BRAND_ORIGIN = "https://free-will.app"
_BRAND_LOGO_URL = f"{_BRAND_ORIGIN}/apple-touch-icon.png"

_ROLE_LABELS = {
    "doctoral_researcher": "Doctorant·e",
    "researcher": "Chercheur·se ou universitaire",
    "student": "Étudiant·e",
    "teacher": "Enseignant·e",
    "independent_scholar": "Chercheur·se indépendant·e",
    "other": "Autre",
}

_USE_LABELS = {
    "research": "Recherche universitaire",
    "teaching": "Enseignement",
    "writing": "Rédaction ou publication",
    "data_exploration": "Exploration du corpus ou du graphe",
    "other": "Autre usage scientifique",
}


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
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "User-Agent": "EleutherIA/2.0",
                    },
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
    role_key = str(request_info["role"])
    role = _ROLE_LABELS.get(role_key, role_key)
    research_focus = str(request_info["research_focus"])
    intended_use = ", ".join(
        _USE_LABELS.get(str(item), str(item)) for item in request_info["intended_use"]
    )
    locale = str(request_info.get("locale") or "unknown")
    submitted_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    subject = f"EleutherIA · Nouvelle demande de compte · {full_name}"
    text = (
        "ELEUTHERIA — NOUVELLE DEMANDE DE COMPTE\n\n"
        "Une nouvelle demande d’accès attend votre examen.\n\n"
        f"Référence : {request_id}\n"
        f"Reçue le : {submitted_at}\n"
        f"Nom : {full_name}\n"
        f"E-mail : {email}\n"
        f"Affiliation: {affiliation}\n"
        f"Situation : {role}\n"
        f"Usage prévu : {intended_use}\n"
        f"Langue de l’interface : {locale}\n\n"
        "CONTEXTE DE RECHERCHE\n"
        f"{research_focus}\n\n"
        "INFORMATIONS DE CONFIDENTIALITÉ\n"
        "Notice lue par la personne : oui\n"
        f"Version de la notice : {request_info['privacy_notice_version']}\n\n"
        f"Pour répondre, écrivez à {email} ou répondez directement à cet e-mail.\n\n"
        "— EleutherIA · free-will.app\n"
        "Message transactionnel généré après l’envoi du formulaire d’accès."
    )

    def escaped(value: str) -> str:
        return html_lib.escape(value).replace("\n", "<br>")

    mailto_email = quote(email, safe="@.+-_")
    reply_subject = quote(f"EleutherIA — votre demande {request_id}")
    reply_href = f"mailto:{mailto_email}?subject={reply_subject}"
    privacy_version = escaped(str(request_info["privacy_notice_version"]))

    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light only">
  <meta name="supported-color-schemes" content="light only">
  <title>{escaped(subject)}</title>
  <style>
    @media only screen and (max-width: 640px) {{
      .email-shell {{ width: 100% !important; }}
      .email-pad {{ padding-left: 22px !important; padding-right: 22px !important; }}
      .detail-label, .detail-value {{ display: block !important; width: 100% !important; }}
      .detail-label {{ padding-bottom: 2px !important; }}
      .detail-value {{ padding-top: 0 !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#f2ece2;color:#292524;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    Nouvelle demande d’accès de {escaped(full_name)} · référence {escaped(request_id)}
  </div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#f2ece2;border-collapse:collapse;">
    <tr>
      <td align="center" style="padding:32px 12px;">
        <table role="presentation" width="640" cellspacing="0" cellpadding="0" border="0" class="email-shell" style="width:640px;max-width:640px;background:#fcf9f4;border-collapse:collapse;border:1px solid #e4d7c4;">
          <tr>
            <td class="email-pad" style="padding:26px 42px;background:#17343d;border-bottom:4px solid #c65d32;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;">
                <tr>
                  <td width="62" valign="middle" style="width:62px;">
                    <img src="{_BRAND_LOGO_URL}" width="52" height="52" alt="EleutherIA" style="display:block;width:52px;height:52px;border:0;background:#fcf9f4;border-radius:2px;">
                  </td>
                  <td valign="middle" style="padding-left:14px;">
                    <div style="font-family:Georgia,'Times New Roman',serif;font-size:25px;line-height:30px;color:#fcf9f4;letter-spacing:.2px;">EleutherIA</div>
                    <div style="font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:10px;line-height:16px;color:#d9cdbb;letter-spacing:1.8px;text-transform:uppercase;">Bureau des accès</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="padding:38px 42px 18px;">
              <div style="font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:11px;line-height:16px;font-weight:bold;color:#9a3412;letter-spacing:1.7px;text-transform:uppercase;">Nouvelle demande</div>
              <h1 style="margin:8px 0 12px;font-family:Georgia,'Times New Roman',serif;font-size:34px;line-height:40px;font-weight:normal;color:#1c1917;">Une personne souhaite rejoindre EleutherIA.</h1>
              <p style="margin:0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:15px;line-height:24px;color:#62584c;">La demande est prête pour un examen humain. Répondez directement à ce message pour contacter la personne.</p>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="padding:10px 42px 26px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;background:#f6efe4;border-top:1px solid #dfd0bb;border-bottom:1px solid #dfd0bb;">
                <tr>
                  <td style="padding:16px 18px;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:11px;line-height:16px;color:#8a725b;letter-spacing:1px;text-transform:uppercase;">Référence</td>
                  <td align="right" style="padding:16px 18px;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;font-weight:bold;color:#4a3829;">{escaped(request_id)}</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="padding:0 42px 28px;">
              <h2 style="margin:0 0 10px;font-family:Georgia,'Times New Roman',serif;font-size:22px;line-height:28px;font-weight:normal;color:#1c1917;">La personne</h2>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;">
                <tr style="border-top:1px solid #eadfce;">
                  <td width="34%" class="detail-label" style="width:34%;padding:12px 6px 12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:12px;line-height:19px;color:#8a725b;">Nom</td>
                  <td class="detail-value" style="padding:12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:14px;line-height:21px;font-weight:bold;color:#2f2923;">{escaped(full_name)}</td>
                </tr>
                <tr style="border-top:1px solid #eadfce;">
                  <td width="34%" class="detail-label" style="width:34%;padding:12px 6px 12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:12px;line-height:19px;color:#8a725b;">Adresse e-mail</td>
                  <td class="detail-value" style="padding:12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:14px;line-height:21px;color:#2f2923;"><a href="mailto:{mailto_email}" style="color:#9a3412;text-decoration:underline;">{escaped(email)}</a></td>
                </tr>
                <tr style="border-top:1px solid #eadfce;">
                  <td width="34%" class="detail-label" style="width:34%;padding:12px 6px 12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:12px;line-height:19px;color:#8a725b;">Affiliation</td>
                  <td class="detail-value" style="padding:12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:14px;line-height:21px;color:#2f2923;">{escaped(affiliation)}</td>
                </tr>
                <tr style="border-top:1px solid #eadfce;">
                  <td width="34%" class="detail-label" style="width:34%;padding:12px 6px 12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:12px;line-height:19px;color:#8a725b;">Situation</td>
                  <td class="detail-value" style="padding:12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:14px;line-height:21px;color:#2f2923;">{escaped(role)}</td>
                </tr>
                <tr style="border-top:1px solid #eadfce;border-bottom:1px solid #eadfce;">
                  <td width="34%" class="detail-label" style="width:34%;padding:12px 6px 12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:12px;line-height:19px;color:#8a725b;">Usage prévu</td>
                  <td class="detail-value" style="padding:12px 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:14px;line-height:21px;color:#2f2923;">{escaped(intended_use)}</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="padding:0 42px 30px;">
              <h2 style="margin:0 0 10px;font-family:Georgia,'Times New Roman',serif;font-size:22px;line-height:28px;font-weight:normal;color:#1c1917;">Contexte de recherche</h2>
              <div style="padding:20px 22px;background:#efe5d6;border-left:4px solid #c65d32;font-family:Georgia,'Times New Roman',serif;font-size:17px;line-height:27px;color:#3e352d;">{escaped(research_focus)}</div>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="padding:0 42px 34px;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;">
                <tr>
                  <td style="background:#9a3412;">
                    <a href="{reply_href}" style="display:inline-block;padding:13px 20px;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:14px;line-height:18px;font-weight:bold;color:#fcf9f4;text-decoration:none;">Répondre à la demande&nbsp;→</a>
                  </td>
                </tr>
              </table>
              <p style="margin:14px 0 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:12px;line-height:19px;color:#8a725b;">Reçue le {escaped(submitted_at)} · interface {escaped(locale)}</p>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="padding:20px 42px;background:#f6efe4;border-top:1px solid #dfd0bb;">
              <p style="margin:0 0 5px;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:11px;line-height:17px;color:#7b6958;">Notice de confidentialité lue · version {privacy_version}</p>
              <p style="margin:0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:11px;line-height:17px;color:#9a8876;">Message transactionnel généré après l’envoi du formulaire d’accès sur <span style="color:#6f5b49;">free-will.app</span>. Aucun suivi marketing.</p>
            </td>
          </tr>
        </table>
        <p style="margin:14px 0 0;font-family:'Trebuchet MS',Helvetica,Arial,sans-serif;font-size:10px;line-height:16px;color:#9a8876;">EleutherIA · Ancient Free Will Database</p>
      </td>
    </tr>
  </table>
</body>
</html>"""
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
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Idempotency-Key": f"account-request/{request_id}",
                        "User-Agent": "EleutherIA/2.0",
                    },
                    json={
                        "from": _from_address(),
                        "to": [recipient],
                        "reply_to": reply_to,
                        "subject": subject,
                        "text": text,
                        "html": html,
                        "headers": {
                            "Auto-Submitted": "auto-generated",
                            "X-Auto-Response-Suppress": "All",
                            "X-Entity-Ref-ID": request_id,
                        },
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
                request_id,
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
    transaction_id: str | None = None,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _from_address()
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=False)
    _, sender_email = parseaddr(_from_address())
    sender_domain = sender_email.rsplit("@", 1)[-1] if "@" in sender_email else None
    msg["Message-ID"] = make_msgid(domain=sender_domain)
    msg["Auto-Submitted"] = "auto-generated"
    msg["X-Auto-Response-Suppress"] = "All"
    if reply_to:
        msg["Reply-To"] = reply_to
    if transaction_id:
        msg["X-Entity-Ref-ID"] = transaction_id
        msg["Resend-Idempotency-Key"] = f"account-request/{transaction_id}"
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
