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
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "booking@prenotika.com")
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


def _cancel_html(
    *,
    cliente_nome: str,
    docente_nome: str,
    studio_nome: str,
    starts_at: datetime,
    ends_at: datetime,
    location: str,
) -> str:
    when = f"{_fmt_local_human(starts_at)} – {ends_at.strftime('%H:%M')}"
    return f"""\
<!doctype html><html><body style="margin:0;padding:0;background:#F8FAFC;font-family:'Inter',Arial,sans-serif;color:#0F172A">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:24px 12px"><tr><td align="center">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:14px;overflow:hidden;border:1px solid #E2E8F0">
      <tr><td style="background:linear-gradient(135deg,#0F172A 0%,#475569 100%);padding:22px 28px">
        <div style="color:#fff;font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
        <div style="color:rgba(255,255,255,0.85);font-size:12px;text-transform:uppercase;letter-spacing:0.18em;margin-top:4px">{_html.escape(studio_nome)}</div>
      </td></tr>
      <tr><td style="padding:28px">
        <h1 style="margin:0 0 8px;font-family:'Sora',Arial,sans-serif;font-size:22px;font-weight:700;color:#B91C1C">Appuntamento annullato</h1>
        <p style="margin:0 0 18px;color:#475569;font-size:14px;line-height:1.5">Ciao <strong style="color:#0F172A">{_html.escape(cliente_nome)}</strong>, ti informiamo che l'appuntamento del <strong>{when}</strong> con <strong style="color:#0F172A">{_html.escape(docente_nome)}</strong> presso <strong>{_html.escape(location)}</strong> è stato <strong style="color:#B91C1C">annullato</strong>.</p>
        <p style="margin:18px 0 6px;color:#475569;font-size:13px;line-height:1.5">In allegato il file <strong>.ics</strong> di cancellazione: aprilo per rimuovere automaticamente l'evento dal tuo calendario.</p>
        <p style="margin:18px 0 0;color:#94A3B8;font-size:12px">Per riprenotare contatta {_html.escape(studio_nome)}.</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""


def build_ics_cancel(*, uid: str, starts_at: datetime, ends_at: datetime, summary: str, location: str, organizer_email: str, organizer_name: str, attendee_email: str, attendee_name: str) -> str:
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "PRODID:-//Prenotika//Booking//IT", "VERSION:2.0",
        "CALSCALE:GREGORIAN", "METHOD:CANCEL",
        "BEGIN:VEVENT",
        f"UID:{uid}", f"DTSTAMP:{dtstamp}",
        f"DTSTART:{_fmt_utc(starts_at)}", f"DTEND:{_fmt_utc(ends_at)}",
        f"SUMMARY:{_escape_ics(summary)}",
        f"LOCATION:{_escape_ics(location)}",
        f"ORGANIZER;CN={_escape_ics(organizer_name)}:mailto:{organizer_email}",
        f"ATTENDEE;CN={_escape_ics(attendee_name)}:mailto:{attendee_email}",
        "STATUS:CANCELLED", "SEQUENCE:1",
        "END:VEVENT", "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


async def send_cancellation_email(
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
    if not cliente_email:
        return None
    cliente_full = f"{cliente_nome} {cliente_cognome}".strip()
    docente_full = f"{docente_nome} {docente_cognome}".strip()
    starts = _to_local_dt(data_iso, dal)
    ends = _to_local_dt(data_iso, al)
    location = studio_sede or studio_nome
    uid = f"cancel-{uuid.uuid4()}@prenotika"
    ics = build_ics_cancel(
        uid=uid,
        starts_at=starts, ends_at=ends,
        summary=f"Appuntamento con {docente_full}",
        location=location,
        organizer_email=(studio_email or BREVO_SENDER_EMAIL),
        organizer_name=studio_nome,
        attendee_email=cliente_email,
        attendee_name=cliente_full,
    )
    html_body = _cancel_html(
        cliente_nome=cliente_full, docente_nome=docente_full, studio_nome=studio_nome,
        starts_at=starts, ends_at=ends, location=location,
    )
    subject = f"Appuntamento annullato — {_fmt_local_human(starts)}"
    return await _send_brevo(
        to_email=cliente_email, to_name=cliente_full, subject=subject,
        html_content=html_body, ics_content=ics, ics_filename=f"disdetta-{data_iso}.ics",
    )


def _reminder_html(*, cliente_nome: str, docente_nome: str, studio_nome: str, starts_at: datetime, ends_at: datetime, location: str) -> str:
    when = f"{_fmt_local_human(starts_at)} – {ends_at.strftime('%H:%M')}"
    return f"""\
