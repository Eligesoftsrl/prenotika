"""
Iter 9: Multi-vertical (centro_studi / studio_legale / studio_medico) backend tests.
- Seed demo studios + login per tipologia
- GET /api/clienti scoping per tipologia
- POST /api/appuntamenti/bulk associazione condizionale
- POST /api/appuntamenti + bulk con materia_id, hydration materia_descrizione
- Report PDF: colonna Materia, merge non unisce materia diversa
- POST /api/studios con tipologia (super_admin)
"""
import os
import io
import pytest
import requests
from datetime import date, timedelta

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://timeslot-manager-23.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

CREDS = {
    "super":  ("superadmin@eligehub.it", "SuperAdmin123!"),
    "admin_cs": ("admin@demo.it", "Admin123!"),
    "doc_cs":   ("docente@demo.it", "Docente123!"),
    "admin_lg": ("admin@legale.it", "Admin123!"),
    "avv":      ("avv@legale.it", "Avv123!"),
    "admin_md": ("admin@medico.it", "Admin123!"),
    "med":      ("med@medico.it", "Med123!"),
}


def _login(key):
    email, pwd = CREDS[key]
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=30)
    assert r.status_code == 200, f"login {key} -> {r.status_code} {r.text}"
    j = r.json()
    return j["access_token"], j


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def tokens():
    return {k: _login(k) for k in CREDS}


# ---------- 1. Seed: 3 studios with correct tipologia ----------
def test_seed_three_studios_tipologia(tokens):
    expected = {
        "admin_cs": "centro_studi",
        "admin_lg": "studio_legale",
        "admin_md": "studio_medico",
    }
    for key, tip in expected.items():
        _, payload = tokens[key]
        assert payload["studio"]["tipologia"] == tip, f"{key} tipologia mismatch"
        assert payload["user"]["role"] == "admin"


# ---------- 2. GET /api/clienti centro_studi: docente vede tutti ----------
def test_clienti_centro_studi_docente_sees_all(tokens):
    tok_admin, _ = tokens["admin_cs"]
    tok_doc, _ = tokens["doc_cs"]
    r_admin = requests.get(f"{API}/clienti", headers=_hdr(tok_admin), timeout=30)
    r_doc = requests.get(f"{API}/clienti", headers=_hdr(tok_doc), timeout=30)
    assert r_admin.status_code == 200 and r_doc.status_code == 200
    admin_ids = sorted([c["id"] for c in r_admin.json()])
    doc_ids = sorted([c["id"] for c in r_doc.json()])
    assert len(admin_ids) >= 2
    assert admin_ids == doc_ids, "centro_studi: docente deve vedere stesso pool di admin"


# ---------- 3. GET /api/clienti studio_legale: avvocato vede solo associati ----------
def test_clienti_legale_avvocato_only_associated(tokens):
    tok_admin, _ = tokens["admin_lg"]
    tok_avv, _ = tokens["avv"]
    # Avvocato vede 1 cliente (Mario Bianchi)
    r_avv = requests.get(f"{API}/clienti", headers=_hdr(tok_avv), timeout=30)
    assert r_avv.status_code == 200
    avv_list = r_avv.json()
    assert len(avv_list) == 1, f"avvocato dovrebbe vedere 1, vede {len(avv_list)}"
    assert avv_list[0]["cognome"] == "Bianchi"

    # Admin crea un nuovo cliente non associato (TEST_)
    r_new = requests.post(f"{API}/clienti", headers=_hdr(tok_admin),
                          json={"nome": "TEST_Iter9", "cognome": "NonAssociato"}, timeout=30)
    assert r_new.status_code == 201
    new_id = r_new.json()["id"]
    try:
        r_admin = requests.get(f"{API}/clienti", headers=_hdr(tok_admin), timeout=30)
        admin_ids = [c["id"] for c in r_admin.json()]
        assert new_id in admin_ids
        # Avvocato NON vede il nuovo cliente non associato
        r_avv2 = requests.get(f"{API}/clienti", headers=_hdr(tok_avv), timeout=30)
        avv_ids = [c["id"] for c in r_avv2.json()]
        assert new_id not in avv_ids
        assert len(avv_ids) == 1
    finally:
        requests.delete(f"{API}/clienti/{new_id}", headers=_hdr(tok_admin), timeout=30)


