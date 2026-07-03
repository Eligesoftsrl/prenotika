from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import secrets
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
from email_service import send_appointment_email, send_bulk_appointments_email

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

app = FastAPI(title="Prenotika SaaS", version="1.0.0")
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
Tipologia = Literal["centro_studi", "studio_legale", "studio_medico"]
Plan = Literal["free", "pro", "business"]

# Limiti professionisti per piano. None = illimitato.
PLAN_LIMITS_PROFESSIONISTI = {
    "free": 1,
    "pro": 5,
    "business": None,
}

class StudioBase(BaseModel):
    nome: str
    sede: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    piva: Optional[str] = None
    note: Optional[str] = None
    tipologia: Tipologia = "centro_studi"
    plan: Plan = "free"
    comunicazioni: Optional[str] = None  # testo libero mostrato in calce ai report PDF
    logo_base64: Optional[str] = None    # dataURL/base64 PNG-JPEG del logo stampato in cima ai PDF

class StudioUpdate(BaseModel):
    nome: Optional[str] = None
    sede: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    piva: Optional[str] = None
    note: Optional[str] = None
    tipologia: Optional[Tipologia] = None
    plan: Optional[Plan] = None
    comunicazioni: Optional[str] = None
    logo_base64: Optional[str] = None

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

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

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
    materia_id: Optional[str] = None
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
    materia_id: Optional[str] = None
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
    materia_id: Optional[str] = None
    associa_alunno: bool = True

class Appuntamento(AppuntamentoBase):
    id: str
    studio_id: str
    created_at: datetime
    cliente_nome: Optional[str] = None
    docente_nome: Optional[str] = None
    materia_descrizione: Optional[str] = None

# --- Eccezioni / ferie del professionista ---
class EccezioneBase(BaseModel):
    data_inizio: str           # YYYY-MM-DD
    data_fine: str             # YYYY-MM-DD (inclusive)
    motivo: Optional[str] = None     # ferie / malattia / festivo / personale (libero)
    tipo: Literal["chiuso", "personalizzato"] = "chiuso"  # personalizzato = blocco parziale
    ora_inizio: Optional[str] = None  # HH:MM (solo se tipo=personalizzato)
    ora_fine: Optional[str] = None

class EccezioneCreate(EccezioneBase):
    docente_id: Optional[str] = None  # admin può specificarlo; docente -> self

class Eccezione(EccezioneBase):
    id: str
    studio_id: str
    docente_id: str
    created_at: datetime

# --- Lead (contact form pubblico landing) ---
class LeadCreate(BaseModel):
    nome: str
    email: EmailStr
    telefono: Optional[str] = None
    tipologia: Optional[str] = None
    studio: Optional[str] = None
    messaggio: Optional[str] = None
    piano_interesse: Optional[str] = None

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


@api.post("/auth/change-password")
async def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nuova password deve avere almeno 8 caratteri")
    doc = await db.users.find_one({"_id": user["id"]})
    if not doc or not verify_password(body.current_password, doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Password attuale non corretta")
    await db.users.update_one(
        {"_id": user["id"]},
        {"$set": {"password_hash": hash_password(body.new_password)}},
    )
    return {"ok": True}


@api.post("/auth/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Genera token di reset e invia email. Risponde sempre 200 per non rivelare esistenza email."""
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email, "active": {"$ne": False}})
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = now_utc() + timedelta(minutes=60)
        await db.password_resets.insert_one({
            "_id": new_id(),
            "user_id": user["_id"],
            "token": token,
            "expires_at": expires_at.isoformat(),
            "used": False,
            "created_at": now_utc().isoformat(),
        })
        frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
        if not frontend_url:
            frontend_url = "https://www.prenotika.com"
        reset_url = f"{frontend_url}/reset-password?token={token}"
        try:
            from email_service import send_password_reset_email
            await send_password_reset_email(
                to_email=email,
                to_name=f"{user.get('nome','')} {user.get('cognome','')}".strip(),
                reset_url=reset_url,
            )
        except Exception as e:
            logger.warning("send_password_reset_email failed: %s", e)
    # Sempre 200 anche se l'utente non esiste (privacy)
    return {"ok": True}


