"""Iteration 2: slot_minuti, docente-alunni N:M associations, docente_id filter on /clienti."""
import os
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


# ---------------- slot_minuti on docente ----------------
class TestSlotMinuti:
    def test_create_docente_with_slot_minuti(self, admin_token):
        email = "TEST_slot_doc@example.com"
        r = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_Slot", "cognome": "TEST_Doc", "email": email,
            "password": "Pass1234!", "slot_minuti": 30
        })
        assert r.status_code == 201, r.text
        did = r.json()["id"]
        assert r.json()["slot_minuti"] == 30

        # GET list and verify persisted
        ls = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
        match = [d for d in ls if d["id"] == did][0]
        assert match["slot_minuti"] == 30

        # PATCH to 45
        p = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                           json={"slot_minuti": 45})
        assert p.status_code == 200
        assert p.json()["slot_minuti"] == 45

        ls2 = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
        assert [d for d in ls2 if d["id"] == did][0]["slot_minuti"] == 45

        # Cleanup
        requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))

    def test_default_slot_minuti_is_60(self, admin_token):
        email = "TEST_slot_def@example.com"
        r = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_Def", "cognome": "TEST_Doc", "email": email,
            "password": "Pass1234!"
        })
        assert r.status_code == 201
        did = r.json()["id"]
        assert r.json()["slot_minuti"] == 60
        requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))


# ---------------- Disponibilita with slot ----------------
class TestDisponibilitaSlot:
    def test_disponibilita_uses_docente_default_slot(self, admin_token, demo_docente_id):
        # Mon-Fri 9-13: with slot 60 -> 4 slots in 9-13 (no booking assumed at far future date)
        from datetime import date, timedelta
        today = date.today()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = (today + timedelta(days=days_ahead + 14)).isoformat()
        r = requests.get(f"{API}/disponibilita?docente_id={demo_docente_id}&data={target}",
                         headers=H(admin_token))
        assert r.status_code == 200
        slots60 = r.json()["slots"]

        r2 = requests.get(f"{API}/disponibilita?docente_id={demo_docente_id}&data={target}&slot_minuti=30",
                          headers=H(admin_token))
        assert r2.status_code == 200
        slots30 = r2.json()["slots"]
        # With 30 min slots, count must be >= 2x of 60 slots (covering same windows)
        assert len(slots30) >= 2 * len(slots60) - 2