# ---------- 4. GET /api/clienti studio_medico: medico vede solo pazienti ----------
def test_clienti_medico_only_associated(tokens):
    tok_med, _ = tokens["med"]
    r = requests.get(f"{API}/clienti", headers=_hdr(tok_med), timeout=30)
    assert r.status_code == 200
    lst = r.json()
    assert len(lst) == 1
    assert lst[0]["cognome"] == "Verdi"


# ---------- 5. POST /api/appuntamenti/bulk in centro_studi NON crea associazione ----------
def test_bulk_centro_studi_no_auto_association(tokens):
    tok_admin, payload_admin = tokens["admin_cs"]
    sid = payload_admin["studio"]["id"]
    # Get docente_id
    r_doc = requests.get(f"{API}/docenti", headers=_hdr(tok_admin), timeout=30)
    assert r_doc.status_code == 200
    docente_id = r_doc.json()[0]["id"]

    # Creo nuovo cliente TEST_, non associato
    r_c = requests.post(f"{API}/clienti", headers=_hdr(tok_admin),
                        json={"nome": "TEST_NonAssoc", "cognome": "CS"}, timeout=30)
    cli_id = r_c.json()["id"]

    fut = (date.today() + timedelta(days=200)).isoformat()
    appt_ids = []
    try:
        r_bulk = requests.post(f"{API}/appuntamenti/bulk", headers=_hdr(tok_admin), json={
            "docente_id": docente_id,
            "cliente_id": cli_id,
            "slots": [{"data": fut, "dal": "09:00", "al": "10:00"}],
            "associa_alunno": True,
        }, timeout=30)
        assert r_bulk.status_code in (200, 201), r_bulk.text
        for c in r_bulk.json().get("created", []):
            appt_ids.append(c["id"])
        # Verifica che il cliente NON sia stato associato (docente vede ancora tutti i clienti
        # ma in centro_studi non c'è docente_clienti link creato).
        # Check via admin con filter docente_id
        r_link = requests.get(f"{API}/clienti?docente_id={docente_id}", headers=_hdr(tok_admin), timeout=30)
        # Nel centro_studi list_clienti ignora docente_id e ritorna tutti -- testiamo via DB indiretto:
        # Se l'admin filtra con docente_id (ramo admin in list_clienti), ma per centro_studi ramo precedente intercetta
        # Quindi controlliamo: il nuovo cliente NON deve essere in lista associati. Usiamo altro endpoint:
        # /api/docenti/{id}/alunni
        r_alunni = requests.get(f"{API}/docenti/{docente_id}/alunni", headers=_hdr(tok_admin), timeout=30)
        if r_alunni.status_code == 200:
            alunni_ids = [a["id"] for a in r_alunni.json()]
            assert cli_id not in alunni_ids, "In centro_studi non deve creare associazione"
    finally:
        for aid in appt_ids:
            requests.delete(f"{API}/appuntamenti/{aid}", headers=_hdr(tok_admin), timeout=30)
        requests.delete(f"{API}/clienti/{cli_id}", headers=_hdr(tok_admin), timeout=30)


