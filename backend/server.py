from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta, date, time
from typing import List, Optional, Literal

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# -----------------------------------------------------------------------------
# Logging & DB
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("eligehub")

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))

app = FastAPI(title="EligeHub SaaS", version="1.0.0")
api = APIRouter(prefix="/api")
bearer_scheme = HTTPBearer(auto_error=False)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
def new_id() -> str:
    return str(uuid.uuid4())

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, role: str, studio_id: Optional[str]) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "studio_id": studio_id,
        "exp": now_utc() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now_utc(),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
Role = Literal["super_admin", "admin", "docente"]

class StudioBase(BaseModel):
    nome: str
    sede: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    piva: Optional[str] = None
    note: Optional[str] = None

class StudioCreate(StudioBase):
    admin_nome: str
    admin_cognome: str
    admin_email: EmailStr
    admin_password: str

class Studio(StudioBase):
    id: str
    created_at: datetime
    active: bool = True

class UserBase(BaseModel):
    nome: str
    cognome: str
    email: EmailStr
    role: Role
    studio_id: Optional[str] = None
    telefono: Optional[str] = None
    specializzazione: Optional[str] = None
    color: Optional[str] = None
    slot_minuti: Optional[int] = 60
    active: bool = True

class UserPublic(UserBase):
    id: str
    created_at: datetime

class DocenteCreate(BaseModel):
    nome: str
    cognome: str
    email: EmailStr
    password: str
    telefono: Optional[str] = None
    specializzazione: Optional[str] = None
    color: Optional[str] = None
    slot_minuti: Optional[int] = 60
    materia_ids: Optional[List[str]] = None

class DocenteUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    specializzazione: Optional[str] = None
    color: Optional[str] = None
    slot_minuti: Optional[int] = None
    active: Optional[bool] = None
    password: Optional[str] = None
    materia_ids: Optional[List[str]] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
    studio: Optional[Studio] = None

class ClienteBase(BaseModel):
    nome: str
    cognome: str
    email: Optional[EmailStr] = None
    cellulare: Optional[str] = None
    residenza: Optional[str] = None
    cap: Optional[str] = None
    indirizzo: Optional[str] = None
    data_nascita: Optional[str] = None  # ISO date
    note: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    email: Optional[EmailStr] = None
    cellulare: Optional[str] = None
    residenza: Optional[str] = None
    cap: Optional[str] = None
    indirizzo: Optional[str] = None
    data_nascita: Optional[str] = None
    note: Optional[str] = None

class Cliente(ClienteBase):
    id: str
    studio_id: str
    created_at: datetime

class OrarioBase(BaseModel):
    # 0 = Monday ... 6 = Sunday
    giorno: int = Field(ge=0, le=6)
    dal: str  # HH:MM
    al: str   # HH:MM

class OrarioCreate(OrarioBase):
    docente_id: Optional[str] = None  # If admin creates for a docente

class Orario(OrarioBase):
    id: str
    studio_id: str
    docente_id: str

class AppuntamentoBase(BaseModel):
    docente_id: str
    cliente_id: str
    data: str       # ISO date YYYY-MM-DD
    dal: str        # HH:MM
    al: str         # HH:MM
    note: Optional[str] = None
    stato: Literal["confermato", "annullato", "completato"] = "confermato"

class AppuntamentoCreate(AppuntamentoBase):
    pass

class AppuntamentoUpdate(BaseModel):
    docente_id: Optional[str] = None
    cliente_id: Optional[str] = None
    data: Optional[str] = None
    dal: Optional[str] = None
    al: Optional[str] = None
    note: Optional[str] = None
    stato: Optional[Literal["confermato", "annullato", "completato"]] = None

# --- Materie & bulk-booking models ---
class MateriaBase(BaseModel):
    descrizione: str
    prezzo: Optional[float] = None

class MateriaCreate(MateriaBase):
    pass

class MateriaUpdate(BaseModel):
    descrizione: Optional[str] = None
    prezzo: Optional[float] = None

class Materia(MateriaBase):
    id: str
    studio_id: str
    created_at: datetime

class NewClienteInline(BaseModel):
    nome: str
    cognome: str
    email: Optional[EmailStr] = None
    cellulare: Optional[str] = None

class BulkSlot(BaseModel):
    data: str  # YYYY-MM-DD
    dal: str
    al: str

class BulkAppuntamentoCreate(BaseModel):
    docente_id: Optional[str] = None     # admin may set; docente uses self
    cliente_id: Optional[str] = None     # either select existing
    nuovo_cliente: Optional[NewClienteInline] = None  # OR create new inline
    slots: List[BulkSlot]
    note: Optional[str] = None
    associa_alunno: bool = True

class Appuntamento(AppuntamentoBase):
    id: str
    studio_id: str
    created_at: datetime
    cliente_nome: Optional[str] = None
    docente_nome: Optional[str] = None

# -----------------------------------------------------------------------------
# Mongo helpers (use id as _id)
# -----------------------------------------------------------------------------
def _from_mongo(doc: Optional[dict]) -> Optional[dict]:
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc and "id" not in doc:
        doc["id"] = doc.pop("_id")
    else:
        doc.pop("_id", None)
    return doc

