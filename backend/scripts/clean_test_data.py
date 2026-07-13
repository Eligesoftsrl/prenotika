"""
Script per pulire il database mantenendo SOLO il super_admin (info@eligesoft.com).

Uso:
    # Railway (produzione) - copia MONGO_URL dalle env di Railway
    MONGO_URL="mongodb://..." DB_NAME="prenotika" python backend/scripts/clean_test_data.py

    # Locale (già pulito)
    python backend/scripts/clean_test_data.py

Con --dry-run mostra solo cosa verrebbe cancellato senza eseguire.
"""
import os
import sys
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

SUPER_ADMIN_EMAIL = "info@eligesoft.com"

COLLECTIONS_TO_WIPE = [
    "studios",
    "appuntamenti",
    "clienti",
    "docenti",
    "materie",
    "orari",
    "eccezioni",
    "docente_alunni",
    "docente_clienti",
    "docente_materie",
    "password_resets",
    "otp_codes",
    "onboarding_tokens",
    "payment_transactions",
    "leads",
]


async def main():
    dry = "--dry-run" in sys.argv
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "prenotika")
    if not mongo_url:
        print("ERRORE: MONGO_URL non impostata.")
        print("  Uso: MONGO_URL='mongodb://...' DB_NAME='prenotika' python backend/scripts/clean_test_data.py")
        sys.exit(1)

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print(f"\n🔗 Connessione a: {db_name}  (dry-run: {dry})")
    print("=" * 60)

    # Conteggi PRIMA
    print("\n📊 PRIMA:")
    for c in COLLECTIONS_TO_WIPE:
        n = await db[c].count_documents({})
        print(f"  {c}: {n}")
    users_before = await db.users.count_documents({})
    super_admin = await db.users.find_one({"email": SUPER_ADMIN_EMAIL})
    print(f"  users: {users_before}  (super_admin trovato: {'✅' if super_admin else '❌ ATTENZIONE'})")

    if not super_admin:
        print(f"\n❌ ABORT: super_admin '{SUPER_ADMIN_EMAIL}' non trovato nel DB. Interruzione.")
        print(f"   Crea prima il super_admin, poi rilancia lo script.")
        client.close()
        sys.exit(2)

    if dry:
        print("\n🔍 DRY-RUN: nessuna operazione eseguita. Rilancia senza --dry-run per procedere.")
        client.close()
        return

    print(f"\n⚠️  Sto per cancellare TUTTI i dati tranne super_admin ({SUPER_ADMIN_EMAIL}).")
    ans = input("Confermi? Scrivi 'PULISCI' per procedere: ")
    if ans.strip() != "PULISCI":
        print("Operazione annullata.")
        client.close()
        return

    # Cancellazione
    for c in COLLECTIONS_TO_WIPE:
        r = await db[c].delete_many({})
        print(f"  {c}: cancellati {r.deleted_count}")
    r = await db.users.delete_many({"email": {"$ne": SUPER_ADMIN_EMAIL}})
    print(f"  users: cancellati {r.deleted_count} (tenuto {SUPER_ADMIN_EMAIL})")

    # Conteggi DOPO
    print("\n📊 DOPO:")
    for c in COLLECTIONS_TO_WIPE:
        n = await db[c].count_documents({})
        print(f"  {c}: {n}")
    users_after = await db.users.count_documents({})
    print(f"  users: {users_after}")

    print("\n✅ Pulizia completata.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