def test_bulk_studio_legale_creates_association(tokens):
    tok_admin, _ = tokens["admin_lg"]
    r_doc = requests.get(f"{API}/docenti", headers=_hdr(tok_admin), timeout=30)
    docente_id = r_doc.json()[0]["id"]

    r_c = requests.post(f"{API}/clienti", headers=_hdr(tok_admin),
                        json={"nome": "TEST_Auto", "cognome": "Assoc"}, timeout=30)
    cli_id = r_c.json()["id"]

    fut = (date.today() + timedelta(days=201)).isoformat()
    appt_ids = []
    try:
        r_bulk = requests.post(f"{API}/appuntamenti/bulk", headers=_hdr(tok_admin), json={
            "docente_id": docente_id, "cliente_id": cli_id,
            "slots": [{"data": fut, "dal": "10:00", "al": "11:00"}],
            "associa_alunno": True,
        }, timeout=30)
        assert r_bulk.status_code in (200, 201)
        for c in r_bulk.json().get("created", []):
            appt_ids.append(c["id"])
        r_alunni = requests.get(f"{API}/docenti/{docente_id}/alunni", headers=_hdr(tok_admin), timeout=30)
        assert r_alunni.status_code == 200
        alunni_ids = [a["id"] for a in r_alunni.json()]
        assert cli_id in alunni_ids, "studio_legale deve creare associazione"
    finally:
        for aid in appt_ids:
            requests.delete(f"{API}/appuntamenti/{aid}", headers=_hdr(tok_admin), timeout=30)
        requests.delete(f"{API}/docenti/{docente_id}/alunni/{cli_id}", headers=_hdr(tok_admin), timeout=30)
        requests.delete(f"{API}/clienti/{cli_id}", headers=_hdr(tok_admin), timeout=30)


def _ensure_docente_materie(tok, docente_id, n=2):
    """Garantisce che il docente abbia almeno n materie associate.
    Restituisce la lista di materie associate."""
    r_mat = requests.get(f"{API}/docenti/{docente_id}/materie", headers=_hdr(tok), timeout=30)
    materie = r_mat.json() if r_mat.status_code == 200 else []
    if len(materie) >= n:
        return materie
    r_all = requests.get(f"{API}/materie", headers=_hdr(tok), timeout=30)
    pool = r_all.json()
    for m in pool:
        if any(mm["id"] == m["id"] for mm in materie):
            continue
        requests.post(f"{API}/docenti/{docente_id}/materie/{m['id']}", headers=_hdr(tok), timeout=30)
        materie.append(m)
        if len(materie) >= n:
            break
    return materie


# ---------- 6. POST /api/appuntamenti accepts materia_id, GET hydrates ----------
def test_appuntamento_materia_id_hydration(tokens):
    tok, payload = tokens["admin_cs"]
    r_doc = requests.get(f"{API}/docenti", headers=_hdr(tok), timeout=30)
    docente_id = r_doc.json()[0]["id"]
    r_cli = requests.get(f"{API}/clienti", headers=_hdr(tok), timeout=30)
    cliente_id = r_cli.json()[0]["id"]
    materie = _ensure_docente_materie(tok, docente_id, 1)
    assert len(materie) >= 1, "Setup: impossibile associare materia al docente"
    materia = materie[0]
    materia_id = materia["id"]
    materia_desc = materia["descrizione"]

    fut = (date.today() + timedelta(days=210)).isoformat()
    r_app = requests.post(f"{API}/appuntamenti", headers=_hdr(tok), json={
        "docente_id": docente_id, "cliente_id": cliente_id,
        "data": fut, "dal": "11:00", "al": "12:00",
        "materia_id": materia_id,
    }, timeout=30)
    assert r_app.status_code in (200, 201), r_app.text
    appt_id = r_app.json()["id"]
    try:
        r_list = requests.get(f"{API}/appuntamenti?dal={fut}&al={fut}", headers=_hdr(tok), timeout=30)
        assert r_list.status_code == 200
        found = [a for a in r_list.json() if a["id"] == appt_id]
        assert found
        a = found[0]
        assert a.get("materia_id") == materia_id
        assert a.get("materia_descrizione") == materia_desc
    finally:
        requests.delete(f"{API}/appuntamenti/{appt_id}", headers=_hdr(tok), timeout=30)


