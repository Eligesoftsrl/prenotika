"""Iteration 3: Materie CRUD, docente_materie N:M, /appuntamenti/bulk endpoint."""
import os
from datetime import date, timedelta

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@demo.it", "password": "Admin123!"}
DOCENTE = {"email": "docente@demo.it", "password": "Docente123!"}


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def docente_token():
    r = requests.post(f"{API}/auth/login", json=DOCENTE, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def demo_docente_id(admin_token):
    dl = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
    d = [x for x in dl if x["email"] == DOCENTE["email"]][0]
    return d["id"]


# ---------------- Materie CRUD ----------------
class TestMaterie:
    def test_admin_can_list_materie(self, admin_token):
        r = requests.get(f"{API}/materie", headers=H(admin_token))
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)

    def test_docente_can_list_materie(self, docente_token):
        r = requests.get(f"{API}/materie", headers=H(docente_token))
        assert r.status_code == 200

    def test_docente_cannot_create_materia(self, docente_token):
        r = requests.post(f"{API}/materie", headers=H(docente_token),
                          json={"descrizione": "TEST_Forbidden", "prezzo": 30})
        assert r.status_code == 403

    def test_create_materia_unique_and_patch_delete(self, admin_token):
        # Create
        r = requests.post(f"{API}/materie", headers=H(admin_token),
                          json={"descrizione": "TEST_Fisica", "prezzo": 25.5})
        assert r.status_code == 201, r.text
        mat = r.json()
        assert mat["descrizione"] == "TEST_Fisica"
        assert mat["prezzo"] == 25.5
        mid = mat["id"]

        # Duplicate -> 400
        r2 = requests.post(f"{API}/materie", headers=H(admin_token),
                           json={"descrizione": "TEST_Fisica"})
        assert r2.status_code == 400, r2.text

        # GET list contains it
        ls = requests.get(f"{API}/materie", headers=H(admin_token)).json()
        assert any(m["id"] == mid for m in ls)

        # PATCH
        p = requests.patch(f"{API}/materie/{mid}", headers=H(admin_token),
                           json={"prezzo": 40})
        assert p.status_code == 200
        assert p.json()["prezzo"] == 40

        # DELETE
        d = requests.delete(f"{API}/materie/{mid}", headers=H(admin_token))
        assert d.status_code == 204

        # GET to verify removal
        ls2 = requests.get(f"{API}/materie", headers=H(admin_token)).json()
        assert not any(m["id"] == mid for m in ls2)


# ---------------- Docente-Materie association ----------------
class TestDocenteMaterie:
    def test_associa_disassocia(self, admin_token, demo_docente_id):
        # Create temp materia
        r = requests.post(f"{API}/materie", headers=H(admin_token),
                          json={"descrizione": "TEST_Chimica"})
        mid = r.json()["id"]
        try:
            # Associate
            a = requests.post(f"{API}/docenti/{demo_docente_id}/materie/{mid}",
                              headers=H(admin_token))
            assert a.status_code == 201, a.text

            # List
            ls = requests.get(f"{API}/docenti/{demo_docente_id}/materie",
                              headers=H(admin_token))
            assert ls.status_code == 200
            assert any(m["id"] == mid for m in ls.json())

            # Idempotent association
            a2 = requests.post(f"{API}/docenti/{demo_docente_id}/materie/{mid}",
                               headers=H(admin_token))
            assert a2.status_code in (200, 201), a2.text

            # Disassociate
            d = requests.delete(f"{API}/docenti/{demo_docente_id}/materie/{mid}",
                                headers=H(admin_token))
            assert d.status_code == 204
            ls2 = requests.get(f"{API}/docenti/{demo_docente_id}/materie",
                               headers=H(admin_token)).json()
            assert not any(m["id"] == mid for m in ls2)
        finally:
            requests.delete(f"{API}/materie/{mid}", headers=H(admin_token))

    def test_delete_materia_cleans_associations(self, admin_token, demo_docente_id):
        r = requests.post(f"{API}/materie", headers=H(admin_token),
                          json={"descrizione": "TEST_Storia"})
        mid = r.json()["id"]
        requests.post(f"{API}/docenti/{demo_docente_id}/materie/{mid}", headers=H(admin_token))
        # Confirm associated
        ls = requests.get(f"{API}/docenti/{demo_docente_id}/materie",
                          headers=H(admin_token)).json()
        assert any(m["id"] == mid for m in ls)
        # Delete materia
        d = requests.delete(f"{API}/materie/{mid}", headers=H(admin_token))
        assert d.status_code == 204
        # Should be removed from docente list
        ls2 = requests.get(f"{API}/docenti/{demo_docente_id}/materie",
                           headers=H(admin_token)).json()
        assert not any(m["id"] == mid for m in ls2)

    def test_delete_docente_cleans_materie_associations(self, admin_token):
        # Create temp docente
        dr = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_DocM", "cognome": "TEST_M", "email": "TEST_docm@example.com",
            "password": "Pass1234!"
        })
        did = dr.json()["id"]
        # Create temp materia
        mr = requests.post(f"{API}/materie", headers=H(admin_token),
                           json={"descrizione": "TEST_Inglese"})
        mid = mr.json()["id"]
        try:
            requests.post(f"{API}/docenti/{did}/materie/{mid}", headers=H(admin_token))
            # Delete docente
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))
            # The materia still exists; but the association must be gone.
            # Re-fetch materie list - materia still present.
            ml = requests.get(f"{API}/materie", headers=H(admin_token)).json()
            assert any(m["id"] == mid for m in ml)
            # Re-create docente and verify it has NO materie associated
            dr2 = requests.post(f"{API}/docenti", headers=H(admin_token), json={
                "nome": "TEST_DocM2", "cognome": "TEST_M", "email": "TEST_docm2@example.com",
                "password": "Pass1234!"
            })
            did2 = dr2.json()["id"]
            ls = requests.get(f"{API}/docenti/{did2}/materie",
                              headers=H(admin_token)).json()
            assert ls == []
            requests.delete(f"{API}/docenti/{did2}", headers=H(admin_token))
        finally:
            requests.delete(f"{API}/materie/{mid}", headers=H(admin_token))


