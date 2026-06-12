"""Iter 7 backend tests: PDF report endpoint /api/reports/appuntamenti.pdf"""
import os
from datetime import date
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://timeslot-manager-23.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login("admin@demo.it", "Admin123!")


@pytest.fixture(scope="module")
def docente_token():
    return _login("docente@demo.it", "Docente123!")


@pytest.fixture(scope="module")
def super_token():
    return _login("superadmin@eligehub.it", "SuperAdmin123!")


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# --- Health checks ---
def test_root_ok():
    r = requests.get(f"{API}/", timeout=15)
    assert r.status_code == 200


# --- PDF generation ---
def test_pdf_week_no_filter(admin_token):
    r = requests.get(f"{API}/reports/appuntamenti.pdf", params={"period": "week"}, headers=_h(admin_token), timeout=60)
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:4] == b"%PDF", f"magic bytes mismatch, got {r.content[:8]!r}"


def test_pdf_day_filename(admin_token):
    target_date = "2026-06-19"
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "day", "data": target_date},
        headers=_h(admin_token),
        timeout=60,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    cd = r.headers.get("content-disposition", "")
    assert f"appuntamenti-day-{target_date}.pdf" in cd, cd


def test_pdf_month_label(admin_token):
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "month", "data": "2026-06-15"},
        headers=_h(admin_token),
        timeout=60,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    # filename uses first day of month
    cd = r.headers.get("content-disposition", "")
    assert "appuntamenti-month-2026-06-01.pdf" in cd, cd
    # 'June 2026' should be present in PDF text (basic substring match in raw bytes)
    # PDF content can be compressed, so we check loosely (may be missing in compressed streams).
    # We don't fail if not found; only warn via assertion on header above.


def test_pdf_docente_filter(admin_token):
    # Find Marco Bianchi id
    docs = requests.get(f"{API}/docenti", headers=_h(admin_token), timeout=15).json()
    marco = next((d for d in docs if d["email"] == "docente@demo.it"), None)
    assert marco, "Marco Bianchi docente not found"
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "week", "docente_id": marco["id"]},
        headers=_h(admin_token),
        timeout=60,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_pdf_docente_id_not_found(admin_token):
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "week", "docente_id": "non-existent-id"},
        headers=_h(admin_token),
        timeout=30,
    )
    assert r.status_code == 404, r.text


def test_pdf_docente_role_ignores_docente_id(docente_token, admin_token):
    # use admin to fetch other docenti, pass another id; backend must still scope to logged-in docente
    docs = requests.get(f"{API}/docenti", headers=_h(admin_token), timeout=15).json()
    other = next((d for d in docs if d["email"] != "docente@demo.it"), None)
    other_id = other["id"] if other else "anything"
    r = requests.get(
        f"{API}/reports/appuntamenti.pdf",
        params={"period": "week", "docente_id": other_id},
        headers=_h(docente_token),
        timeout=60,
    )
    # Must succeed because backend overrides docente_id with own id
    assert r.status_code == 200, r.text
    assert r.content[:4] == b"%PDF"


def test_pdf_super_admin_forbidden(super_token):
    r = requests.get(f"{API}/reports/appuntamenti.pdf", params={"period": "week"}, headers=_h(super_token), timeout=30)
    assert r.status_code == 403, r.text


def test_pdf_invalid_period(admin_token):
    r = requests.get(f"{API}/reports/appuntamenti.pdf", params={"period": "year"}, headers=_h(admin_token), timeout=30)
    assert r.status_code == 400, r.text


# --- Regression: still working iter1-6 APIs ---
def test_regression_dashboard(admin_token):
    r = requests.get(f"{API}/dashboard/stats", headers=_h(admin_token), timeout=15)
    assert r.status_code == 200
    data = r.json()
    for k in ["totale_clienti", "totale_docenti", "appuntamenti_oggi", "appuntamenti_settimana"]:
        assert k in data


def test_regression_disponibilita(admin_token):
    docs = requests.get(f"{API}/docenti", headers=_h(admin_token), timeout=15).json()
    marco = next((d for d in docs if d["email"] == "docente@demo.it"), docs[0])
    r = requests.get(f"{API}/disponibilita", params={"docente_id": marco["id"], "data": "2026-06-15"}, headers=_h(admin_token), timeout=15)
    assert r.status_code == 200
    assert "slots" in r.json()