def test_bulk_materia_id_applied_to_all(tokens):
    tok, _ = tokens["admin_cs"]
    r_doc = requests.get(f"{API}/docenti", headers=_hdr(tok), timeout=30)
    docente_id = r_doc.json()[0]["id"]
    r_cli = requests.get(f"{API}/clienti", headers=_hdr(tok), timeout=30)
    cliente_id = r_cli.json()[0]["id"]
    materie = _ensure_docente_materie(tok, docente_id, 1)
    materia_id = materie[0]["id"]

    fut = (date.today() + timedelta(days=215)).isoformat()
    r_bulk = requests.post(f"{API}/appuntamenti/bulk", headers=_hdr(tok), json={
        "docente_id": docente_id, "cliente_id": cliente_id,
        "slots": [
            {"data": fut, "dal": "14:00", "al": "15:00"},
            {"data": fut, "dal": "15:00", "al": "16:00"},
            {"data": fut, "dal": "16:00", "al": "17:00"},
        ],
        "materia_id": materia_id,
    }, timeout=30)
    assert r_bulk.status_code in (200, 201)
    ids = [c["id"] for c in r_bulk.json().get("created", [])]
    assert len(ids) == 3
    try:
        r_list = requests.get(f"{API}/appuntamenti?dal={fut}&al={fut}", headers=_hdr(tok), timeout=30)
        for a in r_list.json():
            if a["id"] in ids:
                assert a.get("materia_id") == materia_id
    finally:
        for aid in ids:
            requests.delete(f"{API}/appuntamenti/{aid}", headers=_hdr(tok), timeout=30)


# ---------- 7. Report PDF: 8 colonne incl. Materia ----------
def test_pdf_has_materia_column(tokens):
    tok, _ = tokens["admin_cs"]
    r_doc = requests.get(f"{API}/docenti", headers=_hdr(tok), timeout=30)
    docente_id = r_doc.json()[0]["id"]
    r_cli = requests.get(f"{API}/clienti", headers=_hdr(tok), timeout=30)
    cliente_id = r_cli.json()[0]["id"]
    materie = _ensure_docente_materie(tok, docente_id, 1)
    materia_id = materie[0]["id"]
    materia_desc = materie[0]["descrizione"]

    fut = (date.today() + timedelta(days=220)).isoformat()
    # 1 con materia, 1 senza materia, non contigui (gap)
    r1 = requests.post(f"{API}/appuntamenti", headers=_hdr(tok), json={
        "docente_id": docente_id, "cliente_id": cliente_id,
        "data": fut, "dal": "09:00", "al": "10:00", "materia_id": materia_id,
    }, timeout=30)
    assert r1.status_code in (200, 201), r1.text
    r2 = requests.post(f"{API}/appuntamenti", headers=_hdr(tok), json={
        "docente_id": docente_id, "cliente_id": cliente_id,
        "data": fut, "dal": "11:00", "al": "12:00",
    }, timeout=30)
    assert r2.status_code in (200, 201)
    a1 = r1.json()["id"]; a2 = r2.json()["id"]
    try:
        r_pdf = requests.get(f"{API}/reports/appuntamenti.pdf?period=day&data={fut}",
                             headers=_hdr(tok), timeout=60)
        assert r_pdf.status_code == 200
        assert r_pdf.headers.get("content-type", "").startswith("application/pdf")
        content = r_pdf.content
        assert len(content) > 1000
        # extract text via pdfminer/pypdf if available — fallback string search
        try:
            from pypdf import PdfReader
            txt = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(content)).pages)
        except Exception:
            txt = content.decode("latin-1", errors="ignore")
        assert "Materia" in txt, "PDF deve avere colonna 'Materia'"
        assert materia_desc in txt, f"PDF deve contenere descrizione materia '{materia_desc}'"
    finally:
        requests.delete(f"{API}/appuntamenti/{a1}", headers=_hdr(tok), timeout=30)
        requests.delete(f"{API}/appuntamenti/{a2}", headers=_hdr(tok), timeout=30)