# -----------------------------------------------------------------------------
# Auth dependency
# -----------------------------------------------------------------------------
async def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> dict:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Non autenticato")
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessione scaduta")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

    user = await db.users.find_one({"_id": payload["sub"]})
    if not user or not user.get("active", True):
        raise HTTPException(status_code=401, detail="Utente non trovato o disattivato")
    user = _from_mongo(user)
    user.pop("password_hash", None)
    return user

def require_role(*roles: str):
    async def _checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Permessi insufficienti")
        return user
    return _checker

# -----------------------------------------------------------------------------
# Auth routes
# -----------------------------------------------------------------------------
@api.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o password non corretti")
    if not user.get("active", True):
        raise HTTPException(status_code=403, detail="Account disattivato")

    user_clean = _from_mongo(user)
    user_clean.pop("password_hash", None)
    token = create_access_token(user_clean["id"], user_clean["role"], user_clean.get("studio_id"))

    studio = None
    if user_clean.get("studio_id"):
        st = await db.studios.find_one({"_id": user_clean["studio_id"]})
        if st:
            studio = _from_mongo(st)

    return {"access_token": token, "token_type": "bearer", "user": user_clean, "studio": studio}

@api.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    studio = None
    if user.get("studio_id"):
        st = await db.studios.find_one({"_id": user["studio_id"]})
        if st:
            studio = _from_mongo(st)
    return {"user": user, "studio": studio}

# -----------------------------------------------------------------------------
# Studio routes (super_admin)
# -----------------------------------------------------------------------------
@api.get("/studios", response_model=List[Studio])
async def list_studios(_: dict = Depends(require_role("super_admin"))):
    items = await db.studios.find({}).to_list(1000)
    return [_from_mongo(x) for x in items]

