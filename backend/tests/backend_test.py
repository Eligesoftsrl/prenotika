"""EligeHub SaaS backend tests - auth, role isolation, CRUD and business logic."""
import os
import pytest
import requests
from datetime import date, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://timeslot-manager-23.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@demo.it", "password": "Admin123!"}
DOCENTE = {"email": "docente@demo.it", "password": "Docente123!"}
SUPER = {"email": "superadmin@eligehub.it", "password": "SuperAdmin123!"}


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def docente_token():
    r = requests.post(f"{API}/auth/login", json=DOCENTE, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def super_token():
    r = requests.post(f"{API}/auth/login", json=SUPER, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Auth ----------
class TestAuth:
    def test_login_admin(self):
        r = requests.post(f"{API}/auth/login", json=ADMIN)
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["role"] == "admin"
        assert d["studio"] is not None
        assert isinstance(d["access_token"], str) and d["access_token"]

    def test_login_docente(self):
        r = requests.post(f"{API}/auth/login", json=DOCENTE)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "docente"

    def test_login_super(self):
        r = requests.post(f"{API}/auth/login", json=SUPER)
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["role"] == "super_admin"
        assert d["studio"] is None

    def test_login_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN["email"], "password": "wrong"})
        assert r.status_code == 401

    def test_me_with_token(self, admin_token):
        r = requests.get(f"{API}/auth/me", headers=H(admin_token))
        assert r.status_code == 200
        assert r.json()["user"]["email"] == ADMIN["email"]

    def test_me_without_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401


# ---------- Role isolation ----------
class TestRoleIsolation:
    def test_docente_can_read_docenti(self, docente_token):
        r = requests.get(f"{API}/docenti", headers=H(docente_token))
        assert r.status_code == 200

    def test_docente_can_read_clienti(self, docente_token):
        r = requests.get(f"{API}/clienti", headers=H(docente_token))
        assert r.status_code == 200

    def test_docente_cannot_create_cliente(self, docente_token):
        r = requests.post(f"{API}/clienti", headers=H(docente_token),
                          json={"nome": "X", "cognome": "Y"})
        assert r.status_code == 403

    def test_docente_cannot_create_docente(self, docente_token):
        r = requests.post(f"{API}/docenti", headers=H(docente_token),
                          json={"nome": "A", "cognome": "B", "email": "a@b.it", "password": "Xx12345!"})
        assert r.status_code == 403

    def test_docente_cannot_create_studio(self, docente_token):
        r = requests.post(f"{API}/studios", headers=H(docente_token),
                          json={"nome": "X", "admin_nome": "A", "admin_cognome": "B",
                                "admin_email": "x@x.it", "admin_password": "Xx12345!"})
        assert r.status_code == 403


# ---------- Super admin / studio multi-tenant ----------
class TestStudiosAndScoping:
    def test_super_list_studios(self, super_token):
        r = requests.get(f"{API}/studios", headers=H(super_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_cannot_list_studios(self, admin_token):
        r = requests.get(f"{API}/studios", headers=H(admin_token))
        assert r.status_code == 403

    def test_create_and_delete_studio_and_isolation(self, super_token, admin_token):
        # Create new studio
        payload = {
            "nome": "TEST_Studio_Iso",
            "admin_nome": "Test", "admin_cognome": "Admin2",
            "admin_email": "TEST_admin_iso@example.com",
            "admin_password": "Pass1234!",
        }
        r = requests.post(f"{API}/studios", headers=H(super_token), json=payload)
        assert r.status_code == 201, r.text
        new_sid = r.json()["id"]

        # Login as new admin
        lr = requests.post(f"{API}/auth/login", json={
            "email": payload["admin_email"], "password": payload["admin_password"]})
        assert lr.status_code == 200
        new_token = lr.json()["access_token"]

        # Create a cliente in new studio
        cr = requests.post(f"{API}/clienti", headers=H(new_token),
                           json={"nome": "TEST_OtherStudio", "cognome": "Client"})
        assert cr.status_code == 201
        other_cli_id = cr.json()["id"]

        # admin@demo.it must NOT see this client
        lst = requests.get(f"{API}/clienti", headers=H(admin_token))
        assert lst.status_code == 200
        ids = [c["id"] for c in lst.json()]
        assert other_cli_id not in ids

        # Delete studio (cleanup)
        dr = requests.delete(f"{API}/studios/{new_sid}", headers=H(super_token))
        assert dr.status_code == 204

        # New admin login should now fail (user deleted)
        lr2 = requests.post(f"{API}/auth/login", json={
            "email": payload["admin_email"], "password": payload["admin_password"]})
        assert lr2.status_code == 401


# ---------- Clienti CRUD ----------
class TestClientiCRUD:
    def test_crud_clienti(self, admin_token):
        # Create
        r = requests.post(f"{API}/clienti", headers=H(admin_token),
                          json={"nome": "TEST_Mario", "cognome": "TEST_Rossi", "email": "TEST_mr@example.com"})
        assert r.status_code == 201
        cid = r.json()["id"]
        assert "studio_id" in r.json() and r.json()["studio_id"]

        # List
        lst = requests.get(f"{API}/clienti", headers=H(admin_token))
        assert lst.status_code == 200
        assert any(c["id"] == cid for c in lst.json())

        # Patch
        p = requests.patch(f"{API}/clienti/{cid}", headers=H(admin_token), json={"cellulare": "+391112223"})
        assert p.status_code == 200
        assert p.json()["cellulare"] == "+391112223"

        # Verify persisted
        g = requests.get(f"{API}/clienti", headers=H(admin_token))
        match = [c for c in g.json() if c["id"] == cid][0]
        assert match["cellulare"] == "+391112223"

        # Delete
        d = requests.delete(f"{API}/clienti/{cid}", headers=H(admin_token))
        assert d.status_code == 204


# ---------- Docenti CRUD ----------
class TestDocentiCRUD:
    def test_create_update_delete(self, admin_token):
        email = "TEST_docente_crud@example.com"
        r = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "TEST_Luca", "cognome": "TEST_Bianchi", "email": email, "password": "Pass1234!",
            "specializzazione": "Fisica"
        })
        assert r.status_code == 201, r.text
        did = r.json()["id"]

        # Unique email
        r2 = requests.post(f"{API}/docenti", headers=H(admin_token), json={
            "nome": "X", "cognome": "Y", "email": email, "password": "Pass1234!"})
        assert r2.status_code == 400

        # Update
        u = requests.patch(f"{API}/docenti/{did}", headers=H(admin_token),
                           json={"specializzazione": "Chimica"})
        assert u.status_code == 200
        assert u.json()["specializzazione"] == "Chimica"

        # Delete cascade
        d = requests.delete(f"{API}/docenti/{did}", headers=H(admin_token))
        assert d.status_code == 204


