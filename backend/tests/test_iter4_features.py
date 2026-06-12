"""Iteration 4: materia_ids on POST/PATCH /docenti syncs docente_materie.

Includes regression for:
- PATCH without materia_ids leaves docente_materie unchanged
- PATCH with materia_ids=[] empties associations
- PATCH only base fields / only password works (no materia_ids interference)
- DELETE docente cleans docente_materie (already covered in iter3, light retest)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN = {"email": "admin@demo.it", "password": "Admin123!"}


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def two_materie(admin_token):
    """Create 2 temporary materie, cleanup after module."""
    ids = []
    for desc in ["TEST_Iter4_MatA", "TEST_Iter4_MatB"]:
        # cleanup any leftover from previous run
        ls = requests.get(f"{API}/materie", headers=H(admin_token)).json()
        existing = next((m for m in ls if m["descrizione"] == desc), None)
        if existing:
            requests.delete(f"{API}/materie/{existing['id']}", headers=H(admin_token))
        r = requests.post(f"{API}/materie", headers=H(admin_token),
                          json={"descrizione": desc, "prezzo": 30})
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])
    yield ids
    for mid in ids:
        requests.delete(f"{API}/materie/{mid}", headers=H(admin_token))


def _create_docente(admin_token, email_suffix, materia_ids=None):
    body = {
        "nome": f"TEST_Iter4_{email_suffix}",
        "cognome": "TEST_Doc",
        "email": f"TEST_iter4_{email_suffix}@example.com",
        "password": "Pass1234!",
    }
    if materia_ids is not None:
        body["materia_ids"] = materia_ids
    # cleanup leftover
    ls = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
    existing = next((d for d in ls if d["email"] == body["email"]), None)
    if existing:
        requests.delete(f"{API}/docenti/{existing['id']}", headers=H(admin_token))
    r = requests.post(f"{API}/docenti", headers=H(admin_token), json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


class TestCreateDocenteWithMaterie:
    def test_create_with_2_materia_ids(self, admin_token, two_materie):
        did = _create_docente(admin_token, "create2", materia_ids=two_materie)
        try:
            r = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token))
            assert r.status_code == 200
            got = sorted([m["id"] for m in r.json()])
            assert got == sorted(two_materie), f"Expected {two_materie}, got {got}"
            assert len(r.json()) == 2
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_create_without_materia_ids_has_none(self, admin_token):
        did = _create_docente(admin_token, "create_nomat")
        try:
            r = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token))
            assert r.status_code == 200
            assert r.json() == []
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_create_with_empty_list(self, admin_token):
        did = _create_docente(admin_token, "create_empty", materia_ids=[])
        try:
            r = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token))
            assert r.json() == []
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))


class TestPatchDocenteWithMaterie:
    def test_patch_replaces_associations(self, admin_token, two_materie):
        # start with [A]
        did = _create_docente(admin_token, "patch_replace", materia_ids=[two_materie[0]])
        try:
            # Initial check
            r0 = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert [m["id"] for m in r0] == [two_materie[0]]

            # PATCH with [B] -> should replace
            p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                               json={"materia_ids": [two_materie[1]]})
            assert p.status_code == 200, p.text

            r = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert [m["id"] for m in r] == [two_materie[1]], "PATCH should REPLACE, not add"

            # PATCH with both -> [A, B]
            p2 = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                                json={"materia_ids": two_materie})
            assert p2.status_code == 200
            r2 = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert sorted([m["id"] for m in r2]) == sorted(two_materie)
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_patch_empty_list_clears(self, admin_token, two_materie):
        did = _create_docente(admin_token, "patch_clear", materia_ids=two_materie)
        try:
            r0 = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert len(r0) == 2

            p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                               json={"materia_ids": []})
            assert p.status_code == 200

            r = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert r == [], "Empty list must clear all associations"
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_patch_without_materia_ids_leaves_unchanged(self, admin_token, two_materie):
        """CRITICAL regression: PATCH without materia_ids key must NOT touch associations."""
        did = _create_docente(admin_token, "patch_untouched", materia_ids=two_materie)
        try:
            # PATCH only base field
            p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                               json={"telefono": "+39 555 1234567", "color": "#123456"})
            assert p.status_code == 200, p.text
            data = p.json()
            assert data["telefono"] == "+39 555 1234567"
            assert data["color"] == "#123456"

            # Associations must remain
            r = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert sorted([m["id"] for m in r]) == sorted(two_materie), \
                "PATCH without materia_ids must NOT alter docente_materie"
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_patch_only_password(self, admin_token):
        """Regression: PATCH only password works (no materia_ids interference)."""
        did = _create_docente(admin_token, "patch_pwd")
        try:
            p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                               json={"password": "NewPass1234!"})
            assert p.status_code == 200, p.text

            # Login with new password
            r = requests.post(f"{API}/auth/login", json={
                "email": "TEST_iter4_patch_pwd@example.com",
                "password": "NewPass1234!"
            })
            assert r.status_code == 200, r.text
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_patch_base_fields_no_password(self, admin_token):
        """Regression: PATCH base fields without password works."""
        did = _create_docente(admin_token, "patch_base")
        try:
            p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                               json={"nome": "TEST_Updated", "slot_minuti": 30, "active": True})
            assert p.status_code == 200, p.text
            data = p.json()
            assert data["nome"] == "TEST_Updated"
            assert data["slot_minuti"] == 30
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_patch_password_and_materia_ids_together(self, admin_token, two_materie):
        did = _create_docente(admin_token, "patch_combo")
        try:
            p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token), json={
                "password": "Combo1234!",
                "materia_ids": [two_materie[0]],
                "telefono": "+39 111"
            })
            assert p.status_code == 200, p.text
            # password works
            r = requests.post(f"{API}/auth/login", json={
                "email": "TEST_iter4_patch_combo@example.com",
                "password": "Combo1234!"
            })
            assert r.status_code == 200
            # materie set
            ml = requests.get(f"{API}/docenti/{did}/materie", headers=H(admin_token)).json()
            assert [m["id"] for m in ml] == [two_materie[0]]
        finally:
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))


class TestDeleteCleanup:
    def test_delete_docente_cleans_materie(self, admin_token, two_materie):
        did = _create_docente(admin_token, "delete_clean", materia_ids=two_materie)
        # delete
        requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))
        # Recreate with same email - associations must be empty
        did2 = _create_docente(admin_token, "delete_clean")
        try:
            ls = requests.get(f"{API}/docenti/{did2}/materie", headers=H(admin_token)).json()
            assert ls == []
        finally:
            requests.delete(f"{API}/docenti/{did2}", headers=H(admin_token))


class TestDisponibilitaRegression:
    def test_disponibilita_demo_today(self, admin_token):
        """GET /api/disponibilita returns free slots for demo docente."""
        # find demo docente
        dl = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
        d = [x for x in dl if x["email"] == "docente@demo.it"][0]
        from datetime import date, timedelta
        # Use a Monday in future to be safe
        today = date.today()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        monday = (today + timedelta(days=days_ahead)).isoformat()
        r = requests.get(f"{API}/disponibilita",
                         headers=H(admin_token),
                         params={"docente_id": d["id"], "data": monday})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "slots" in data
        # Demo docente has 09-13 and 15-18 on weekdays, 60-min slots => 7 slots expected
        assert len(data["slots"]) >= 1
        # Check structure
        for s in data["slots"]:
            assert "dal" in s and "al" in s
