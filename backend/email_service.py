"""
Email service Prenotika - Brevo Transactional API + ICS calendar attachment.
Invio non bloccante: i fallimenti vengono loggati ma non interrompono il flusso.
"""
from __future__ import annotations
import base64
import html as _html
import logging
import os
import uuid
from datetime import datetime, date, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger("eligehub.email")

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "team@zioners.com")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Prenotika")
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Europe/Rome")
BREVO_URL = "https://api.brevo.com/v3/smtp/email"

_TZ = ZoneInfo(APP_TIMEZONE)


def _escape_ics(value: str) -> str:
    return (
        (value or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def _to_local_dt(data_iso: str, ora_hhmm: str) -> datetime:
    """Combina data 'YYYY-MM-DD' + ora 'HH:MM' in datetime timezone Europe/Rome."""
    d = date.fromisoformat(data_iso)
    h, m = [int(x) for x in ora_hhmm.split(":")]
    return datetime.combine(d, time(h, m), tzinfo=_TZ)


def _fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt_local_human(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M")


def build_ics(
    *,
    uid: str,
    starts_at: datetime,
    ends_at: datetime,
    summary: str,
    description: str,
    location: str,
    organizer_email: str,
    organizer_name: str,
    attendee_email: str,
    attendee_name: str,
) -> str:
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//Prenotika//Booking//IT",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{_fmt_utc(starts_at)}",
        f"DTEND:{_fmt_utc(ends_at)}",
        f"SUMMARY:{_escape_ics(summary)}",
        f"DESCRIPTION:{_escape_ics(description)}",
        f"LOCATION:{_escape_ics(location)}",
        f"ORGANIZER;CN={_escape_ics(organizer_name)}:mailto:{organizer_email}",
        f"ATTENDEE;CN={_escape_ics(attendee_name)};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{attendee_email}",
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def _html_body(
    *,
    cliente_nome: str,
    docente_nome: str,
    studio_nome: str,
    starts_at: datetime,
    ends_at: datetime,
    location: str,
    materia: Optional[str],
    note: Optional[str],
    is_multiple: bool,
    altre_date: Optional[list[tuple[datetime, datetime]]] = None,
) -> str:
    when = f"{_fmt_local_human(starts_at)} – {ends_at.strftime('%H:%M')}"
    altri_html = ""
    if altre_date:
        items = "".join(
            f"<li>{_fmt_local_human(s)} – {e.strftime('%H:%M')}</li>"
            for s, e in altre_date
        )
        altri_html = f'<p style="margin:14px 0 6px;font-weight:600">Date successive:</p><ul style="margin:0 0 12px 18px;padding:0">{items}</ul>'

    materia_html = (
        f'<tr><td style="padding:6px 0;color:#475569">Argomento</td><td style="padding:6px 0;font-weight:600">{_html.escape(materia)}</td></tr>'
        if materia else ""
    )
    note_html = (
        f'<tr><td style="padding:6px 0;color:#475569">Note</td><td style="padding:6px 0">{_html.escape(note)}</td></tr>'
        if note else ""
    )

    titolo = "Conferma appuntamento" if not is_multiple else "Conferma appuntamenti ricorrenti"
    return f"""\
<!doctype html>
<html><body style="margin:0;padding:0;background:#F8FAFC;font-family:'Inter',Arial,sans-serif;color:#0F172A">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:24px 12px">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:14px;overflow:hidden;border:1px solid #E2E8F0">
        <tr><td style="background:linear-gradient(135deg,#7C3AED 0%,#60A5FA 50%,#2DD4BF 100%);padding:22px 28px">
          <div style="color:#fff;font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
          <div style="color:rgba(255,255,255,0.85);font-size:12px;text-transform:uppercase;letter-spacing:0.18em;margin-top:4px">{_html.escape(studio_nome)}</div>
        </td></tr>
        <tr><td style="padding:28px">
          <h1 style="margin:0 0 8px;font-family:'Sora',Arial,sans-serif;font-size:22px;font-weight:700;letter-spacing:-0.02em">{titolo}</h1>
          <p style="margin:0 0 18px;color:#475569;font-size:14px;line-height:1.5">Ciao <strong style="color:#0F172A">{_html.escape(cliente_nome)}</strong>, ti confermiamo {'gli appuntamenti' if is_multiple else "l'appuntamento"} con <strong style="color:#0F172A">{_html.escape(docente_nome)}</strong>.</p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 18px;font-size:14px;margin-bottom:14px">
            <tr><td style="padding:6px 0;color:#475569;width:36%">Quando</td><td style="padding:6px 0;font-weight:600">{when}</td></tr>
            <tr><td style="padding:6px 0;color:#475569">Dove</td><td style="padding:6px 0">{_html.escape(location)}</td></tr>
            {materia_html}
            {note_html}
          </table>
          {altri_html}
          <p style="margin:18px 0 6px;color:#475569;font-size:13px;line-height:1.5">In allegato trovi un file <strong>.ics</strong> per aggiungere l'appuntamento al tuo calendario (Google, Apple, Outlook).</p>
          <p style="margin:18px 0 0;color:#94A3B8;font-size:12px">Per disdire o modificare, contatta {_html.escape(studio_nome)}.</p>
        </td></tr>
        <tr><td style="padding:14px 28px;background:#F8FAFC;border-top:1px solid #E2E8F0;color:#94A3B8;font-size:11px;text-align:center">
          Email automatica inviata da Prenotika — La gestione intelligente degli appuntamenti
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


async def _send_brevo(
    *,
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    ics_content: Optional[str] = None,
    ics_filename: str = "appuntamento.ics",
) -> Optional[str]:
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY non configurata — invio email skipped")
        return None
    payload: dict = {
        "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if ics_content:
        payload["attachment"] = [{
            "name": ics_filename,
            "content": base64.b64encode(ics_content.encode("utf-8")).decode("utf-8"),
        }]
    try:
        async with httpx.AsyncClient(timeout=15.0) as cli:
            r = await cli.post(
                BREVO_URL,
                headers={
                    "api-key": BREVO_API_KEY,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json=payload,
            )
        if r.status_code >= 400:
            logger.warning(f"Brevo email FAILED {r.status_code}: {r.text[:300]}")
            return None
        try:
            return r.json().get("messageId")
        except Exception:
            return None
    except Exception as e:
        logger.warning(f"Brevo email exception: {e}")
        return None


async def send_appointment_email(
    *,
    cliente_email: str,
    cliente_nome: str,
    cliente_cognome: str,
    docente_nome: str,
    docente_cognome: str,
    studio_nome: str,
    studio_sede: Optional[str],
    studio_email: Optional[str],
    data_iso: str,
    dal: str,
    al: str,
    materia: Optional[str] = None,
    note: Optional[str] = None,
) -> Optional[str]:
    """Invia conferma per un singolo appuntamento. Returns brevo messageId o None."""
    if not cliente_email:
        return None
    cliente_full = f"{cliente_nome} {cliente_cognome}".strip()
    docente_full = f"{docente_nome} {docente_cognome}".strip()
    starts = _to_local_dt(data_iso, dal)
    ends = _to_local_dt(data_iso, al)
    location = studio_sede or studio_nome

    uid = f"{uuid.uuid4()}@prenotika"
    ics = build_ics(
        uid=uid,
        starts_at=starts,
        ends_at=ends,
        summary=f"Appuntamento con {docente_full}",
        description=f"Studio: {studio_nome}\n{('Argomento: ' + materia) if materia else ''}\n{('Note: ' + note) if note else ''}".strip(),
        location=location,
        organizer_email=(studio_email or BREVO_SENDER_EMAIL),
        organizer_name=studio_nome,
        attendee_email=cliente_email,
        attendee_name=cliente_full,
    )
    html_body = _html_body(
        cliente_nome=cliente_full,
        docente_nome=docente_full,
        studio_nome=studio_nome,
        starts_at=starts,
        ends_at=ends,
        location=location,
        materia=materia,
        note=note,
        is_multiple=False,
    )
    subject = f"Conferma appuntamento — {_fmt_local_human(starts)}"
    return await _send_brevo(
        to_email=cliente_email,
        to_name=cliente_full,
        subject=subject,
        html_content=html_body,
        ics_content=ics,
        ics_filename=f"appuntamento-{data_iso}.ics",
    )


async def send_bulk_appointments_email(
    *,
    cliente_email: str,
    cliente_nome: str,
    cliente_cognome: str,
    docente_nome: str,
    docente_cognome: str,
    studio_nome: str,
    studio_sede: Optional[str],
    studio_email: Optional[str],
    slots: list[dict],   # each {data, dal, al}
    materia: Optional[str] = None,
    note: Optional[str] = None,
) -> Optional[str]:
    """Invia conferma con allegato multi-evento per ricorrenze. Returns brevo messageId."""
    if not cliente_email or not slots:
        return None
    cliente_full = f"{cliente_nome} {cliente_cognome}".strip()
    docente_full = f"{docente_nome} {docente_cognome}".strip()
    location = studio_sede or studio_nome

    # Costruisce un unico VCALENDAR con N VEVENT
    organizer_email = studio_email or BREVO_SENDER_EMAIL
    head = [
        "BEGIN:VCALENDAR",
        "PRODID:-//Prenotika//Booking//IT",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
    ]
    events: list[str] = []
    dt_pairs: list[tuple[datetime, datetime]] = []
    for s in slots:
        starts = _to_local_dt(s["data"], s["dal"])
        ends = _to_local_dt(s["data"], s["al"])
        dt_pairs.append((starts, ends))
        uid = f"{uuid.uuid4()}@prenotika"
        dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        desc_parts = []
        if materia:
            desc_parts.append(f"Argomento: {materia}")
        if note:
            desc_parts.append(f"Note: {note}")
        desc_text = "\n".join(desc_parts)
        events.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{_fmt_utc(starts)}",
            f"DTEND:{_fmt_utc(ends)}",
            f"SUMMARY:{_escape_ics(f'Appuntamento con {docente_full}')}",
            f"DESCRIPTION:{_escape_ics(desc_text)}",
            f"LOCATION:{_escape_ics(location)}",
            f"ORGANIZER;CN={_escape_ics(studio_nome)}:mailto:{organizer_email}",
            f"ATTENDEE;CN={_escape_ics(cliente_full)};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{cliente_email}",
            "STATUS:CONFIRMED",
            "SEQUENCE:0",
            "END:VEVENT",
        ])
    ics = "\r\n".join(head + events + ["END:VCALENDAR"]) + "\r\n"

    dt_pairs.sort()
    first_s, first_e = dt_pairs[0]
    altre = dt_pairs[1:]
    html_body = _html_body(
        cliente_nome=cliente_full,
        docente_nome=docente_full,
        studio_nome=studio_nome,
        starts_at=first_s,
        ends_at=first_e,
        location=location,
        materia=materia,
        note=note,
        is_multiple=True,
        altre_date=altre,
    )
    subject = f"Conferma {len(slots)} appuntamenti con {docente_full}"
    return await _send_brevo(
        to_email=cliente_email,
        to_name=cliente_full,
        subject=subject,
        html_content=html_body,
        ics_content=ics,
        ics_filename=f"appuntamenti-{first_s.strftime('%Y-%m-%d')}.ics",
    )