<!doctype html><html><body style="margin:0;padding:0;background:#F8FAFC;font-family:'Inter',Arial,sans-serif;color:#0F172A">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:24px 12px"><tr><td align="center">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:14px;overflow:hidden;border:1px solid #E2E8F0">
      <tr><td style="background:linear-gradient(135deg,#F59E0B 0%,#7C3AED 60%,#2DD4BF 100%);padding:22px 28px">
        <div style="color:#fff;font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
        <div style="color:rgba(255,255,255,0.9);font-size:12px;text-transform:uppercase;letter-spacing:0.18em;margin-top:4px">Promemoria · {_html.escape(studio_nome)}</div>
      </td></tr>
      <tr><td style="padding:28px">
        <h1 style="margin:0 0 8px;font-family:'Sora',Arial,sans-serif;font-size:22px;font-weight:700;color:#0F172A">A domani!</h1>
        <p style="margin:0 0 18px;color:#475569;font-size:14px;line-height:1.5">Ciao <strong>{_html.escape(cliente_nome)}</strong>, ti ricordiamo l'appuntamento di domani <strong>{when}</strong> con <strong>{_html.escape(docente_nome)}</strong> presso <strong>{_html.escape(location)}</strong>.</p>
        <p style="margin:18px 0 0;color:#94A3B8;font-size:12px">Se non puoi più venire, ti chiediamo di avvisare al più presto.</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""


async def send_reminder_email(
    *,
    cliente_email: str,
    cliente_nome: str,
    cliente_cognome: str,
    docente_nome: str,
    docente_cognome: str,
    studio_nome: str,
    studio_sede: Optional[str],
    data_iso: str,
    dal: str,
    al: str,
) -> Optional[str]:
    if not cliente_email:
        return None
    cliente_full = f"{cliente_nome} {cliente_cognome}".strip()
    docente_full = f"{docente_nome} {docente_cognome}".strip()
    starts = _to_local_dt(data_iso, dal)
    ends = _to_local_dt(data_iso, al)
    location = studio_sede or studio_nome
    html_body = _reminder_html(
        cliente_nome=cliente_full, docente_nome=docente_full, studio_nome=studio_nome,
        starts_at=starts, ends_at=ends, location=location,
    )
    subject = f"Promemoria appuntamento — {_fmt_local_human(starts)}"
    return await _send_brevo(
        to_email=cliente_email, to_name=cliente_full,
        subject=subject, html_content=html_body,
    )

