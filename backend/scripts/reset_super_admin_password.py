"""Script one-shot per reimpostare la password di info@eligesoft.com."""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL = "info@eligesoft.com"
NEW_PASSWORD = "19Elige20."


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME", "prenotika")

    c = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=10000)
    db = c[db_name]

    new_hash = pwd.hash(NEW_PASSWORD)
    # verifica locale che il hash appena generato sia corretto
    assert pwd.verify(NEW_PASSWORD, new_hash), "hash generato non verifica!"
    print(f"→ hash generato correttamente per {EMAIL}")

    r = await db.users.update_one(
        {"email": EMAIL.lower().strip()},
        {"$set": {"password_hash": new_hash, "active": True, "role": "super_admin"}},
    )
    print(f"→ update: matched={r.matched_count} modified={r.modified_count}")

    # verifica finale rileggendo dal DB
    doc = await db.users.find_one({"email": EMAIL.lower().strip()})
    if not doc:
        print("!! utente non trovato dopo update")
        sys.exit(1)
    ok = pwd.verify(NEW_PASSWORD, doc["password_hash"])
    print(f"→ verify hash salvato su DB: {ok}")
    if not ok:
        sys.exit(1)

    c.close()
    print("\n✅ Password reset OK. Credenziali:")
    print(f"   email:    {EMAIL}")
    print(f"   password: {NEW_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