@api.post("/auth/reset-password")
async def reset_password(body: ResetPasswordRequest):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="La password deve avere almeno 8 caratteri")
    rec = await db.password_resets.find_one({"token": body.token})
    if not rec:
        raise HTTPException(status_code=400, detail="Link non valido")
    if rec.get("used"):
        raise HTTPException(status_code=400, detail="Link già utilizzato")
    try:
        expires_at = datetime.fromisoformat(rec["expires_at"])
    except Exception:
        expires_at = now_utc() - timedelta(seconds=1)
    if expires_at < now_utc():
        raise HTTPException(status_code=400, detail="Link scaduto. Richiedine uno nuovo.")
    await db.users.update_one(
        {"_id": rec["user_id"]},
        {"$set": {"password_hash": hash_password(body.new_password)}},
    )
    await db.password_resets.update_one(
        {"_id": rec["_id"]},
        {"$set": {"used": True, "used_at": now_utc().isoformat()}},
    )
    return {"ok": True}

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
        "tipologia": body.tipologia,
        "plan": body.plan or "free",
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

    # Invio email di benvenuto (best-effort: NON bloccare la creazione se fallisce).
    try:
        setup_token = secrets.token_urlsafe(32)
        await db.password_resets.insert_one({
            "_id": new_id(),
            "user_id": admin_doc["_id"],
            "token": setup_token,
            "expires_at": (now_utc() + timedelta(days=7)).isoformat(),
            "used": False,
            "created_at": now_utc().isoformat(),
        })
        frontend_url = (os.environ.get("FRONTEND_URL") or "https://www.prenotika.com").rstrip("/")
        from email_service import send_welcome_admin_email
        await send_welcome_admin_email(
            to_email=admin_doc["email"],
            to_name=f"{admin_doc['nome']} {admin_doc['cognome']}".strip(),
            studio_nome=studio_doc["nome"],
            login_email=admin_doc["email"],
            temp_password=body.admin_password,
            login_url=f"{frontend_url}/login",
            setup_url=f"{frontend_url}/reset-password?token={setup_token}",
        )
        logger.info("Welcome email sent to %s for studio %s", admin_doc["email"], studio_doc["nome"])
    except Exception as e:
        logger.warning("Welcome email failed (studio creato comunque): %s", e)

    return _from_mongo(studio_doc)