async def send_welcome_admin_email(
    *,
    to_email: str,
    to_name: str,
    studio_nome: str,
    login_email: str,
    temp_password: str,
    login_url: str,
    setup_url: str,
) -> Optional[str]:
    """Invia email di benvenuto all'admin di uno studio appena creato.
    Include credenziali temporanee e un magic link per impostare subito
    una nuova password (valido 7 giorni)."""
    subject = f"Benvenuto in Prenotika · {studio_nome}"
    safe_name = _html.escape(to_name or "")
    safe_studio = _html.escape(studio_nome or "")
    safe_email = _html.escape(login_email)
    safe_pwd = _html.escape(temp_password)
    html_body = f"""\
<!doctype html><html><body style="font-family:'Inter',Arial,sans-serif;color:#0F172A;background:#F8FAFC;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;box-shadow:0 8px 26px -8px rgba(15,23,42,0.08)">
    <div style="background:linear-gradient(135deg,#7C3AED 0%,#60A5FA 50%,#2DD4BF 100%);padding:26px 30px;color:#fff">
      <div style="font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
      <div style="font-size:11px;letter-spacing:0.22em;text-transform:uppercase;margin-top:4px;opacity:0.9">Smart Booking</div>
    </div>
    <div style="padding:30px;font-size:14px;line-height:1.65">
      <h1 style="font-family:'Sora',Arial,sans-serif;font-size:24px;font-weight:800;color:#0F172A;margin:0 0 12px;letter-spacing:-0.01em">Ciao {safe_name}, benvenuto! 👋</h1>
      <p style="margin:0 0 14px;color:#334155">Il tuo spazio Prenotika per <strong>{safe_studio}</strong> è stato attivato. Da qui potrai gestire agenda, professionisti, appuntamenti e report in modo veloce e ordinato.</p>

      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:18px 20px;margin:22px 0">
        <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#7C3AED;font-weight:700;margin-bottom:10px">Le tue credenziali</div>
        <table style="width:100%;font-size:14px;border-collapse:collapse">
          <tr><td style="padding:4px 0;color:#64748B;width:120px">Email login</td><td style="padding:4px 0;color:#0F172A;font-weight:600">{safe_email}</td></tr>
          <tr><td style="padding:4px 0;color:#64748B">Password iniziale</td><td style="padding:4px 0;color:#0F172A;font-family:'JetBrains Mono',Menlo,Consolas,monospace;font-weight:600;background:#F1F5F9;padding-left:8px;border-radius:6px;display:inline-block;padding:4px 10px">{safe_pwd}</td></tr>
        </table>
      </div>

      <p style="margin:0 0 8px;color:#334155">Ti consigliamo di <strong>impostare subito una tua password personale</strong> con il link sicuro qui sotto (valido 7 giorni):</p>
      <p style="text-align:center;margin:22px 0">
        <a href="{setup_url}" style="display:inline-block;padding:14px 30px;background:linear-gradient(135deg,#7C3AED 0%,#2DD4BF 100%);color:#fff;text-decoration:none;font-weight:700;border-radius:14px;font-size:14px;letter-spacing:0.01em;box-shadow:0 10px 22px -6px rgba(124,58,237,0.45)">Imposta la tua password</a>
      </p>

      <p style="margin:18px 0 6px;color:#64748B;font-size:12px">In alternativa, puoi accedere subito con le credenziali sopra da:</p>
      <p style="margin:0 0 22px;font-size:13px"><a href="{login_url}" style="color:#7C3AED;font-weight:600">{login_url}</a></p>

      <hr style="border:none;border-top:1px solid #E2E8F0;margin:22px 0" />
      <p style="margin:0;color:#64748B;font-size:12px;line-height:1.6">Per qualsiasi domanda scrivici a <a href="mailto:booking@prenotika.com" style="color:#7C3AED">booking@prenotika.com</a>. Siamo felici di averti a bordo. 🚀</p>
    </div>
    <div style="padding:16px 30px;background:#F8FAFC;font-size:11px;color:#94A3B8;text-align:center;border-top:1px solid #E2E8F0">Prenotika · La gestione intelligente degli appuntamenti · Eligesoft Srl · P.IVA 04532690650</div>
  </div>
</body></html>"""
    return await _send_brevo(
        to_email=to_email, to_name=to_name or to_email,
        subject=subject, html_content=html_body,
    )