@api.post("/studios", response_model=Studio, status_code=201)
async def create_studio(body: StudioCreate, _: dict = Depends(require_role("super_admin"))):
    # Validate admin email uniqueness
    existing = await db.users.find_one({"email": body.admin_email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email admin già in uso")

    studio_id = new_id()
    studio_doc = {
        "_id": studio_id,
        "nome": body.nome,
        "sede": body.sede,
        "telefono": body.telefono,
        "email": body.email,
        "piva": body.piva,
        "note": body.note,
        "active": True,
        "created_at": now_utc().isoformat(),
    }
    await db.studios.insert_one(studio_doc)

    admin_doc = {
        "_id": new_id(),
        "nome": body.admin_nome,
        "cognome": body.admin_cognome,
        "email": body.admin_email.lower().strip(),
        "password_hash": hash_password(body.admin_password),
        "role": "admin",
        "studio_id": studio_id,
        "active": True,
        "created_at": now_utc().isoformat(),
    }
    await db.users.insert_one(admin_doc)

    return _from_mongo(studio_doc)

@api.delete("/studios/{studio_id}", status_code=204)
async def delete_studio(studio_id: str, _: dict = Depends(require_role("super_admin"))):
    await db.studios.delete_one({"_id": studio_id})
    await db.users.delete_many({"studio_id": studio_id})
    await db.clienti.delete_many({"studio_id": studio_id})
    await db.orari.delete_many({"studio_id": studio_id})
    await db.appuntamenti.delete_many({"studio_id": studio_id})
    await db.docente_clienti.delete_many({"studio_id": studio_id})
    await db.materie.delete_many({"studio_id": studio_id})
    await db.docente_materie.delete_many({"studio_id": studio_id})
    return

# -----------------------------------------------------------------------------
# Docenti routes (admin within studio)
# -----------------------------------------------------------------------------
def _scope_studio_id(user: dict) -> str:
    sid = user.get("studio_id")
    if not sid:
        raise HTTPException(status_code=400, detail="Utente non assegnato a uno studio")
    return sid

@api.get("/docenti", response_model=List[UserPublic])
async def list_docenti(user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    items = await db.users.find({"studio_id": sid, "role": "docente"}).to_list(1000)
    return [_from_mongo(x) for x in items]

@api.post("/docenti", response_model=UserPublic, status_code=201)
async def create_docente(body: DocenteCreate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    email = body.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email già in uso")
    doc = {
        "_id": new_id(),
        "nome": body.nome,
        "cognome": body.cognome,
        "email": email,
        "password_hash": hash_password(body.password),
        "role": "docente",
        "studio_id": sid,
        "telefono": body.telefono,
        "specializzazione": body.specializzazione,
        "color": body.color or "#2C4C3B",
        "slot_minuti": body.slot_minuti or 60,
        "active": True,
        "created_at": now_utc().isoformat(),
    }
    await db.users.insert_one(doc)
    # Sincronizza materie associate
    if body.materia_ids:
        for mid in body.materia_ids:
            existing = await db.docente_materie.find_one({"studio_id": sid, "docente_id": doc["_id"], "materia_id": mid})
            if not existing:
                await db.docente_materie.insert_one({
                    "_id": new_id(),
                    "studio_id": sid,
                    "docente_id": doc["_id"],
                    "materia_id": mid,
                    "created_at": now_utc().isoformat(),
                })
    return _from_mongo(doc)

@api.patch("/docenti/{docente_id}", response_model=UserPublic)
async def update_docente(docente_id: str, body: DocenteUpdate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not target:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    updates = body.model_dump(exclude_unset=True)
    materia_ids = updates.pop("materia_ids", None)
    if "password" in updates and updates["password"]:
        updates["password_hash"] = hash_password(updates.pop("password"))
    elif "password" in updates:
        updates.pop("password")
    updates = {k: v for k, v in updates.items() if v is not None}
    if updates:
        await db.users.update_one({"_id": docente_id}, {"$set": updates})
    # Sincronizza materie (se passato esplicitamente, anche [] per svuotare)
    if materia_ids is not None:
        await db.docente_materie.delete_many({"studio_id": sid, "docente_id": docente_id})
        for mid in materia_ids:
            await db.docente_materie.insert_one({
                "_id": new_id(),
                "studio_id": sid,
                "docente_id": docente_id,
                "materia_id": mid,
                "created_at": now_utc().isoformat(),
            })
    fresh = await db.users.find_one({"_id": docente_id})
    return _from_mongo(fresh)

@api.delete("/docenti/{docente_id}", status_code=204)
async def delete_docente(docente_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not target:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    await db.users.delete_one({"_id": docente_id})
    await db.orari.delete_many({"docente_id": docente_id})
    await db.appuntamenti.delete_many({"docente_id": docente_id})
    await db.docente_clienti.delete_many({"docente_id": docente_id})
    await db.docente_materie.delete_many({"docente_id": docente_id})
    return

# ---- Associazione Alunni <-> Docente (N:M, tabella "pubblico" originale) ----
@api.get("/docenti/{docente_id}/alunni", response_model=List[Cliente])
async def list_alunni_docente(docente_id: str, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    if user["role"] == "docente" and user["id"] != docente_id:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    links = await db.docente_clienti.find({"studio_id": sid, "docente_id": docente_id}).to_list(2000)
    cli_ids = [link["cliente_id"] for link in links]
    if not cli_ids:
        return []
    clienti = await db.clienti.find({"_id": {"$in": cli_ids}}).sort("cognome", 1).to_list(2000)
    return [_from_mongo(c) for c in clienti]

@api.post("/docenti/{docente_id}/alunni/{cliente_id}", status_code=201)
async def associa_alunno(docente_id: str, cliente_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    cliente = await db.clienti.find_one({"_id": cliente_id, "studio_id": sid})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    existing = await db.docente_clienti.find_one({"studio_id": sid, "docente_id": docente_id, "cliente_id": cliente_id})
    if existing:
        return {"message": "Già associato"}
    await db.docente_clienti.insert_one({
        "_id": new_id(),
        "studio_id": sid,
        "docente_id": docente_id,
        "cliente_id": cliente_id,
        "created_at": now_utc().isoformat(),
    })
    return {"message": "Alunno associato al docente"}

@api.delete("/docenti/{docente_id}/alunni/{cliente_id}", status_code=204)
async def disassocia_alunno(docente_id: str, cliente_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    await db.docente_clienti.delete_many({"studio_id": sid, "docente_id": docente_id, "cliente_id": cliente_id})
    return

# -----------------------------------------------------------------------------
# Clienti routes (admin)
# -----------------------------------------------------------------------------
@api.get("/clienti", response_model=List[Cliente])
async def list_clienti(
    docente_id: Optional[str] = None,
    user: dict = Depends(require_role("admin", "docente")),
):
    sid = _scope_studio_id(user)
    # Se è docente, mostra solo i propri alunni associati
    if user["role"] == "docente":
        links = await db.docente_clienti.find({"studio_id": sid, "docente_id": user["id"]}).to_list(2000)
        ids = [link["cliente_id"] for link in links]
        if not ids:
            return []
        items = await db.clienti.find({"_id": {"$in": ids}}).sort("cognome", 1).to_list(2000)
        return [_from_mongo(x) for x in items]
    # Admin: opzionalmente filtra per docente_id (alunni associati)
    if docente_id:
        links = await db.docente_clienti.find({"studio_id": sid, "docente_id": docente_id}).to_list(2000)
        ids = [link["cliente_id"] for link in links]
        if not ids:
            return []
        items = await db.clienti.find({"_id": {"$in": ids}}).sort("cognome", 1).to_list(2000)
        return [_from_mongo(x) for x in items]
    items = await db.clienti.find({"studio_id": sid}).sort("cognome", 1).to_list(2000)
    return [_from_mongo(x) for x in items]

@api.post("/clienti", response_model=Cliente, status_code=201)
async def create_cliente(body: ClienteCreate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    doc = {
        "_id": new_id(),
        "studio_id": sid,
        "created_at": now_utc().isoformat(),
        **body.model_dump(),
    }
    await db.clienti.insert_one(doc)
    return _from_mongo(doc)

@api.patch("/clienti/{cliente_id}", response_model=Cliente)
async def update_cliente(cliente_id: str, body: ClienteUpdate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.clienti.find_one({"_id": cliente_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        await db.clienti.update_one({"_id": cliente_id}, {"$set": updates})
    fresh = await db.clienti.find_one({"_id": cliente_id})
    return _from_mongo(fresh)

@api.delete("/clienti/{cliente_id}", status_code=204)
async def delete_cliente(cliente_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.clienti.find_one({"_id": cliente_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    await db.clienti.delete_one({"_id": cliente_id})
    await db.docente_clienti.delete_many({"cliente_id": cliente_id})
    return

# -----------------------------------------------------------------------------
# Orari (disponibilità docente)
# -----------------------------------------------------------------------------
def _resolve_docente_id(user: dict, requested: Optional[str]) -> str:
    if user["role"] == "docente":
        return user["id"]
    if not requested:
        raise HTTPException(status_code=400, detail="docente_id richiesto")
    return requested

def _validate_time_range(dal: str, al: str):
    try:
        h1, m1 = map(int, dal.split(":"))
        h2, m2 = map(int, al.split(":"))
    except Exception:
        raise HTTPException(status_code=400, detail="Formato orario non valido (HH:MM)")
    if (h1, m1) >= (h2, m2):
        raise HTTPException(status_code=400, detail="L'orario di inizio deve essere precedente a quello di fine")

@api.get("/orari", response_model=List[Orario])
async def list_orari(docente_id: Optional[str] = None, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    q = {"studio_id": sid}
    if user["role"] == "docente":
        q["docente_id"] = user["id"]
    elif docente_id:
        q["docente_id"] = docente_id
    items = await db.orari.find(q).to_list(1000)
    return [_from_mongo(x) for x in items]

@api.post("/orari", response_model=Orario, status_code=201)
async def create_orario(body: OrarioCreate, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    docente_id = _resolve_docente_id(user, body.docente_id)
    # verify docente exists in studio
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    _validate_time_range(body.dal, body.al)
    doc = {
        "_id": new_id(),
        "studio_id": sid,
        "docente_id": docente_id,
        "giorno": body.giorno,
        "dal": body.dal,
        "al": body.al,
    }
    await db.orari.insert_one(doc)
    return _from_mongo(doc)

@api.delete("/orari/{orario_id}", status_code=204)
async def delete_orario(orario_id: str, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    target = await db.orari.find_one({"_id": orario_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Orario non trovato")
    if user["role"] == "docente" and target["docente_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Non puoi eliminare orari di altri docenti")
    await db.orari.delete_one({"_id": orario_id})
    return

# -----------------------------------------------------------------------------
# Appuntamenti
# -----------------------------------------------------------------------------
async def _hydrate_appuntamenti(items: List[dict]) -> List[dict]:
    if not items:
        return []
    cliente_ids = list({i["cliente_id"] for i in items})
    docente_ids = list({i["docente_id"] for i in items})
    clienti = {c["_id"]: c async for c in db.clienti.find({"_id": {"$in": cliente_ids}})}
    docenti = {u["_id"]: u async for u in db.users.find({"_id": {"$in": docente_ids}})}
    out = []
    for it in items:
        d = _from_mongo(it)
        c = clienti.get(it["cliente_id"])
        u = docenti.get(it["docente_id"])
        d["cliente_nome"] = f"{c['nome']} {c['cognome']}" if c else None
        d["docente_nome"] = f"{u['nome']} {u['cognome']}" if u else None
        out.append(d)
    return out

@api.get("/appuntamenti", response_model=List[Appuntamento])
async def list_appuntamenti(
    data_da: Optional[str] = None,
    data_a: Optional[str] = None,
    docente_id: Optional[str] = None,
    user: dict = Depends(require_role("admin", "docente")),
):
    sid = _scope_studio_id(user)
    q: dict = {"studio_id": sid}
    if user["role"] == "docente":
        q["docente_id"] = user["id"]
    elif docente_id:
        q["docente_id"] = docente_id
    if data_da or data_a:
        q["data"] = {}
        if data_da:
            q["data"]["$gte"] = data_da
        if data_a:
            q["data"]["$lte"] = data_a
    items = await db.appuntamenti.find(q).sort([("data", 1), ("dal", 1)]).to_list(2000)
    return await _hydrate_appuntamenti(items)

@api.post("/appuntamenti", response_model=Appuntamento, status_code=201)
async def create_appuntamento(body: AppuntamentoCreate, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    # docente scope: can only create for themselves
    docente_id = body.docente_id
    if user["role"] == "docente":
        docente_id = user["id"]
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    cliente = await db.clienti.find_one({"_id": body.cliente_id, "studio_id": sid})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    _validate_time_range(body.dal, body.al)

    # Check overlap with existing appuntamenti for the docente on same date
    overlap = await db.appuntamenti.find_one({
        "studio_id": sid,
        "docente_id": docente_id,
        "data": body.data,
        "stato": {"$ne": "annullato"},
        "dal": {"$lt": body.al},
        "al": {"$gt": body.dal},
    })
    if overlap:
        raise HTTPException(status_code=409, detail="Slot non disponibile: il docente ha già un appuntamento in questo orario")

    doc = {
        "_id": new_id(),
        "studio_id": sid,
        "docente_id": docente_id,
        "cliente_id": body.cliente_id,
        "data": body.data,
        "dal": body.dal,
        "al": body.al,
        "note": body.note,
        "stato": body.stato,
        "created_at": now_utc().isoformat(),
    }
    await db.appuntamenti.insert_one(doc)
    hydrated = await _hydrate_appuntamenti([doc])
    return hydrated[0]

@api.patch("/appuntamenti/{app_id}", response_model=Appuntamento)
async def update_appuntamento(app_id: str, body: AppuntamentoUpdate, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    target = await db.appuntamenti.find_one({"_id": app_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    if user["role"] == "docente" and target["docente_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if "dal" in updates or "al" in updates:
        dal = updates.get("dal", target["dal"])
        al = updates.get("al", target["al"])
        _validate_time_range(dal, al)
    if updates:
        await db.appuntamenti.update_one({"_id": app_id}, {"$set": updates})
    fresh = await db.appuntamenti.find_one({"_id": app_id})
    hydrated = await _hydrate_appuntamenti([fresh])
    return hydrated[0]

@api.delete("/appuntamenti/{app_id}", status_code=204)
async def delete_appuntamento(app_id: str, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    target = await db.appuntamenti.find_one({"_id": app_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    if user["role"] == "docente" and target["docente_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    await db.appuntamenti.delete_one({"_id": app_id})
    return

# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------
@api.get("/dashboard/stats")
async def dashboard_stats(user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    today = date.today().isoformat()
    week_end = (date.today() + timedelta(days=7)).isoformat()

    q_base = {"studio_id": sid}
    if user["role"] == "docente":
        q_base["docente_id"] = user["id"]

    tot_clienti = await db.clienti.count_documents({"studio_id": sid})
    tot_docenti = await db.users.count_documents({"studio_id": sid, "role": "docente"})
    app_oggi = await db.appuntamenti.count_documents({**q_base, "data": today, "stato": {"$ne": "annullato"}})
    app_settimana = await db.appuntamenti.count_documents({
        **q_base,
        "data": {"$gte": today, "$lte": week_end},
        "stato": {"$ne": "annullato"},
    })

    prossimi = await db.appuntamenti.find({
        **q_base,
        "data": {"$gte": today},
        "stato": {"$ne": "annullato"},
    }).sort([("data", 1), ("dal", 1)]).limit(5).to_list(5)
    prossimi_hydrated = await _hydrate_appuntamenti(prossimi)

    return {
        "totale_clienti": tot_clienti,
        "totale_docenti": tot_docenti,
        "appuntamenti_oggi": app_oggi,
        "appuntamenti_settimana": app_settimana,
        "prossimi_appuntamenti": prossimi_hydrated,
    }

# -----------------------------------------------------------------------------
# Materie (admin) + associazione N:M con docenti (riproduce combomat)
# -----------------------------------------------------------------------------
@api.get("/materie", response_model=List[Materia])
async def list_materie(user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    items = await db.materie.find({"studio_id": sid}).sort("descrizione", 1).to_list(500)
    return [_from_mongo(x) for x in items]

@api.post("/materie", response_model=Materia, status_code=201)
async def create_materia(body: MateriaCreate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    desc = body.descrizione.strip()
    if not desc:
        raise HTTPException(status_code=400, detail="Descrizione richiesta")
    existing = await db.materie.find_one({"studio_id": sid, "descrizione": desc})
    if existing:
        raise HTTPException(status_code=400, detail="Materia già esistente")
    doc = {
        "_id": new_id(),
        "studio_id": sid,
        "descrizione": desc,
        "prezzo": body.prezzo,
        "created_at": now_utc().isoformat(),
    }
    await db.materie.insert_one(doc)
    return _from_mongo(doc)

@api.patch("/materie/{materia_id}", response_model=Materia)
async def update_materia(materia_id: str, body: MateriaUpdate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.materie.find_one({"_id": materia_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Materia non trovata")
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        await db.materie.update_one({"_id": materia_id}, {"$set": updates})
    fresh = await db.materie.find_one({"_id": materia_id})
    return _from_mongo(fresh)

@api.delete("/materie/{materia_id}", status_code=204)
async def delete_materia(materia_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.materie.find_one({"_id": materia_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Materia non trovata")
    await db.materie.delete_one({"_id": materia_id})
    await db.docente_materie.delete_many({"materia_id": materia_id})
    return

@api.get("/docenti/{docente_id}/materie", response_model=List[Materia])
async def list_materie_docente(docente_id: str, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    links = await db.docente_materie.find({"studio_id": sid, "docente_id": docente_id}).to_list(500)
    mat_ids = [link["materia_id"] for link in links]
    if not mat_ids:
        return []
    items = await db.materie.find({"_id": {"$in": mat_ids}}).sort("descrizione", 1).to_list(500)
    return [_from_mongo(x) for x in items]

@api.post("/docenti/{docente_id}/materie/{materia_id}", status_code=201)
async def associa_materia(docente_id: str, materia_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    materia = await db.materie.find_one({"_id": materia_id, "studio_id": sid})
    if not docente or not materia:
        raise HTTPException(status_code=404, detail="Docente o materia non trovati")
    existing = await db.docente_materie.find_one({"studio_id": sid, "docente_id": docente_id, "materia_id": materia_id})
    if existing:
        return {"message": "Già associata"}
    await db.docente_materie.insert_one({
        "_id": new_id(),
        "studio_id": sid,
        "docente_id": docente_id,
        "materia_id": materia_id,
        "created_at": now_utc().isoformat(),
    })
    return {"message": "Materia associata"}

@api.delete("/docenti/{docente_id}/materie/{materia_id}", status_code=204)
async def disassocia_materia(docente_id: str, materia_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    await db.docente_materie.delete_many({"studio_id": sid, "docente_id": docente_id, "materia_id": materia_id})
    return

# -----------------------------------------------------------------------------
# Bulk booking con ricorrenza + creazione cliente al volo
# -----------------------------------------------------------------------------
@api.post("/appuntamenti/bulk")
async def bulk_appuntamenti(body: BulkAppuntamentoCreate, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    # Docente scope
    docente_id = body.docente_id
    if user["role"] == "docente":
        docente_id = user["id"]
    if not docente_id:
        raise HTTPException(status_code=400, detail="docente_id richiesto")
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")

    # Risolvi cliente: esistente o nuovo
    cliente_id = body.cliente_id
    if not cliente_id and body.nuovo_cliente:
        nc = body.nuovo_cliente
        cliente_id = new_id()
        await db.clienti.insert_one({
            "_id": cliente_id,
            "studio_id": sid,
            "nome": nc.nome.strip(),
            "cognome": nc.cognome.strip(),
            "email": nc.email,
            "cellulare": nc.cellulare,
            "created_at": now_utc().isoformat(),
        })
    if not cliente_id:
        raise HTTPException(status_code=400, detail="Specificare un cliente esistente o i dati per un nuovo cliente")

    cliente = await db.clienti.find_one({"_id": cliente_id, "studio_id": sid})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")

    # Auto-associate cliente al docente se richiesto
    if body.associa_alunno:
        existing_link = await db.docente_clienti.find_one({"studio_id": sid, "docente_id": docente_id, "cliente_id": cliente_id})
        if not existing_link:
            await db.docente_clienti.insert_one({
                "_id": new_id(),
                "studio_id": sid,
                "docente_id": docente_id,
                "cliente_id": cliente_id,
                "created_at": now_utc().isoformat(),
            })

    if not body.slots:
        raise HTTPException(status_code=400, detail="Nessuno slot specificato")

    created = []
    skipped = []
    for s in body.slots:
        try:
            _validate_time_range(s.dal, s.al)
        except HTTPException as e:
            skipped.append({"data": s.data, "dal": s.dal, "al": s.al, "motivo": e.detail})
            continue
        overlap = await db.appuntamenti.find_one({
            "studio_id": sid,
            "docente_id": docente_id,
            "data": s.data,
            "stato": {"$ne": "annullato"},
            "dal": {"$lt": s.al},
            "al": {"$gt": s.dal},
        })
        if overlap:
            skipped.append({"data": s.data, "dal": s.dal, "al": s.al, "motivo": "Slot occupato"})
            continue
        doc = {
            "_id": new_id(),
            "studio_id": sid,
            "docente_id": docente_id,
            "cliente_id": cliente_id,
            "data": s.data,
            "dal": s.dal,
            "al": s.al,
            "note": body.note,
            "stato": "confermato",
            "created_at": now_utc().isoformat(),
        }
        await db.appuntamenti.insert_one(doc)
        created.append({"data": s.data, "dal": s.dal, "al": s.al, "id": doc["_id"]})

    return {
        "cliente_id": cliente_id,
        "docente_id": docente_id,
        "created": created,
        "skipped": skipped,
        "count_created": len(created),
        "count_skipped": len(skipped),
    }

# -----------------------------------------------------------------------------
# Report PDF appuntamenti
# -----------------------------------------------------------------------------
from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import mm

_GIORNI_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

def _date_range_for(period: str, ref: date) -> tuple[date, date, str]:
    if period == "day":
        return ref, ref, ref.strftime("%d/%m/%Y")
    if period == "week":
        weekday = ref.weekday()
        start = ref - timedelta(days=weekday)
        end = start + timedelta(days=6)
        return start, end, f"settimana {start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')}"
    if period == "month":
        start = ref.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        return start, end, f"{start.strftime('%B %Y')}"
    raise HTTPException(status_code=400, detail="period deve essere day, week o month")

@api.get("/reports/appuntamenti.pdf")
async def report_appuntamenti_pdf(
    period: str = "week",            # day | week | month
    data: Optional[str] = None,      # YYYY-MM-DD (default oggi)
    docente_id: Optional[str] = None,  # se None: tutti
    user: dict = Depends(require_role("admin", "docente")),
):
    sid = _scope_studio_id(user)
    ref = date.fromisoformat(data) if data else date.today()
    start, end, label = _date_range_for(period, ref)

    # Docenti scope
    if user["role"] == "docente":
        docente_id = user["id"]
    docenti_q = {"studio_id": sid, "role": "docente"}
    if docente_id:
        docenti_q["_id"] = docente_id
    docenti = await db.users.find(docenti_q).sort("cognome", 1).to_list(500)
    if not docenti:
        raise HTTPException(status_code=404, detail="Nessun docente trovato")

    # Studio info
    studio = await db.studios.find_one({"_id": sid})
    studio_nome = studio["nome"] if studio else "Centro Studi"

    # Appuntamenti del range, hydrated
    app_q = {
        "studio_id": sid,
        "data": {"$gte": start.isoformat(), "$lte": end.isoformat()},
        "docente_id": {"$in": [d["_id"] for d in docenti]},
    }
    raw_app = await db.appuntamenti.find(app_q).sort([("data", 1), ("dal", 1)]).to_list(5000)
    hydrated = await _hydrate_appuntamenti(raw_app)

    by_docente: dict[str, list[dict]] = {d["_id"]: [] for d in docenti}
    for a in hydrated:
        if a["docente_id"] in by_docente:
            by_docente[a["docente_id"]].append(a)

    # Build PDF
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=colors.HexColor("#2C4C3B"), fontSize=20, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#1E1E1E"), fontSize=14, spaceBefore=10, spaceAfter=6)
    small = ParagraphStyle("small", parent=styles["Normal"], textColor=colors.HexColor("#5C5C5C"), fontSize=9)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10)

    story = []
    story.append(Paragraph(studio_nome, h1))
    period_it = {"day": "Giorno", "week": "Settimana", "month": "Mese"}.get(period, period)
    sub = f"Report appuntamenti — {period_it}: {label}"
    if docente_id and docenti:
        d = docenti[0]
        sub += f" — Docente: {d['nome']} {d['cognome']}"
    story.append(Paragraph(sub, small))
    story.append(Spacer(1, 6))

    total_appuntamenti = 0
    for d in docenti:
        list_d = by_docente.get(d["_id"], [])
        if not list_d and docente_id is None:
            continue  # in modalità "tutti", salta i docenti senza appuntamenti
        story.append(Paragraph(f"{d['nome']} {d['cognome']}", h2))
        story.append(Paragraph(
            f"Email: {d.get('email','—')} • Durata slot: {d.get('slot_minuti', 60)} min • Totale appuntamenti: {len(list_d)}",
            small,
        ))
        story.append(Spacer(1, 4))
        if not list_d:
            story.append(Paragraph("Nessun appuntamento nel periodo selezionato.", body))
        else:
            data_rows = [["Data", "Giorno", "Dalle", "Alle", "Cliente", "Stato", "Note"]]
            for a in list_d:
                dt = date.fromisoformat(a["data"])
                data_rows.append([
                    dt.strftime("%d/%m/%Y"),
                    _GIORNI_IT[dt.weekday()],
                    a["dal"],
                    a["al"],
                    a.get("cliente_nome") or "—",
                    a.get("stato", "confermato"),
                    (a.get("note") or "")[:60],
                ])
            tbl = Table(data_rows, colWidths=[22*mm, 24*mm, 14*mm, 14*mm, 50*mm, 22*mm, 34*mm], repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C4C3B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FBF9F6"), colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (3, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E4E0D6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(tbl)
            total_appuntamenti += len(list_d)
        story.append(Spacer(1, 8))

    if total_appuntamenti == 0:
        story.append(Paragraph("Nessun appuntamento nel periodo selezionato.", body))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generato il {now_utc().strftime('%d/%m/%Y %H:%M')} UTC — EligeHub SaaS",
        small,
    ))
    doc.build(story)
    buf.seek(0)

    filename = f"appuntamenti-{period}-{start.isoformat()}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

# -----------------------------------------------------------------------------
# Public availability check: free slots for a docente on a given date
# -----------------------------------------------------------------------------
def _to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m

def _to_hhmm(mins: int) -> str:
    return f"{mins // 60:02d}:{mins % 60:02d}"

@api.get("/disponibilita")
async def disponibilita(
    docente_id: str,
    data: str,  # YYYY-MM-DD
    slot_minuti: Optional[int] = None,
    user: dict = Depends(require_role("admin", "docente")),
):
    sid = _scope_studio_id(user)
    docente = await db.users.find_one({"_id": docente_id, "studio_id": sid, "role": "docente"})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente non trovato")
    if slot_minuti is None:
        slot_minuti = int(docente.get("slot_minuti") or 60)
    try:
        d = date.fromisoformat(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Data non valida (YYYY-MM-DD)")
    giorno = d.weekday()  # 0=Mon
    orari = await db.orari.find({"studio_id": sid, "docente_id": docente_id, "giorno": giorno}).to_list(100)
    if not orari:
        return {"slots": []}
    booked = await db.appuntamenti.find({
        "studio_id": sid, "docente_id": docente_id, "data": data, "stato": {"$ne": "annullato"}
    }).to_list(500)
    slots = []
    for o in orari:
        start = _to_minutes(o["dal"])
        end = _to_minutes(o["al"])
        cur = start
        while cur + slot_minuti <= end:
            slot_dal = _to_hhmm(cur)
            slot_al = _to_hhmm(cur + slot_minuti)
            # check overlap with booked
            conflict = any(
                _to_minutes(b["dal"]) < cur + slot_minuti and _to_minutes(b["al"]) > cur
                for b in booked
            )
            if not conflict:
                slots.append({"dal": slot_dal, "al": slot_al})
            cur += slot_minuti
    return {"slots": slots}

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@api.get("/")
async def root():
    return {"app": "EligeHub SaaS", "status": "ok", "time": now_utc().isoformat()}

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Startup: indexes & seed
# -----------------------------------------------------------------------------
async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("studio_id")
    await db.studios.create_index("nome")
    await db.clienti.create_index([("studio_id", 1), ("cognome", 1)])
    await db.orari.create_index([("studio_id", 1), ("docente_id", 1), ("giorno", 1)])
    await db.appuntamenti.create_index([("studio_id", 1), ("docente_id", 1), ("data", 1)])
    await db.docente_clienti.create_index([("studio_id", 1), ("docente_id", 1), ("cliente_id", 1)], unique=True)
    await db.materie.create_index([("studio_id", 1), ("descrizione", 1)], unique=True)
    await db.docente_materie.create_index([("studio_id", 1), ("docente_id", 1), ("materia_id", 1)], unique=True)

async def seed_super_admin_and_demo():
    super_email = os.environ["SUPER_ADMIN_EMAIL"].lower().strip()
    super_password = os.environ["SUPER_ADMIN_PASSWORD"]
    existing_super = await db.users.find_one({"email": super_email})
    if not existing_super:
        await db.users.insert_one({
            "_id": new_id(),
            "nome": "Super",
            "cognome": "Admin",
            "email": super_email,
            "password_hash": hash_password(super_password),
            "role": "super_admin",
            "studio_id": None,
            "active": True,
            "created_at": now_utc().isoformat(),
        })
        logger.info("Seeded super_admin %s", super_email)
    elif not verify_password(super_password, existing_super["password_hash"]):
        await db.users.update_one({"_id": existing_super["_id"]}, {"$set": {"password_hash": hash_password(super_password)}})
        logger.info("Updated super_admin password")

    # Demo studio + admin + docente
    demo_studio = await db.studios.find_one({"nome": os.environ["DEMO_STUDIO_NAME"]})
    if not demo_studio:
        studio_id = new_id()
        await db.studios.insert_one({
            "_id": studio_id,
            "nome": os.environ["DEMO_STUDIO_NAME"],
            "sede": "Via Roma 1, Milano",
            "telefono": "+39 02 1234567",
            "email": "info@demo.it",
            "piva": "IT01234567890",
            "note": "Studio demo precaricato",
            "active": True,
            "created_at": now_utc().isoformat(),
        })
        await db.users.insert_one({
            "_id": new_id(),
            "nome": "Anna",
            "cognome": "Rossi",
            "email": os.environ["DEMO_ADMIN_EMAIL"].lower().strip(),
            "password_hash": hash_password(os.environ["DEMO_ADMIN_PASSWORD"]),
            "role": "admin",
            "studio_id": studio_id,
            "active": True,
            "created_at": now_utc().isoformat(),
        })
        docente_id = new_id()
        await db.users.insert_one({
            "_id": docente_id,
            "nome": "Marco",
            "cognome": "Bianchi",
            "email": os.environ["DEMO_DOCENTE_EMAIL"].lower().strip(),
            "password_hash": hash_password(os.environ["DEMO_DOCENTE_PASSWORD"]),
            "role": "docente",
            "studio_id": studio_id,
            "specializzazione": "Matematica",
            "color": "#2C4C3B",
            "slot_minuti": 60,
            "active": True,
            "created_at": now_utc().isoformat(),
        })
        # Seed default availability Mon-Fri 9-13 and 15-18
        for g in range(0, 5):
            await db.orari.insert_many([
                {"_id": new_id(), "studio_id": studio_id, "docente_id": docente_id, "giorno": g, "dal": "09:00", "al": "13:00"},
                {"_id": new_id(), "studio_id": studio_id, "docente_id": docente_id, "giorno": g, "dal": "15:00", "al": "18:00"},
            ])
        # Seed a couple of demo clienti
        cli1_id = new_id()
        cli2_id = new_id()
        await db.clienti.insert_many([
            {"_id": cli1_id, "studio_id": studio_id, "nome": "Luca", "cognome": "Verdi", "email": "luca.verdi@example.com", "cellulare": "+39 333 1111111", "created_at": now_utc().isoformat()},
            {"_id": cli2_id, "studio_id": studio_id, "nome": "Giulia", "cognome": "Neri", "email": "giulia.neri@example.com", "cellulare": "+39 333 2222222", "created_at": now_utc().isoformat()},
        ])
        # Associate both demo clienti to the demo docente (relazione "pubblico")
        await db.docente_clienti.insert_many([
            {"_id": new_id(), "studio_id": studio_id, "docente_id": docente_id, "cliente_id": cli1_id, "created_at": now_utc().isoformat()},
            {"_id": new_id(), "studio_id": studio_id, "docente_id": docente_id, "cliente_id": cli2_id, "created_at": now_utc().isoformat()},
        ])
        logger.info("Seeded demo studio + admin + docente + clienti")

    # Patch: assicurati che il docente demo abbia gli alunni associati anche su DB già esistenti
    demo_studio_after = await db.studios.find_one({"nome": os.environ["DEMO_STUDIO_NAME"]})
    if demo_studio_after:
        sid = demo_studio_after["_id"]
        demo_docente = await db.users.find_one({"studio_id": sid, "role": "docente"})
        if demo_docente:
            # ensure slot_minuti
            if not demo_docente.get("slot_minuti"):
                await db.users.update_one({"_id": demo_docente["_id"]}, {"$set": {"slot_minuti": 60}})
            # ensure alunni links
            existing_links = await db.docente_clienti.count_documents({"studio_id": sid, "docente_id": demo_docente["_id"]})
            if existing_links == 0:
                clienti = await db.clienti.find({"studio_id": sid}).to_list(50)
                for c in clienti:
                    await db.docente_clienti.insert_one({
                        "_id": new_id(),
                        "studio_id": sid,
                        "docente_id": demo_docente["_id"],
                        "cliente_id": c["_id"],
                        "created_at": now_utc().isoformat(),
                    })
                logger.info("Patched demo: linked %d alunni to demo docente", len(clienti))

@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_super_admin_and_demo()

@app.on_event("shutdown")
async def on_shutdown():
    client.close()