# ---------------- Bulk appuntamenti ----------------
def _future_date(offset_days=20):
    return (date.today() + timedelta(days=offset_days)).isoformat()


def _future_monday(offset_weeks=3):
    today = date.today()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead + 7 * offset_weeks)).isoformat()


class TestBulkAppuntamenti:
    def test_bulk_create_3_slots(self, admin_token, demo_docente_id):
        # Use existing demo cliente
        clienti = requests.get(f"{API}/clienti", headers=H(admin_token)).json()
        verdi = [c for c in clienti if c["cognome"] == "Verdi"][0]
        cid = verdi["id"]
        # Use far future to avoid overlap with prior tests
        d0 = _future_monday(4)
        d1 = (date.fromisoformat(d0) + timedelta(days=7)).isoformat()
        d2 = (date.fromisoformat(d0) + timedelta(days=14)).isoformat()
        body = {
            "docente_id": demo_docente_id,
            "cliente_id": cid,
            "slots": [
                {"data": d0, "dal": "09:00", "al": "10:00"},
                {"data": d1, "dal": "09:00", "al": "10:00"},
                {"data": d2, "dal": "09:00", "al": "10:00"},
            ],
            "note": "TEST_bulk",
        }
        r = requests.post(f"{API}/appuntamenti/bulk", headers=H(admin_token), json=body)
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["count_created"] == 3
        assert out["count_skipped"] == 0
        # Cleanup
        for c in out["created"]:
            requests.delete(f"{API}/appuntamenti/{c['id']}", headers=H(admin_token))

    def test_bulk_skip_overlap(self, admin_token, demo_docente_id):
        clienti = requests.get(f"{API}/clienti", headers=H(admin_token)).json()
        verdi = [c for c in clienti if c["cognome"] == "Verdi"][0]
        cid = verdi["id"]
        d0 = _future_monday(6)
        # Pre-create an appointment at d0 10:00-11:00
        pre = requests.post(f"{API}/appuntamenti", headers=H(admin_token), json={
            "docente_id": demo_docente_id, "cliente_id": cid,
            "data": d0, "dal": "10:00", "al": "11:00"
        })
        assert pre.status_code == 201, pre.text
        pre_id = pre.json()["id"]
        try:
            d1 = (date.fromisoformat(d0) + timedelta(days=7)).isoformat()
            d2 = (date.fromisoformat(d0) + timedelta(days=14)).isoformat()
            body = {
                "docente_id": demo_docente_id,
                "cliente_id": cid,
                "slots": [
                    {"data": d0, "dal": "10:00", "al": "11:00"},  # overlap
                    {"data": d1, "dal": "10:00", "al": "11:00"},
                    {"data": d2, "dal": "10:00", "al": "11:00"},
                ],
            }
            r = requests.post(f"{API}/appuntamenti/bulk", headers=H(admin_token), json=body)
            assert r.status_code == 200, r.text
            out = r.json()
            assert out["count_created"] == 2
            assert out["count_skipped"] == 1
            assert out["skipped"][0]["motivo"] == "Slot occupato"
            # Cleanup created
            for c in out["created"]:
                requests.delete(f"{API}/appuntamenti/{c['id']}", headers=H(admin_token))
        finally:
            requests.delete(f"{API}/appuntamenti/{pre_id}", headers=H(admin_token))

    def test_bulk_with_nuovo_cliente_creates_and_associates(self, admin_token, demo_docente_id):
        d0 = _future_monday(8)
        new_email = "TEST_bulk_new@example.com"
        body = {
            "docente_id": demo_docente_id,
            "nuovo_cliente": {
                "nome": "TEST_BulkNew",
                "cognome": "TEST_Cli",
                "email": new_email,
                "cellulare": "+391234567",
            },
            "slots": [
                {"data": d0, "dal": "15:00", "al": "16:00"},
            ],
        }
        r = requests.post(f"{API}/appuntamenti/bulk", headers=H(admin_token), json=body)
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["count_created"] == 1
        new_cid = out["cliente_id"]
        try:
            # Verify cliente appears in GET /clienti
            cl = requests.get(f"{API}/clienti", headers=H(admin_token)).json()
            assert any(c["id"] == new_cid for c in cl)
            # Verify associated with demo docente
            alunni = requests.get(f"{API}/docenti/{demo_docente_id}/alunni",
                                  headers=H(admin_token)).json()
            assert any(a["id"] == new_cid for a in alunni)
        finally:
            for c in out["created"]:
                requests.delete(f"{API}/appuntamenti/{c['id']}", headers=H(admin_token))
            requests.delete(f"{API}/clienti/{new_cid}", headers=H(admin_token))

    def test_bulk_without_cliente_400(self, admin_token, demo_docente_id):
        body = {
            "docente_id": demo_docente_id,
            "slots": [{"data": _future_monday(10), "dal": "09:00", "al": "10:00"}],
        }
        r = requests.post(f"{API}/appuntamenti/bulk", headers=H(admin_token), json=body)
        assert r.status_code == 400, r.text

    def test_bulk_as_docente_forces_self(self, admin_token, docente_token, demo_docente_id):
        # Create a second docente
        dr = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_OtherBulk", "cognome": "TEST_D", "email": "TEST_otherbulk@example.com",
            "password": "Pass1234!"
        })
        other_did = dr.json()["id"]
        clienti = requests.get(f"{API}/clienti", headers=H(docente_token)).json()
        cid = clienti[0]["id"]
        d0 = _future_monday(12)
        try:
            body = {
                "docente_id": other_did,  # docente tries to spoof
                "cliente_id": cid,
                "slots": [{"data": d0, "dal": "11:00", "al": "12:00"}],
            }
            r = requests.post(f"{API}/appuntamenti/bulk", headers=H(docente_token), json=body)
            assert r.status_code == 200, r.text
            out = r.json()
            # Must be forced to demo docente (self), not other_did
            assert out["docente_id"] == demo_docente_id
            assert out["count_created"] == 1
            for c in out["created"]:
                requests.delete(f"{API}/appuntamenti/{c['id']}", headers=H(admin_token))
        finally:
            requests.delete(f"{API}/docenti/{other_did}", headers=H(admin_token))

    def test_bulk_invalid_time_range_skips(self, admin_token, demo_docente_id):
        clienti = requests.get(f"{API}/clienti", headers=H(admin_token)).json()
        cid = [c for c in clienti if c["cognome"] == "Verdi"][0]["id"]
        d0 = _future_monday(14)
        body = {
            "docente_id": demo_docente_id,
            "cliente_id": cid,
            "slots": [
                {"data": d0, "dal": "10:00", "al": "10:00"},  # invalid
                {"data": d0, "dal": "11:00", "al": "10:00"},  # invalid
            ],
        }
        r = requests.post(f"{API}/appuntamenti/bulk", headers=H(admin_token), json=body)
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["count_created"] == 0
        assert out["count_skipped"] == 2
        for s in out["skipped"]:
            assert s["motivo"]  # motivo present