async def send_password_reset_email(
    *,
    to_email: str,
    to_name: str,
    reset_url: str,
) -> Optional[str]:
    """Invia email di recupero password con magic link (valido 60 min)."""
    subject = "Reimposta la tua password Prenotika"
    safe_name = _html.escape(to_name or "")
    html_body = f"""\
<!doctype html><html><body style="font-family:'Inter',Arial,sans-serif;color:#0F172A;background:#F8FAFC;padding:24px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;box-shadow:0 6px 22px -6px rgba(15,23,42,0.06)">
    <div style="background:linear-gradient(135deg,#7C3AED 0%,#60A5FA 50%,#2DD4BF 100%);padding:22px 28px;color:#fff;font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
    <div style="padding:28px;font-size:14px;line-height:1.65">
      <h1 style="font-family:'Sora',Arial,sans-serif;font-size:22px;font-weight:800;color:#0F172A;margin:0 0 12px">Reimposta la tua password</h1>
      <p style="margin:0 0 14px;color:#334155">Ciao {safe_name},</p>
      <p style="margin:0 0 18px;color:#334155">abbiamo ricevuto una richiesta di reset password per il tuo account Prenotika. Clicca il bottone qui sotto per scegliere una nuova password. Il link è valido per <strong>60 minuti</strong>.</p>
      <p style="text-align:center;margin:26px 0">
        <a href="{reset_url}" style="display:inline-block;padding:14px 30px;background:linear-gradient(135deg,#7C3AED 0%,#2DD4BF 100%);color:#fff;text-decoration:none;font-weight:700;border-radius:14px;font-size:14px;letter-spacing:0.01em;box-shadow:0 10px 22px -6px rgba(124,58,237,0.45)">Reimposta la password</a>
      </p>
      <p style="margin:18px 0 8px;color:#64748B;font-size:12px">Se il bottone non funziona, copia e incolla questo link nel browser:</p>
      <p style="margin:0 0 22px;font-size:12px;word-break:break-all;color:#7C3AED">{reset_url}</p>
      <hr style="border:none;border-top:1px solid #E2E8F0;margin:22px 0" />
      <p style="margin:0;color:#64748B;font-size:12px;line-height:1.6">Se non hai richiesto tu il reset, ignora questa email: la tua password attuale resta invariata. Per qualsiasi problema, contatta <a href="mailto:booking@prenotika.com" style="color:#7C3AED">booking@prenotika.com</a>.</p>
    </div>
    <div style="padding:14px 28px;background:#F8FAFC;font-size:11px;color:#94A3B8;text-align:center;border-top:1px solid #E2E8F0">Prenotika · La gestione intelligente degli appuntamenti</div>
  </div>
</body></html>"""
    return await _send_brevo(
        to_email=to_email, to_name=to_name or to_email,
        subject=subject, html_content=html_body,
    )




