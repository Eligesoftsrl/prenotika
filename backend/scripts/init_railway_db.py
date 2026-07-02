"""
Script di bootstrap del database di produzione (Railway MongoDB).
Uso:
    MONGO_URL="mongodb://..." DB_NAME="prenotika" \
    SUPER_ADMIN_EMAIL="..." SUPER_ADMIN_PASSWORD="..." \
    python -m backend.scripts.init_railway_db

Cosa fa:
  - Verifica la connessione a MongoDB
  - Crea tutti gli indici necessari (idempotente)
  - Crea l'utente super_admin (idempotente)
  - NON crea alcuno studio/utente demo: l'utente crea i tenant in produzione
"""
import os
import sys
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

# Consenti l'esecuzione anche via `python backend/scripts/init_railway_db.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from passlib.context import CryptContext  # noqa: E402

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _ensure_indexes(db):
    await db.users.create_index("email", unique=True)
    await db.users.create_index("studio_id")
    await db.studios.create_index("nome")
    await db.clienti.create_index([("studio_id", 1), ("cognome", 1)])
    await db.orari.create_index([("studio_id", 1), ("docente_id", 1), ("giorno", 1)])
    await db.appuntamenti.create_index([("studio_id", 1), ("docente_id", 1), ("data", 1)])
    await db.docente_clienti.create_index(
        [("studio_id", 1), ("docente_id", 1), ("cliente_id", 1)], unique=True
    )
    await db.materie.create_index([("studio_id", 1), ("descrizione", 1)], unique=True)
    await db.docente_materie.create_index(
        [("studio_id", 1), ("docente_id", 1), ("materia_id", 1)], unique=True
    )
    await db.eccezioni.create_index([("studio_id", 1), ("docente_id", 1), ("data_inizio", 1)])
    await db.leads.create_index([("created_at", -1)])
    await db.leads.create_index("status")


async def _seed_super_admin(db):
    email = os.environ["SUPER_ADMIN_EMAIL"].lower().strip()
    password = os.environ["SUPER_ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": email})
    if not existing:
        await db.users.insert_one({
            "_id": str(uuid4()),
            "nome": "Super",
            "cognome": "Admin",
            "email": email,
            "password_hash": pwd_ctx.hash(password),
            "role": "super_admin",
            "studio_id": None,
            "active": True,
            "created_at": _now_iso(),
        })
        print(f"  [OK] Super admin creato: {email}")
    else:
        if not pwd_ctx.verify(password, existing["password_hash"]):
            await db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {"password_hash": pwd_ctx.hash(password)}},
            )
            print(f"  [OK] Password super admin aggiornata: {email}")
        else:
            print(f"  [SKIP] Super admin già esistente: {email}")


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME", "prenotika")

    print(f"→ Connessione a MongoDB (db: {db_name})…")
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=10000)
    try:
        info = await client.admin.command("ping")
        print(f"  [OK] Ping: {info}")
    except Exception as e:
        print(f"  [ERR] Impossibile connettersi: {e}")
        sys.exit(1)

    db = client[db_name]

    print("→ Creo indici…")
    await _ensure_indexes(db)
    print("  [OK] Indici pronti")

    print("→ Seed super admin…")
    await _seed_super_admin(db)

    print("→ Elenco collezioni presenti:")
    for c in await db.list_collection_names():
        cnt = await db[c].count_documents({})
        print(f"    - {c}: {cnt} doc")

    client.close()
    print("\n✅ Database pronto per la produzione.")


if __name__ == "__main__":
    asyncio.run(main())