# ---------------- Docente alunni association ----------------
class TestDocenteAlunni:
    def test_list_alunni_demo_docente_has_two(self, admin_token, demo_docente_id):
        r = requests.get(f"{API}/docenti/{demo_docente_id}/alunni", headers=H(admin_token))
        assert r.status_code == 200
        alunni = r.json()
        cognomi = sorted([a["cognome"] for a in alunni])
        assert "Verdi" in cognomi
        assert "Neri" in cognomi

    def test_docente_can_list_own_alunni(self, docente_token, demo_docente_id):
        r = requests.get(f"{API}/docenti/{demo_docente_id}/alunni", headers=H(docente_token))
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_docente_cannot_list_other_docente_alunni(self, admin_token, docente_token):
        # Create another docente
        r = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_Other", "cognome": "TEST_Doc", "email": "TEST_other_doc@example.com",
            "password": "Pass1234!"
        })
        other_did = r.json()["id"]
        try:
            r2 = requests.get(f"{API}/docenti/{other_did}/alunni", headers=H(docente_token))
            assert r2.status_code == 403
        finally:
            requests.delete(f"{API}/docenti/{other_did}", headers=H(admin_token))

    def test_associa_disassocia_alunno(self, admin_token, demo_docente_id):
        # create temp cliente
        cr = requests.post(f"{API}/clienti", headers=H(admin_token),
                           json={"nome": "TEST_Assoc", "cognome": "TEST_Alunno"})
        assert cr.status_code == 201
        cid = cr.json()["id"]
        try:
            # associate
            a = requests.post(f"{API}/docenti/{demo_docente_id}/alunni/{cid}",
                              headers=H(admin_token))
            assert a.status_code == 201

            # verify in list
            ls = requests.get(f"{API}/docenti/{demo_docente_id}/alunni",
                              headers=H(admin_token)).json()
            assert any(x["id"] == cid for x in ls)

            # idempotent - second call should NOT 4xx; returns "Già associato"
            a2 = requests.post(f"{API}/docenti/{demo_docente_id}/alunni/{cid}",
                               headers=H(admin_token))
            assert a2.status_code in (200, 201), a2.text
            assert "associato" in a2.json().get("message", "").lower() or a2.status_code == 201

            # disassociate
            d = requests.delete(f"{API}/docenti/{demo_docente_id}/alunni/{cid}",
                                headers=H(admin_token))
            assert d.status_code == 204
            ls2 = requests.get(f"{API}/docenti/{demo_docente_id}/alunni",
                               headers=H(admin_token)).json()
            assert not any(x["id"] == cid for x in ls2)
        finally:
            requests.delete(f"{API}/clienti/{cid}", headers=H(admin_token))

    def test_delete_cliente_cleans_associations(self, admin_token, demo_docente_id):
        cr = requests.post(f"{API}/clienti", headers=H(admin_token),
                           json={"nome": "TEST_DelClean", "cognome": "TEST_Cli"})
        cid = cr.json()["id"]
        requests.post(f"{API}/docenti/{demo_docente_id}/alunni/{cid}", headers=H(admin_token))
        # Delete cliente
        requests.delete(f"{API}/clienti/{cid}", headers=H(admin_token))
        # alunni list must not contain cid
        ls = requests.get(f"{API}/docenti/{demo_docente_id}/alunni",
                          headers=H(admin_token)).json()
        assert not any(x["id"] == cid for x in ls)

    def test_delete_docente_cleans_associations(self, admin_token):
        # create temp docente
        dr = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_DelDoc", "cognome": "TEST_Doc", "email": "TEST_deldoc@example.com",
            "password": "Pass1234!"
        })
        did = dr.json()["id"]
        # create temp cliente
        cr = requests.post(f"{API}/clienti", headers=H(admin_token),
                           json={"nome": "TEST_DelDocCli", "cognome": "TEST_Cli"})
        cid = cr.json()["id"]
        try:
            # associate
            requests.post(f"{API}/docenti/{did}/alunni/{cid}", headers=H(admin_token))
            # filter clienti by docente_id
            f = requests.get(f"{API}/clienti?docente_id={did}", headers=H(admin_token)).json()
            assert any(c["id"] == cid for c in f)
            # delete docente
            requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))
            # filter again, must be empty (no association left)
            f2 = requests.get(f"{API}/clienti?docente_id={did}", headers=H(admin_token)).json()
            assert f2 == []
        finally:
            requests.delete(f"{API}/clienti/{cid}", headers=H(admin_token))


# ---------------- Clienti filtering ----------------
class TestClientiFilter:
    def test_admin_clienti_filter_by_docente(self, admin_token, demo_docente_id):
        # Without filter must have at least 2
        all_c = requests.get(f"{API}/clienti", headers=H(admin_token)).json()
        # With filter must return only associated (2: Luca Verdi, Giulia Neri)
        f = requests.get(f"{API}/clienti?docente_id={demo_docente_id}", headers=H(admin_token)).json()
        assert len(f) >= 2
        cognomi = {c["cognome"] for c in f}
        assert "Verdi" in cognomi
        assert "Neri" in cognomi
        # All returned must be associated to the docente -> subset of all clienti
        all_ids = {c["id"] for c in all_c}
        for c in f:
            assert c["id"] in all_ids

    def test_docente_sees_only_associated_clienti(self, docente_token):
        r = requests.get(f"{API}/clienti", headers=H(docente_token))
        assert r.status_code == 200
        items = r.json()
        # Demo docente has 2 associated alunni
        assert len(items) == 2
        cognomi = {c["cognome"] for c in items}
        assert cognomi == {"Verdi", "Neri"}