async def send_otp_email(
    *,
    to_email: str,
    to_name: str,
    otp_code: str,
    expires_minutes: int = 10,
) -> Optional[str]:
    """Invia un codice OTP a 6 cifre via email per accesso passwordless."""
    subject = f"{otp_code} · Il tuo codice di accesso Prenotika"
    safe_name = _html.escape(to_name or "")
    # Rendering del codice a 6 cifre con celle separate
    digits = "".join(
        f'<span style="display:inline-block;width:44px;height:56px;line-height:56px;margin:0 4px;background:#F1F5F9;border:1px solid #E2E8F0;border-radius:10px;font-family:\'JetBrains Mono\',Menlo,Consolas,monospace;font-size:26px;font-weight:800;color:#0F172A;letter-spacing:0">{d}</span>'
        for d in otp_code
    )
    html_body = f"""\
<!doctype html><html><body style="font-family:'Inter',Arial,sans-serif;color:#0F172A;background:#F8FAFC;padding:24px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;box-shadow:0 6px 22px -6px rgba(15,23,42,0.06)">
    <div style="background:linear-gradient(135deg,#7C3AED 0%,#60A5FA 50%,#2DD4BF 100%);padding:22px 28px;color:#fff;font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
    <div style="padding:28px;font-size:14px;line-height:1.65">
      <h1 style="font-family:'Sora',Arial,sans-serif;font-size:22px;font-weight:800;color:#0F172A;margin:0 0 12px">Il tuo codice di accesso</h1>
      <p style="margin:0 0 8px;color:#334155">Ciao {safe_name},</p>
      <p style="margin:0 0 18px;color:#334155">usa questo codice per accedere al tuo account Prenotika. Il codice è valido per <strong>{expires_minutes} minuti</strong>.</p>
      <div style="text-align:center;margin:22px 0;padding:20px;background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:12px">
        {digits}
      </div>
      <p style="margin:8px 0 4px;color:#64748B;font-size:12px;text-align:center">Non condividere questo codice con nessuno. Il nostro team non te lo chiederà mai.</p>
      <hr style="border:none;border-top:1px solid #E2E8F0;margin:22px 0" />
      <p style="margin:0;color:#64748B;font-size:12px;line-height:1.6">Se non hai richiesto tu il codice, ignora questa email. Per qualsiasi problema scrivi a <a href="mailto:booking@prenotika.com" style="color:#7C3AED">booking@prenotika.com</a>.</p>
    </div>
    <div style="padding:14px 28px;background:#F8FAFC;font-size:11px;color:#94A3B8;text-align:center;border-top:1px solid #E2E8F0">Prenotika · La gestione intelligente degli appuntamenti</div>
  </div>
</body></html>"""
    return await _send_brevo(
        to_email=to_email, to_name=to_name or to_email,
        subject=subject, html_content=html_body,
    )


async def send_onboarding_start_email(
    *,
    to_email: str,
    to_name: str,
    studio_nome: str,
    setup_url: str,
    otp_code: str,
) -> Optional[str]:
    """Email inviata subito dopo la creazione automatica dello studio (onboarding).
    Include: link diretto di setup + codice OTP a 6 cifre come fallback."""
    subject = f"Benvenuto in Prenotika · {studio_nome} è attivo 🎉"
    safe_name = _html.escape(to_name or "")
    safe_studio = _html.escape(studio_nome or "")
    digits = "".join(
        f'<span style="display:inline-block;width:36px;height:46px;line-height:46px;margin:0 3px;background:#F1F5F9;border:1px solid #E2E8F0;border-radius:8px;font-family:\'JetBrains Mono\',Menlo,Consolas,monospace;font-size:22px;font-weight:800;color:#0F172A">{d}</span>'
        for d in otp_code
    )
    html_body = f"""\
<!doctype html><html><body style="font-family:'Inter',Arial,sans-serif;color:#0F172A;background:#F8FAFC;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;box-shadow:0 8px 26px -8px rgba(15,23,42,0.08)">
    <div style="background:linear-gradient(135deg,#7C3AED 0%,#60A5FA 50%,#2DD4BF 100%);padding:26px 30px;color:#fff">
      <div style="font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.02em">Prenotika</div>
      <div style="font-size:11px;letter-spacing:0.22em;text-transform:uppercase;margin-top:4px;opacity:0.9">Smart Booking</div>
    </div>
    <div style="padding:30px;font-size:14px;line-height:1.65">
      <h1 style="font-family:'Sora',Arial,sans-serif;font-size:24px;font-weight:800;color:#0F172A;margin:0 0 12px">Ciao {safe_name}, il tuo spazio è pronto! 🚀</h1>
      <p style="margin:0 0 14px;color:#334155">Abbiamo attivato <strong>{safe_studio}</strong>. Completa la configurazione iniziale (tipologia, orari, logo) in meno di 2 minuti.</p>
      <p style="text-align:center;margin:22px 0">
        <a href="{setup_url}" style="display:inline-block;padding:14px 30px;background:linear-gradient(135deg,#7C3AED 0%,#2DD4BF 100%);color:#fff;text-decoration:none;font-weight:700;border-radius:14px;font-size:14px;letter-spacing:0.01em;box-shadow:0 10px 22px -6px rgba(124,58,237,0.45)">Configura il tuo studio</a>
      </p>
      <p style="margin:18px 0 6px;color:#64748B;font-size:12px">Se il pulsante non funziona, copia questo link:</p>
      <p style="margin:0 0 22px;font-size:12px;word-break:break-all;color:#7C3AED">{setup_url}</p>

      <hr style="border:none;border-top:1px solid #E2E8F0;margin:22px 0" />
      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px 18px;margin:6px 0">
        <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#7C3AED;font-weight:700;margin-bottom:10px">Accesso rapido con codice</div>
        <p style="margin:0 0 10px;color:#334155;font-size:13px">In alternativa, accedi in qualsiasi momento inserendo la tua email e questo codice OTP (valido 10 min):</p>
        <div style="text-align:center;margin:12px 0">{digits}</div>
      </div>
      <p style="margin:18px 0 0;color:#64748B;font-size:12px;line-height:1.6">Nessuna password iniziale richiesta. Potrai impostarla in seguito dalla sezione Account.</p>
    </div>
    <div style="padding:16px 30px;background:#F8FAFC;font-size:11px;color:#94A3B8;text-align:center;border-top:1px solid #E2E8F0">Prenotika · Eligesoft Srl · P.IVA 04532690650</div>
  </div>
</body></html>"""
    return await _send_brevo(
        to_email=to_email, to_name=to_name or to_email,
        subject=subject, html_content=html_body,
    )


