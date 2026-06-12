"""Iter 8 backend tests:
- PDF report _merge_consecutive: contigui stesso cliente/docente/data/stato vengono uniti
- non uniti se: stati diversi, gap temporale, clienti diversi
- merge concatena note diverse con ' | '
- regressione PDF day/week/month e role scoping
"""
import os
from datetime import date, timedelta
from io import BytesIO

import pytest
import requests
from pypdf import PdfReader

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://timeslot-manager-23.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"


# --- Auth helpers ---
def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _h(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def admin_session():
    s = _login("admin@demo.it", "Admin123!")
    return s


@pytest.fixture(scope="module")
def admin_token(admin_session):
    return admin_session["access_token"]


@pytest.fixture(scope="module")
def docente_token():
    return _login("docente@demo.it", "Docente123!")["access_token"]


@pytest.fixture(scope="module")
def super_token():
    return _login("superadmin@eligehub.it", "SuperAdmin123!")["access_token"]


@pytest.fixture(scope="module")
def demo_ids(admin_token):
    """Get demo docente & clienti ids for testing."""
    docs = requests.get(f"{API}/docenti", headers=_h(admin_token), timeout=30).json()
    clients = requests.get(f"{API}/clienti", headers=_h(admin_token), timeout=30).json()
    # Normalize id field (API exposes 'id', internal '_id')
    def _id(o):
        return o.get("_id") or o.get("id")
    # Marco Bianchi (slot 60)
    docente = next((d for d in docs if d.get("nome", "").lower().startswith("marco")), docs[0])
    cli1 = next((c for c in clients if c.get("nome", "").lower().startswith("luca")), clients[0])
    cli2 = next(
        (c for c in clients if _id(c) != _id(cli1)),
        clients[1] if len(clients) > 1 else clients[0],
    )
    # Inject normalized id key
    for o in (docente, cli1, cli2):
        o["_id"] = _id(o)
    return {"docente": docente, "cli1": cli1, "cli2": cli2}


# Test data isolation: use future "scratch" dates that demo data doesn't touch
TEST_DATE = (date.today() + timedelta(days=120)).isoformat()
TEST_DATE_2 = (date.today() + timedelta(days=121)).isoformat()
TEST_DATE_3 = (date.today() + timedelta(days=122)).isoformat()
TEST_DATE_4 = (date.today() + timedelta(days=123)).isoformat()
TEST_DATE_5 = (date.today() + timedelta(days=124)).isoformat()


def _create_appt(token, payload):
    r = requests.post(f"{API}/appuntamenti", json=payload, headers=_h(token), timeout=30)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    j["_id"] = j.get("_id") or j.get("id")
    return j


def _delete_appt(token, aid):
    requests.delete(f"{API}/appuntamenti/{aid}", headers=_h(token), timeout=30)


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    out = []
    for p in reader.pages:
        out.append(p.extract_text() or "")
    return "\n".join(out)


def _get_pdf_for_day(token, day_iso, docente_id=None):
    params = {"period": "day", "data": day_iso}
    if docente_id:
        params["docente_id"] = docente_id
    r = requests.get(f"{API}/reports/appuntamenti.pdf", params=params, headers=_h(token), timeout=60)
    assert r.status_code == 200, r.text
    assert r.content[:4] == b"%PDF"
    return r.content


# --- Test 1: 3 contigui stesso cliente/docente/data -> 1 riga merged 09:00-12:00 ---
def test_merge_three_consecutive_same_client(admin_token, demo_ids):
    docente = demo_ids["docente"]
    cli = demo_ids["cli1"]
    created = []
    try:
        for dal, al in [("09:00", "10:00"), ("10:00", "11:00"), ("11:00", "12:00")]:
            a = _create_appt(
                admin_token,
                {
                    "docente_id": docente["_id"],
                    "cliente_id": cli["_id"],
                    "data": TEST_DATE,
                    "dal": dal,
                    "al": al,
                    "stato": "confermato",
                    "note": "",
                },
            )
            created.append(a["_id"])

        content = _get_pdf_for_day(admin_token, TEST_DATE, docente_id=docente["_id"])
        text = _extract_pdf_text(content)
        # After merge: one row 09:00 .. 12:00. Intermediate boundary times 10:00/11:00 should NOT appear as own rows
        assert "09:00" in text, f"09:00 missing in PDF text: {text}"
        assert "12:00" in text, f"12:00 missing in PDF text: {text}"
        # Count occurrences of cliente name -> should be 1 (merged)
        cli_name = f"{cli['nome']} {cli['cognome']}"
        count = text.count(cli_name)
        assert count == 1, f"expected 1 merged row for {cli_name}, got {count} rows. Text:\n{text}"
    finally:
        for aid in created:
            _delete_appt(admin_token, aid)


# --- Test 2: stati diversi NON vengono uniti ---
def test_no_merge_when_stato_differs(admin_token, demo_ids):
    docente = demo_ids["docente"]
    cli = demo_ids["cli1"]
    created = []
    try:
        a1 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli["_id"],
            "data": TEST_DATE_2, "dal": "09:00", "al": "10:00",
            "stato": "confermato", "note": "",
        })
        created.append(a1["_id"])
        a2 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli["_id"],
            "data": TEST_DATE_2, "dal": "10:00", "al": "11:00",
            "stato": "confermato", "note": "",
        })
        created.append(a2["_id"])
        # Update a2 stato to annullato
        r = requests.patch(
            f"{API}/appuntamenti/{a2['_id']}",
            json={"stato": "annullato"},
            headers=_h(admin_token),
            timeout=30,
        )
        assert r.status_code == 200, r.text

        content = _get_pdf_for_day(admin_token, TEST_DATE_2, docente_id=docente["_id"])
        text = _extract_pdf_text(content)
        cli_name = f"{cli['nome']} {cli['cognome']}"
        count = text.count(cli_name)
        assert count == 2, f"expected 2 separate rows (diff stato), got {count}. Text:\n{text}"
        assert "annullato" in text.lower()
    finally:
        for aid in created:
            _delete_appt(admin_token, aid)