# ---------- 8. PDF merge non unisce materie diverse ----------
def test_pdf_merge_skips_different_materia(tokens):
    tok, _ = tokens["admin_cs"]
    r_doc = requests.get(f"{API}/docenti", headers=_hdr(tok), timeout=30)
    docente_id = r_doc.json()[0]["id"]
    r_cli = requests.get(f"{API}/clienti", headers=_hdr(tok), timeout=30)
    cliente_id = r_cli.json()[0]["id"]
    materie = _ensure_docente_materie(tok, docente_id, 2)
    if len(materie) < 2:
        pytest.skip("Servono 2 materie associate al docente")
    m1 = materie[0]; m2 = materie[1]

    fut = (date.today() + timedelta(days=225)).isoformat()
    # 2 contigui stesso cliente, materia diversa -> NON deve unire
    r1 = requests.post(f"{API}/appuntamenti", headers=_hdr(tok), json={
        "docente_id": docente_id, "cliente_id": cliente_id,
        "data": fut, "dal": "09:00", "al": "10:00", "materia_id": m1["id"],
    }, timeout=30)
    r2 = requests.post(f"{API}/appuntamenti", headers=_hdr(tok), json={
        "docente_id": docente_id, "cliente_id": cliente_id,
        "data": fut, "dal": "10:00", "al": "11:00", "materia_id": m2["id"],
    }, timeout=30)
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)
    a1 = r1.json()["id"]; a2 = r2.json()["id"]
    try:
        r_pdf = requests.get(f"{API}/reports/appuntamenti.pdf?period=day&data={fut}",
                             headers=_hdr(tok), timeout=60)
        assert r_pdf.status_code == 200
        try:
            from pypdf import PdfReader
            txt = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(r_pdf.content)).pages)
        except Exception:
            txt = r_pdf.content.decode("latin-1", errors="ignore")
        # Entrambe le materie devono apparire come righe distinte
        assert m1["descrizione"] in txt
        assert m2["descrizione"] in txt
        # Verifica che non ci sia una riga 09:00 -> 11:00 (merge sarebbe sbagliato)
        # Cerchiamo entrambi gli orari di fine
        assert "10:00" in txt and "11:00" in txt
    finally:
        requests.delete(f"{API}/appuntamenti/{a1}", headers=_hdr(tok), timeout=30)
        requests.delete(f"{API}/appuntamenti/{a2}", headers=_hdr(tok), timeout=30)


# ---------- 9. POST /api/studios super_admin con tipologia ----------
def test_super_admin_create_studio_tipologia(tokens):
    tok, _ = tokens["super"]
    payload = {
        "nome": "TEST_Iter9_Legale",
        "sede": "Via Test 99",
        "tipologia": "studio_legale",
        "admin_nome": "TestAdmin",
        "admin_cognome": "Iter9",
        "admin_email": "test_iter9_admin@example.com",
        "admin_password": "TempPwd123!",
    }
    r = requests.post(f"{API}/studios", headers=_hdr(tok), json=payload, timeout=30)
    assert r.status_code in (200, 201), r.text
    sid = r.json()["id"]
    try:
        # BUG-check: la response e il DB devono persistere tipologia='studio_legale'
        assert r.json().get("tipologia") == "studio_legale", \
            f"BUG: POST /api/studios non persiste tipologia. Got: {r.json().get('tipologia')}"
        r_list = requests.get(f"{API}/studios", headers=_hdr(tok), timeout=30)
        item = [s for s in r_list.json() if s["id"] == sid][0]
        assert item["tipologia"] == "studio_legale", \
            f"BUG: GET /api/studios returns tipologia={item.get('tipologia')} per studio appena creato"
    finally:
        requests.delete(f"{API}/studios/{sid}", headers=_hdr(tok), timeout=30)