async def send_lead_notification(
    *,
    lead: dict,
    notify_to: str = "booking@prenotika.com",
) -> Optional[str]:
    """Notifica al team di un nuovo lead/contatto dalla landing."""
    nome = _html.escape(lead.get("nome", ""))
    email = _html.escape(lead.get("email", ""))
    telefono = _html.escape(lead.get("telefono") or "—")
    tipologia = _html.escape(lead.get("tipologia") or "—")
    studio = _html.escape(lead.get("studio") or "—")
    piano = _html.escape(lead.get("piano_interesse") or "—")
    messaggio = _html.escape(lead.get("messaggio") or "—").replace("\n", "<br/>")
    subject = f"[Prenotika] Nuovo lead da {nome}"
    html_body = f"""\
<!doctype html><html><body style="font-family:'Inter',Arial,sans-serif;color:#0F172A;background:#F8FAFC;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden">
    <div style="background:linear-gradient(135deg,#7C3AED 0%,#60A5FA 50%,#2DD4BF 100%);padding:20px 26px;color:#fff;font-family:'Sora',Arial,sans-serif;font-weight:800;font-size:20px;letter-spacing:-0.02em">Prenotika · Nuovo lead</div>
    <div style="padding:24px 26px;font-size:14px;line-height:1.6">
      <p style="margin:0 0 14px;color:#475569">Hai ricevuto una nuova richiesta dalla landing page.</p>
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="color:#475569;padding:6px 0;width:32%">Nome</td><td style="font-weight:600">{nome}</td></tr>
        <tr><td style="color:#475569;padding:6px 0">Email</td><td><a href="mailto:{email}" style="color:#7C3AED">{email}</a></td></tr>
        <tr><td style="color:#475569;padding:6px 0">Telefono</td><td>{telefono}</td></tr>
        <tr><td style="color:#475569;padding:6px 0">Tipologia</td><td>{tipologia}</td></tr>
        <tr><td style="color:#475569;padding:6px 0">Studio</td><td>{studio}</td></tr>
        <tr><td style="color:#475569;padding:6px 0">Piano interesse</td><td style="font-weight:600;color:#7C3AED">{piano}</td></tr>
        <tr><td style="color:#475569;padding:6px 0;vertical-align:top">Messaggio</td><td>{messaggio}</td></tr>
      </table>
    </div>
  </div>
</body></html>"""
    return await _send_brevo(
        to_email=notify_to, to_name="Prenotika Team",
        subject=subject, html_content=html_body,
    )