# --- Test 3: gap (non contigui) NON uniti ---
def test_no_merge_with_time_gap(admin_token, demo_ids):
    docente = demo_ids["docente"]
    cli = demo_ids["cli1"]
    created = []
    try:
        a1 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli["_id"],
            "data": TEST_DATE_3, "dal": "09:00", "al": "10:00",
            "stato": "confermato", "note": "",
        })
        created.append(a1["_id"])
        a2 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli["_id"],
            "data": TEST_DATE_3, "dal": "11:00", "al": "12:00",
            "stato": "confermato", "note": "",
        })
        created.append(a2["_id"])

        content = _get_pdf_for_day(admin_token, TEST_DATE_3, docente_id=docente["_id"])
        text = _extract_pdf_text(content)
        cli_name = f"{cli['nome']} {cli['cognome']}"
        count = text.count(cli_name)
        assert count == 2, f"expected 2 separate rows (gap), got {count}. Text:\n{text}"
    finally:
        for aid in created:
            _delete_appt(admin_token, aid)


# --- Test 4: clienti diversi -> NON uniti ---
def test_no_merge_different_clients(admin_token, demo_ids):
    docente = demo_ids["docente"]
    cli1 = demo_ids["cli1"]
    cli2 = demo_ids["cli2"]
    if cli1["_id"] == cli2["_id"]:
        pytest.skip("Only one cliente in demo data")
    created = []
    try:
        a1 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli1["_id"],
            "data": TEST_DATE_4, "dal": "09:00", "al": "10:00",
            "stato": "confermato", "note": "",
        })
        created.append(a1["_id"])
        a2 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli2["_id"],
            "data": TEST_DATE_4, "dal": "10:00", "al": "11:00",
            "stato": "confermato", "note": "",
        })
        created.append(a2["_id"])

        content = _get_pdf_for_day(admin_token, TEST_DATE_4, docente_id=docente["_id"])
        text = _extract_pdf_text(content)
        n1 = f"{cli1['nome']} {cli1['cognome']}"
        n2 = f"{cli2['nome']} {cli2['cognome']}"
        assert n1 in text and n2 in text, f"expected both clients in PDF. Text:\n{text}"
    finally:
        for aid in created:
            _delete_appt(admin_token, aid)


# --- Test 5: note diverse -> concatenate con ' | ' ---
def test_merge_concat_notes(admin_token, demo_ids):
    docente = demo_ids["docente"]
    cli = demo_ids["cli1"]
    created = []
    try:
        a1 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli["_id"],
            "data": TEST_DATE_5, "dal": "09:00", "al": "10:00",
            "stato": "confermato", "note": "AAA",
        })
        created.append(a1["_id"])
        a2 = _create_appt(admin_token, {
            "docente_id": docente["_id"], "cliente_id": cli["_id"],
            "data": TEST_DATE_5, "dal": "10:00", "al": "11:00",
            "stato": "confermato", "note": "BBB",
        })
        created.append(a2["_id"])

        content = _get_pdf_for_day(admin_token, TEST_DATE_5, docente_id=docente["_id"])
        text = _extract_pdf_text(content)
        cli_name = f"{cli['nome']} {cli['cognome']}"
        count = text.count(cli_name)
        assert count == 1, f"expected 1 merged row, got {count}. Text:\n{text}"
        # PDF notes column truncates to 60 chars; "AAA | BBB" should be present
        assert "AAA | BBB" in text or ("AAA" in text and "BBB" in text and "|" in text), \
            f"expected concatenated notes 'AAA | BBB' in PDF. Text:\n{text}"
    finally:
        for aid in created:
            _delete_appt(admin_token, aid)


# --- Regressione: status, magic bytes, role scoping ---
def test_regression_pdf_periods_admin(admin_token):
    for period in ("day", "week", "month"):
        r = requests.get(
            f"{API}/reports/appuntamenti.pdf",
            params={"period": period},
            headers=_h(admin_token),
            timeout=60,
        )
        assert r.status_code == 200, f"{period}: {r.text}"
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF"


def test_regression_pdf_docente_role(docente_token):
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "week"},
        headers=_h(docente_token),
        timeout=60,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_regression_pdf_super_admin_forbidden(super_token):
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "week"},
        headers=_h(super_token),
        timeout=60,
    )
    assert r.status_code == 403