# ---------- Orari ----------
class TestOrari:
    def test_docente_lists_only_own(self, docente_token):
        r = requests.get(f"{API}/orari", headers=H(docente_token))
        assert r.status_code == 200
        items = r.json()
        # All belong to same docente_id
        docente_ids = {i["docente_id"] for i in items}
        assert len(docente_ids) <= 1

    def test_docente_create_orario_and_invalid(self, docente_token):
        r = requests.post(f"{API}/orari", headers=H(docente_token),
                          json={"giorno": 5, "dal": "10:00", "al": "11:00"})
        assert r.status_code == 201
        oid = r.json()["id"]

        bad = requests.post(f"{API}/orari", headers=H(docente_token),
                            json={"giorno": 5, "dal": "12:00", "al": "11:00"})
        assert bad.status_code == 400

        # Cleanup
        requests.delete(f"{API}/orari/{oid}", headers=H(docente_token))

    def test_admin_creates_for_docente(self, admin_token):
        # Find demo docente id
        dl = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
        did = [d for d in dl if d["email"] == DOCENTE["email"]][0]["id"]
        r = requests.post(f"{API}/orari", headers=H(admin_token),
                          json={"giorno": 6, "dal": "10:00", "al": "11:00", "docente_id": did})
        assert r.status_code == 201
        oid = r.json()["id"]
        d = requests.delete(f"{API}/orari/{oid}", headers=H(admin_token))
        assert d.status_code == 204


# ---------- Appuntamenti & overlap ----------
class TestAppuntamenti:
    def test_create_overlap_and_disponibilita(self, admin_token, docente_token):
        # Find docente + cliente
        dl = requests.get(f"{API}/docenti", headers=H(admin_token)).json()
        did = [d for d in dl if d["email"] == DOCENTE["email"]][0]["id"]
        cl = requests.get(f"{API}/clienti", headers=H(admin_token)).json()
        cid = cl[0]["id"]

        # Pick next monday (weekday 0) so orari Mon-Fri 9-13 apply
        today = date.today()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = (today + timedelta(days=days_ahead)).isoformat()

        # Cleanup any existing TEST appuntamenti for that date
        existing = requests.get(f"{API}/appuntamenti?data_da={target}&data_a={target}",
                                headers=H(admin_token)).json()
        for a in existing:
            if a["docente_id"] == did and a["dal"] in ("09:00", "10:00"):
                requests.delete(f"{API}/appuntamenti/{a['id']}", headers=H(admin_token))

        # Create appuntamento
        body = {"docente_id": did, "cliente_id": cid, "data": target,
                "dal": "10:00", "al": "11:00"}
        r = requests.post(f"{API}/appuntamenti", headers=H(admin_token), json=body)
        assert r.status_code == 201, r.text
        ap = r.json()
        assert ap["cliente_nome"] and ap["docente_nome"]
        app_id = ap["id"]

        # Overlap
        r2 = requests.post(f"{API}/appuntamenti", headers=H(admin_token),
                           json={**body, "dal": "10:30", "al": "11:30"})
        assert r2.status_code == 409

        # docente cannot create for someone else (force admin docente_id different) - here docente token forces own
        # Verify docente can list own
        lst_d = requests.get(f"{API}/appuntamenti", headers=H(docente_token)).json()
        assert all(a["docente_id"] == did for a in lst_d)

        # Disponibilita - slot 10:00 must NOT be present
        disp = requests.get(f"{API}/disponibilita?docente_id={did}&data={target}",
                            headers=H(admin_token))
        assert disp.status_code == 200
        slots = disp.json()["slots"]
        assert not any(s["dal"] == "10:00" for s in slots)
        # 09:00 should still be free
        assert any(s["dal"] == "09:00" for s in slots)

        # Cleanup
        requests.delete(f"{API}/appuntamenti/{app_id}", headers=H(admin_token))


# ---------- Dashboard ----------
class TestDashboard:
    def test_admin_stats(self, admin_token):
        r = requests.get(f"{API}/dashboard/stats", headers=H(admin_token))
        assert r.status_code == 200
        d = r.json()
        for k in ("totale_clienti", "totale_docenti", "appuntamenti_oggi",
                  "appuntamenti_settimana", "prossimi_appuntamenti"):
            assert k in d
        assert isinstance(d["prossimi_appuntamenti"], list)

    def test_docente_stats(self, docente_token):
        r = requests.get(f"{API}/dashboard/stats", headers=H(docente_token))
        assert r.status_code == 200
