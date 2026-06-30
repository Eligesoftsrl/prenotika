"""
Scheduler reminder 24h prima dell'appuntamento.
Gira ogni ora; recupera tutti gli appuntamenti pianificati tra +23h e +25h
da adesso (Europe/Rome) che NON hanno reminded_at, invia email con Brevo
e marca reminded_at = now_utc.
"""
from __future__ import annotations
import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from email_service import send_reminder_email

logger = logging.getLogger("eligehub.reminder")
APP_TZ = ZoneInfo(os.environ.get("APP_TIMEZONE", "Europe/Rome"))


async def _send_reminders_24h(db):
    """Trova appuntamenti in arrivo tra 23h e 25h e invia il promemoria."""
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(APP_TZ)
    target_min = now_local + timedelta(hours=23)
    target_max = now_local + timedelta(hours=25)
    # Tutti gli appuntamenti confermati in 2 giorni di range (poi filtriamo per ora)
    date_min = target_min.date().isoformat()
    date_max = target_max.date().isoformat()
    q = {
        "stato": "confermato",
        "data": {"$gte": date_min, "$lte": date_max},
        "reminded_at": {"$exists": False},
    }
    cursor = db.appuntamenti.find(q)
    apps = await cursor.to_list(1000)
    sent = 0
    for app in apps:
        try:
            d = app["data"]
            t = app["dal"]
            ay, am, ad = [int(x) for x in d.split("-")]
            ah, am2 = [int(x) for x in t.split(":")]
            local_dt = datetime(ay, am, ad, ah, am2, tzinfo=APP_TZ)
            if not (target_min <= local_dt <= target_max):
                continue
            cliente = await db.clienti.find_one({"_id": app["cliente_id"]})
            if not cliente or not cliente.get("email"):
                continue
            docente = await db.users.find_one({"_id": app["docente_id"]})
            studio_doc = await db.studios.find_one({"_id": app["studio_id"]})
            msg_id = await send_reminder_email(
                cliente_email=cliente["email"],
                cliente_nome=cliente.get("nome", ""),
                cliente_cognome=cliente.get("cognome", ""),
                docente_nome=(docente or {}).get("nome", ""),
                docente_cognome=(docente or {}).get("cognome", ""),
                studio_nome=(studio_doc or {}).get("nome", "Prenotika"),
                studio_sede=(studio_doc or {}).get("sede"),
                data_iso=d,
                dal=t,
                al=app["al"],
            )
            await db.appuntamenti.update_one(
                {"_id": app["_id"]},
                {"$set": {"reminded_at": now_utc.isoformat()}},
            )
            if msg_id:
                sent += 1
        except Exception as e:
            logger.warning(f"Reminder fail for appuntamento {app.get('_id')}: {e}")
    if sent:
        logger.info(f"Reminder 24h: inviati {sent}/{len(apps)} promemoria")


_scheduler: AsyncIOScheduler | None = None


def start_reminder_scheduler(db):
    """Avvia il job 'ogni ora'. Idempotente."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    sched = AsyncIOScheduler(timezone=APP_TZ)
    sched.add_job(
        _send_reminders_24h,
        trigger="cron",
        minute=5,  # ogni ora al minuto 5
        args=[db],
        id="reminder_24h",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    sched.start()
    _scheduler = sched
    logger.info("Reminder scheduler avviato (ogni ora al minuto :05, TZ=%s)", APP_TZ)
    return sched


def shutdown_reminder_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