@api.get("/studio")
async def get_my_studio(user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    fresh = await db.studios.find_one({"_id": sid})
    return _from_mongo(fresh)

@api.get("/studio/quota")
async def get_studio_quota(user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    studio_doc = await db.studios.find_one({"_id": sid})
    plan = (studio_doc or {}).get("plan", "free")
    limit = PLAN_LIMITS_PROFESSIONISTI.get(plan)
    used = await db.users.count_documents({"studio_id": sid, "role": "docente", "active": True})
    return {
        "plan": plan,
        "professionisti_used": used,
        "professionisti_limit": limit,  # None = illimitato
        "can_add_more": True if limit is None else used < limit,
    }

@api.patch("/studio", response_model=Studio)
async def update_my_studio(body: StudioUpdate, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    # SECURITY: l'admin non può modificare il piano del proprio studio (solo super_admin lo può fare).
    updates.pop("plan", None)
    if updates:
        await db.studios.update_one({"_id": sid}, {"$set": updates})
    fresh = await db.studios.find_one({"_id": sid})
    return _from_mongo(fresh)

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

@api.patch("/studios/{studio_id}", response_model=Studio)
async def update_studio_as_super(studio_id: str, body: StudioUpdate, _: dict = Depends(require_role("super_admin"))):
    target = await db.studios.find_one({"_id": studio_id})
    if not target:
        raise HTTPException(status_code=404, detail="Studio non trovato")
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        await db.studios.update_one({"_id": studio_id}, {"$set": updates})
    fresh = await db.studios.find_one({"_id": studio_id})
    return _from_mongo(fresh)

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
    # Enforcement quota professionisti per piano
    studio_doc = await db.studios.find_one({"_id": sid})
    plan = (studio_doc or {}).get("plan", "free")
    limit = PLAN_LIMITS_PROFESSIONISTI.get(plan)
    if limit is not None:
        current_count = await db.users.count_documents({"studio_id": sid, "role": "docente", "active": True})
        if current_count >= limit:
            raise HTTPException(
                status_code=403,
                detail=f"Limite del piano {plan.capitalize()} raggiunto ({limit} professionisti). Passa a un piano superiore per aggiungere altri operatori.",
            )
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
        "color": body.color or "#7C3AED",
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
    studio = await db.studios.find_one({"_id": sid})
    tipologia = (studio or {}).get("tipologia", "centro_studi")
    # In centro_studi non c'è associazione studente-docente: tutti vedono tutti
    if tipologia == "centro_studi":
        items = await db.clienti.find({"studio_id": sid}).sort("cognome", 1).to_list(2000)
        return [_from_mongo(x) for x in items]
    # Se è docente in studio_legale/medico, mostra solo i propri clienti associati
    if user["role"] == "docente":
        links = await db.docente_clienti.find({"studio_id": sid, "docente_id": user["id"]}).to_list(2000)
        ids = [link["cliente_id"] for link in links]
        if not ids:
            return []
        items = await db.clienti.find({"_id": {"$in": ids}}).sort("cognome", 1).to_list(2000)
        return [_from_mongo(x) for x in items]
    # Admin: opzionalmente filtra per docente_id (clienti associati)
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
    materia_ids = list({i.get("materia_id") for i in items if i.get("materia_id")})
    clienti = {c["_id"]: c async for c in db.clienti.find({"_id": {"$in": cliente_ids}})}
    docenti = {u["_id"]: u async for u in db.users.find({"_id": {"$in": docente_ids}})}
    materie = {}
    if materia_ids:
        materie = {m["_id"]: m async for m in db.materie.find({"_id": {"$in": materia_ids}})}
    out = []
    for it in items:
        d = _from_mongo(it)
        c = clienti.get(it["cliente_id"])
        u = docenti.get(it["docente_id"])
        d["cliente_nome"] = f"{c['nome']} {c['cognome']}" if c else None
        d["docente_nome"] = f"{u['nome']} {u['cognome']}" if u else None
        mid = it.get("materia_id")
        d["materia_descrizione"] = materie.get(mid, {}).get("descrizione") if mid else None
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
    # Check ferie/eccezioni
    blocked = await _is_blocked_by_eccezione(docente_id=docente_id, studio_id=sid, data_iso=body.data, dal=body.dal, al=body.al)
    if blocked:
        motivo = blocked.get("motivo") or "ferie"
        raise HTTPException(status_code=409, detail=f"Il docente non è disponibile in questa data ({motivo})")

    doc = {
        "_id": new_id(),
        "studio_id": sid,
        "docente_id": docente_id,
        "cliente_id": body.cliente_id,
        "data": body.data,
        "dal": body.dal,
        "al": body.al,
        "note": body.note,
        "materia_id": body.materia_id,
        "stato": body.stato,
        "created_at": now_utc().isoformat(),
    }
    await db.appuntamenti.insert_one(doc)
    hydrated = await _hydrate_appuntamenti([doc])
    # Invia email di conferma al cliente (non bloccante)
    try:
        if cliente.get("email"):
            studio_doc = await db.studios.find_one({"_id": sid})
            materia_descr = None
            if body.materia_id:
                m = await db.materie.find_one({"_id": body.materia_id, "studio_id": sid})
                materia_descr = (m or {}).get("descrizione")
            await send_appointment_email(
                cliente_email=cliente["email"],
                cliente_nome=cliente.get("nome", ""),
                cliente_cognome=cliente.get("cognome", ""),
                docente_nome=docente.get("nome", ""),
                docente_cognome=docente.get("cognome", ""),
                studio_nome=(studio_doc or {}).get("nome", "Prenotika"),
                studio_sede=(studio_doc or {}).get("sede"),
                studio_email=(studio_doc or {}).get("email"),
                data_iso=body.data,
                dal=body.dal,
                al=body.al,
                materia=materia_descr,
                note=body.note,
            )
    except Exception as _email_err:
        logger.warning(f"Email conferma appuntamento singolo fallita: {_email_err}")
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
async def delete_appuntamento(app_id: str, user: dict = Depends(require_role("admin"))):
    sid = _scope_studio_id(user)
    target = await db.appuntamenti.find_one({"_id": app_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    await db.appuntamenti.delete_one({"_id": app_id})
    # Invia email di disdetta al cliente (non bloccante)
    try:
        cliente = await db.clienti.find_one({"_id": target["cliente_id"]}) if target.get("cliente_id") else None
        docente = await db.users.find_one({"_id": target["docente_id"]}) if target.get("docente_id") else None
        studio_doc = await db.studios.find_one({"_id": sid})
        if cliente and cliente.get("email") and docente:
            materia_descr = None
            if target.get("materia_id"):
                m = await db.materie.find_one({"_id": target["materia_id"], "studio_id": sid})
                materia_descr = (m or {}).get("descrizione")
            from email_service import send_cancellation_email
            await send_cancellation_email(
                cliente_email=cliente["email"],
                cliente_nome=cliente.get("nome", ""),
                cliente_cognome=cliente.get("cognome", ""),
                docente_nome=docente.get("nome", ""),
                docente_cognome=docente.get("cognome", ""),
                studio_nome=(studio_doc or {}).get("nome", "Prenotika"),
                studio_sede=(studio_doc or {}).get("sede"),
                studio_email=(studio_doc or {}).get("email"),
                data_iso=target["data"],
                dal=target["dal"],
                al=target["al"],
                materia=materia_descr,
                note=target.get("note"),
            )
    except Exception as _email_err:
        logger.warning(f"Email disdetta fallita: {_email_err}")
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
# Leads pubblici (landing page contact form)
# -----------------------------------------------------------------------------
@api.post("/leads", status_code=201)
async def create_lead(body: LeadCreate):
    doc = {
        "_id": str(uuid.uuid4()),
        "nome": body.nome.strip(),
        "email": body.email,
        "telefono": (body.telefono or "").strip() or None,
        "tipologia": body.tipologia,
        "studio": (body.studio or "").strip() or None,
        "messaggio": (body.messaggio or "").strip() or None,
        "piano_interesse": (body.piano_interesse or "").strip() or None,
        "created_at": datetime.now(timezone.utc),
        "status": "new",
    }
    await db.leads.insert_one(doc)
    try:
        from email_service import send_lead_notification
        await send_lead_notification(lead={**doc, "id": doc["_id"]})
    except Exception as e:
        logger.warning(f"Notifica lead fallita: {e}")
    return {"ok": True, "id": doc["_id"]}

class LeadUpdate(BaseModel):
    status: Optional[Literal["new", "contacted", "converted", "closed"]] = None
    notes: Optional[str] = None

@api.get("/leads")
async def list_leads(_: dict = Depends(require_role("super_admin"))):
    items = await db.leads.find({}).sort([("created_at", -1)]).to_list(500)
    return [_from_mongo(x) for x in items]

@api.get("/leads/count")
async def count_leads(status: Optional[str] = None, _: dict = Depends(require_role("super_admin"))):
    q = {"status": status} if status else {}
    n = await db.leads.count_documents(q)
    return {"count": n, "status": status}

@api.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, body: LeadUpdate, _: dict = Depends(require_role("super_admin"))):
    target = await db.leads.find_one({"_id": lead_id})
    if not target:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        await db.leads.update_one({"_id": lead_id}, {"$set": updates})
    fresh = await db.leads.find_one({"_id": lead_id})
    return _from_mongo(fresh)

@api.delete("/leads/{lead_id}", status_code=204)
async def delete_lead(lead_id: str, _: dict = Depends(require_role("super_admin"))):
    await db.leads.delete_one({"_id": lead_id})
    return

# -----------------------------------------------------------------------------
# Eccezioni / ferie professionista
# -----------------------------------------------------------------------------
def _target_docente_id_for_eccezione(user: dict, requested: Optional[str]) -> str:
    if user["role"] == "docente":
        return user["id"]
    if not requested:
        raise HTTPException(status_code=422, detail="docente_id richiesto per admin")
    return requested

@api.get("/eccezioni", response_model=List[Eccezione])
async def list_eccezioni(docente_id: Optional[str] = None, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    q = {"studio_id": sid}
    if user["role"] == "docente":
        q["docente_id"] = user["id"]
    elif docente_id:
        q["docente_id"] = docente_id
    items = await db.eccezioni.find(q).sort([("data_inizio", 1)]).to_list(500)
    return [_from_mongo(x) for x in items]

@api.post("/eccezioni", response_model=Eccezione, status_code=201)
async def create_eccezione(body: EccezioneCreate, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    target = _target_docente_id_for_eccezione(user, body.docente_id)
    # Valida range
    if body.data_fine < body.data_inizio:
        raise HTTPException(status_code=422, detail="data_fine deve essere >= data_inizio")
    if body.tipo == "personalizzato" and (not body.ora_inizio or not body.ora_fine):
        raise HTTPException(status_code=422, detail="Per tipo 'personalizzato' specificare ora_inizio e ora_fine")
    doc = {
        "_id": str(uuid.uuid4()),
        "studio_id": sid,
        "docente_id": target,
        "data_inizio": body.data_inizio,
        "data_fine": body.data_fine,
        "motivo": (body.motivo or "").strip() or None,
        "tipo": body.tipo,
        "ora_inizio": body.ora_inizio,
        "ora_fine": body.ora_fine,
        "created_at": datetime.now(timezone.utc),
    }
    await db.eccezioni.insert_one(doc)
    return _from_mongo(doc)

@api.delete("/eccezioni/{ecc_id}", status_code=204)
async def delete_eccezione(ecc_id: str, user: dict = Depends(require_role("admin", "docente"))):
    sid = _scope_studio_id(user)
    target = await db.eccezioni.find_one({"_id": ecc_id, "studio_id": sid})
    if not target:
        raise HTTPException(status_code=404, detail="Eccezione non trovata")
    if user["role"] == "docente" and target["docente_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    await db.eccezioni.delete_one({"_id": ecc_id})
    return

async def _is_blocked_by_eccezione(*, docente_id: str, studio_id: str, data_iso: str, dal: str, al: str) -> Optional[dict]:
    """Returns the eccezione that blocks this slot, or None."""
    eccs = await db.eccezioni.find({
        "studio_id": studio_id,
        "docente_id": docente_id,
        "data_inizio": {"$lte": data_iso},
        "data_fine": {"$gte": data_iso},
    }).to_list(50)
    for e in eccs:
        if e.get("tipo") == "chiuso":
            return e
        # personalizzato: blocca solo se gli orari si sovrappongono
        oi, of_ = e.get("ora_inizio"), e.get("ora_fine")
        if oi and of_ and (dal < of_) and (al > oi):
            return e
    return None

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

    # Auto-associate cliente al docente se richiesto (solo per tipologie con associazione)
    studio = await db.studios.find_one({"_id": sid})
    tipologia = (studio or {}).get("tipologia", "centro_studi")
    needs_association = tipologia in ("studio_legale", "studio_medico")
    if body.associa_alunno and needs_association:
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
        blocked = await _is_blocked_by_eccezione(docente_id=docente_id, studio_id=sid, data_iso=s.data, dal=s.dal, al=s.al)
        if blocked:
            skipped.append({"data": s.data, "dal": s.dal, "al": s.al, "motivo": f"Ferie/chiusura ({blocked.get('motivo') or 'non disponibile'})"})
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
            "materia_id": body.materia_id,
            "stato": "confermato",
            "created_at": now_utc().isoformat(),
        }
        await db.appuntamenti.insert_one(doc)
        created.append({"data": s.data, "dal": s.dal, "al": s.al, "id": doc["_id"]})

    # Invia email riepilogativa con ICS multi-evento (non bloccante)
    try:
        if created and cliente.get("email"):
            studio_doc = await db.studios.find_one({"_id": sid})
            materia_descr = None
            if body.materia_id:
                m = await db.materie.find_one({"_id": body.materia_id, "studio_id": sid})
                materia_descr = (m or {}).get("descrizione")
            await send_bulk_appointments_email(
                cliente_email=cliente["email"],
                cliente_nome=cliente.get("nome", ""),
                cliente_cognome=cliente.get("cognome", ""),
                docente_nome=docente.get("nome", ""),
                docente_cognome=docente.get("cognome", ""),
                studio_nome=(studio_doc or {}).get("nome", "Prenotika"),
                studio_sede=(studio_doc or {}).get("sede"),
                studio_email=(studio_doc or {}).get("email"),
                slots=created,
                materia=materia_descr,
                note=body.note,
            )
    except Exception as _email_err:
        logger.warning(f"Email conferma bulk appuntamenti fallita: {_email_err}")

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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.units import mm
import base64 as _b64

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

    # Merge appuntamenti consecutivi stesso cliente, stesso docente, stessa data
    def _merge_consecutive(rows: list[dict]) -> list[dict]:
        if not rows:
            return rows
        # ordina per data, dal
        rows = sorted(rows, key=lambda x: (x["data"], x["dal"]))
        merged = []
        cur = dict(rows[0])
        for nxt in rows[1:]:
            same_key = (
                nxt["data"] == cur["data"]
                and nxt["cliente_id"] == cur["cliente_id"]
                and nxt["stato"] == cur.get("stato")
                and nxt.get("materia_id") == cur.get("materia_id")
                and nxt["dal"] == cur["al"]
            )
            if same_key:
                cur["al"] = nxt["al"]
                # concat note se diverse
                if nxt.get("note") and nxt["note"] != cur.get("note"):
                    cur["note"] = ((cur.get("note") or "") + " | " + nxt["note"]).strip(" |")
            else:
                merged.append(cur)
                cur = dict(nxt)
        merged.append(cur)
        return merged

    for did in list(by_docente.keys()):
        by_docente[did] = _merge_consecutive(by_docente[did])

    # Build PDF
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#0F172A"), fontSize=14, spaceBefore=10, spaceAfter=6)
    small = ParagraphStyle("small", parent=styles["Normal"], textColor=colors.HexColor("#475569"), fontSize=9)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10)

    story = []
    # ---- Carta intestata: logo (sx) + nome + dati anagrafici (dx) ----
    logo_flowable = None
    logo_raw = (studio or {}).get("logo_base64")
    if logo_raw:
        try:
            payload = logo_raw.split(",", 1)[1] if logo_raw.startswith("data:") else logo_raw
            img_bytes = _b64.b64decode(payload)
            from PIL import Image as PILImage
            with PILImage.open(BytesIO(img_bytes)) as _probe:
                _probe.verify()
            img_io = BytesIO(img_bytes)
            img = RLImage(img_io)
            iw, ih = img.imageWidth, img.imageHeight
            target_h = 24 * mm
            ratio = target_h / float(ih) if ih else 1.0
            img.drawHeight = target_h
            img.drawWidth = min(40 * mm, iw * ratio)
            img.hAlign = "LEFT"
            logo_flowable = img
        except Exception as _e:
            logger.warning(f"Logo studio non valido, ignorato: {_e}")

    # Costruisce il blocco anagrafica come Paragraph multilinea
    studio_d = studio or {}
    anagrafica_lines = []
    if studio_d.get("sede"):
        anagrafica_lines.append(studio_d["sede"])
    contact_bits = []
    if studio_d.get("telefono"):
        contact_bits.append(f"Tel. {studio_d['telefono']}")
    if studio_d.get("email"):
        contact_bits.append(studio_d["email"])
    if contact_bits:
        anagrafica_lines.append(" • ".join(contact_bits))
    if studio_d.get("piva"):
        anagrafica_lines.append(f"P.IVA {studio_d['piva']}")

    head_name_style = ParagraphStyle("hn", parent=styles["Heading1"], textColor=colors.HexColor("#7C3AED"), fontSize=18, spaceAfter=2, leading=22)
    head_anag_style = ParagraphStyle("ha", parent=styles["Normal"], textColor=colors.HexColor("#475569"), fontSize=9, leading=12)

    right_block = [Paragraph(studio_nome, head_name_style)]
    if anagrafica_lines:
        right_block.append(Paragraph("<br/>".join(
            x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for x in anagrafica_lines
        ), head_anag_style))

    if logo_flowable is not None:
        header_tbl = Table(
            [[logo_flowable, right_block]],
            colWidths=[45 * mm, 135 * mm],
        )
        header_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_tbl)
    else:
        for p in right_block:
            story.append(p)
    # Linea separatrice
    sep = Table([[""]], colWidths=[180 * mm], rowHeights=[0.6])
    sep.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.HexColor("#7C3AED"))]))
    story.append(Spacer(1, 4))
    story.append(sep)
    story.append(Spacer(1, 6))

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
            data_rows = [["Data", "Giorno", "Dalle", "Alle", "Cliente", "Materia", "Stato", "Note"]]
            for a in list_d:
                dt = date.fromisoformat(a["data"])
                data_rows.append([
                    dt.strftime("%d/%m/%Y"),
                    _GIORNI_IT[dt.weekday()],
                    a["dal"],
                    a["al"],
                    a.get("cliente_nome") or "—",
                    a.get("materia_descrizione") or "—",
                    a.get("stato", "confermato"),
                    (a.get("note") or "")[:60],
                ])
            tbl = Table(data_rows, colWidths=[22*mm, 22*mm, 13*mm, 13*mm, 42*mm, 28*mm, 20*mm, 24*mm], repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (3, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
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

    # Sezione "Comunicazioni" del centro (in calce al report)
    comunicazioni = (studio or {}).get("comunicazioni")
    if comunicazioni and comunicazioni.strip():
        story.append(Spacer(1, 14))
        com_h = ParagraphStyle("com_h", parent=styles["Heading3"], textColor=colors.HexColor("#7C3AED"), fontSize=12, spaceAfter=4)
        com_body = ParagraphStyle("com_body", parent=styles["Normal"], fontSize=9.5, textColor=colors.HexColor("#0F172A"), leading=13)
        story.append(Paragraph("Comunicazioni del centro", com_h))
        # converte newline in <br/>
        text_html = (comunicazioni.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"))
        story.append(Paragraph(text_html, com_body))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generato il {now_utc().strftime('%d/%m/%Y %H:%M')} UTC — Prenotika SaaS",
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
    return {"app": "Prenotika SaaS", "status": "ok", "time": now_utc().isoformat()}

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
    await db.eccezioni.create_index([("studio_id", 1), ("docente_id", 1), ("data_inizio", 1)])
    await db.leads.create_index([("created_at", -1)])
    await db.leads.create_index("status")
    await db.password_resets.create_index("token", unique=True)
    await db.password_resets.create_index("expires_at")

async def seed_super_admin():
    """Seed idempotente del super_admin (opzionale).

    - Se le env SUPER_ADMIN_EMAIL / SUPER_ADMIN_PASSWORD NON sono impostate,
      il seed viene skippato (in produzione l'utente super_admin esiste già in DB).
    - Se sono impostate, il super_admin viene creato o la password aggiornata.
    """
    super_email = os.environ.get("SUPER_ADMIN_EMAIL")
    super_password = os.environ.get("SUPER_ADMIN_PASSWORD")
    if not super_email or not super_password:
        logger.info("SUPER_ADMIN_* non impostate: skip seed super_admin")
    else:
        super_email = super_email.lower().strip()
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

    # Patch retro-compatibilità sui documenti pre-esistenti (safe in produzione)
    await db.studios.update_many({"tipologia": {"$exists": False}}, {"$set": {"tipologia": "centro_studi"}})
    await db.studios.update_many({"plan": {"$exists": False}}, {"$set": {"plan": "free"}})


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_super_admin()
    try:
        from reminder_scheduler import start_reminder_scheduler
        start_reminder_scheduler(db)
    except Exception as e:
        logger.warning(f"Impossibile avviare reminder scheduler: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    try:
        from reminder_scheduler import shutdown_reminder_scheduler
        shutdown_reminder_scheduler()
    except Exception:
        pass
    client.close()


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_super_admin()
    try:
        from reminder_scheduler import start_reminder_scheduler
        start_reminder_scheduler(db)
    except Exception as e:
        logger.warning(f"Impossibile avviare reminder scheduler: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    try:
        from reminder_scheduler import shutdown_reminder_scheduler
        shutdown_reminder_scheduler()
    except Exception:
        pass
    client.close()
