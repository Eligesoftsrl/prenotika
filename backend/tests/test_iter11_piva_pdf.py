"""Iter 11 - Test bug fix PATCH /api/studio (P.IVA con email null/vuota) + header carta intestata PDF."""
import os
import requests
import base64

def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        return None
    return None


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env() or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not configured"
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@demo.it"
ADMIN_PASSWORD = "Admin123!"


def _login():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_get_studio_baseline():
    tok = _login()
    r = requests.get(f"{API}/studio", headers=_h(tok), timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "piva" in data
    assert "email" in data
    assert "logo_base64" in data


def test_patch_piva_only_persists():
    """Bug fix verifica: aggiornare solo P.IVA deve persistere."""
    tok = _login()
    new_piva = "IT99887766554"
    r = requests.patch(f"{API}/studio", headers=_h(tok), json={"piva": new_piva}, timeout=10)
    assert r.status_code == 200, f"PATCH failed: {r.status_code} {r.text}"
    assert r.json().get("piva") == new_piva

    # GET to verify persistence
    g = requests.get(f"{API}/studio", headers=_h(tok), timeout=10)
    assert g.status_code == 200
    assert g.json().get("piva") == new_piva


def test_patch_piva_with_email_null_no_422():
    """Edge case: payload con email=null (come fa frontend dopo fix) + piva deve passare."""
    tok = _login()
    new_piva = "IT11223344556"
    payload = {
        "nome": "Centro Studi Demo",
        "telefono": None,
        "email": None,        # <-- frontend ora invia null, NON ""
        "piva": new_piva,
        "sede": None,
        "comunicazioni": "",  # CLEARABLE: '' = cancella
        "logo_base64": "",    # CLEARABLE
    }
    r = requests.patch(f"{API}/studio", headers=_h(tok), json=payload, timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert body.get("piva") == new_piva

    g = requests.get(f"{API}/studio", headers=_h(tok), timeout=10)
    assert g.json().get("piva") == new_piva


def test_patch_email_empty_string_returns_422():
    """Verifica: backend (EmailStr) rifiuta ancora '' come email. Conferma RCA del bug."""
    tok = _login()
    r = requests.patch(f"{API}/studio", headers=_h(tok), json={"email": "", "piva": "IT00000000000"}, timeout=10)
    # Conferma che '' produce 422 (motivo per cui frontend normalizza '' -> null)
    assert r.status_code == 422, f"Expected 422 (RCA confirm), got {r.status_code}: {r.text}"


# ---- Carta intestata PDF ----

# PNG verde 200x80 (base64) - usato come logo valido
GREEN_PNG_B64 = None


def _make_green_png():
    """Crea PNG 200x80 con rumore (non comprimibile) per superare soglia 2500B."""
    from PIL import Image
    from io import BytesIO
    import random
    random.seed(42)
    img = Image.new("RGB", (200, 80))
    px = img.load()
    for y in range(80):
        for x in range(200):
            px[x, y] = (random.randint(0, 255), random.randint(60, 160), random.randint(0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def test_pdf_with_header_carta_intestata():
    """Set logo + dati studio, scarica PDF e verifica magic bytes + dimensione + XObject Image."""
    tok = _login()
    # Configura studio completo per popolare carta intestata
    logo = _make_green_png()
    payload = {
        "nome": "Centro Studi Demo",
        "sede": "Via Roma 1, Milano",
        "telefono": "+39 02 1234567",
        "email": "info@centrostudi.it",
        "piva": "IT12345678901",
        "logo_base64": logo,
    }
    r = requests.patch(f"{API}/studio", headers=_h(tok), json=payload, timeout=15)
    assert r.status_code == 200, f"setup PATCH failed: {r.status_code} {r.text}"
    assert r.json().get("logo_base64", "").startswith("data:image/png")

    # Scarica PDF
    rp = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        headers=_h(tok),
        params={"period": "week", "data": "2026-02-09"},
        timeout=30,
    )
    assert rp.status_code == 200, f"PDF download failed: {rp.status_code} {rp.text[:300]}"
    content = rp.content
    # Magic bytes
    assert content[:4] == b"%PDF", f"Not a PDF, head={content[:8]!r}"
    # Dimensione con logo embedded > 2500 bytes
    assert len(content) > 2500, f"PDF too small ({len(content)} bytes), logo probably missing"
    # Verifica XObject Image embedded (logo) - tolleriamo entrambe le sintassi
    has_image = (b"/Subtype /Image" in content) or (b"/Subtype/Image" in content)
    assert has_image, "Nessun XObject Image trovato nel PDF (logo non embedded)"


def _decompress_pdf_streams(content: bytes) -> bytes:
    """Estrae e decomprime stream FlateDecode/ASCII85Decode dal PDF per cercare testo."""
    import zlib, base64 as _b64m
    out = bytearray()
    pos = 0
    while True:
        s = content.find(b"stream", pos)
        if s == -1:
            break
        e = content.find(b"endstream", s)
        if e == -1:
            break
        body_start = s + 6
        if content[body_start:body_start+2] in (b"\r\n", b"\n\r"):
            body_start += 2
        elif content[body_start:body_start+1] in (b"\n", b"\r"):
            body_start += 1
        raw = content[body_start:e].rstrip(b"\r\n ")
        # try ASCII85 wrapper "Gat...~>"
        try:
            if raw.endswith(b"~>"):
                ascii85 = _b64m.a85decode(raw, adobe=False)
                try:
                    out += zlib.decompress(ascii85)
                except Exception:
                    out += ascii85
            else:
                out += zlib.decompress(raw)
        except Exception:
            pass
        pos = e + len(b"endstream")
    return bytes(out)


def test_pdf_header_contains_anagrafica_text():
    """Estrae testo dal PDF via pypdf e verifica dati anagrafici nel header."""
    import pypdf
    from io import BytesIO
    tok = _login()
    rp = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        headers=_h(tok),
        params={"period": "week", "data": "2026-02-09"},
        timeout=30,
    )
    assert rp.status_code == 200
    reader = pypdf.PdfReader(BytesIO(rp.content))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages)
    needles = ["Centro Studi Demo", "P.IVA", "Via Roma", "info@centrostudi", "12345678901", "+39 02 1234567"]
    found = [n for n in needles if n in full_text]
    assert len(found) >= 3, f"Solo {found} trovato in PDF text. Full text preview: {full_text[:500]!r}"
    print(f"[anagrafica found]: {found}")
