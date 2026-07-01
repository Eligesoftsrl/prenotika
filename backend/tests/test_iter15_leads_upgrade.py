"""Iteration 15: Leads endpoints (super_admin only) + upgrade quota flow."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

SUPER = {"email": "superadmin@eligehub.it", "password": "SuperAdmin123!"}
ADMIN = {"email": "admin@demo.it", "password": "Admin123!"}

DEMO_STUDIO_ID = "95064d29-4598-4be5-abfc-4ee57bcbd4d8"


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def super_token():
    return _login(SUPER)


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


def _h(t):
    return {"Authorization": f"Bearer {t}"}


# --- Leads endpoints -----------------------------------------------------
class TestLeadsEndpoints:
    def test_list_leads_super_admin_200(self, super_token):
        r = requests.get(f"{API}/leads", headers=_h(super_token), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_leads_admin_forbidden(self, admin_token):
        r = requests.get(f"{API}/leads", headers=_h(admin_token), timeout=15)
        assert r.status_code == 403

    def test_create_patch_delete_lead(self, super_token):
        # Create a lead via public endpoint (no auth)
        payload = {
            "nome": "TEST_Iter15 Lead",
            "email": "test_iter15@example.com",
            "telefono": "+39 000 000",
            "tipologia": "centro_studi",
            "studio": "TEST Studio",
            "messaggio": "Interessato",
            "piano_interesse": "pro",
        }
        r = requests.post(f"{API}/leads", json=payload, timeout=15)
        assert r.status_code == 201, r.text
        lead = r.json()
        lid = lead.get("id")
        assert lid, lead

        # PATCH status
        r = requests.patch(
            f"{API}/leads/{lid}",
            json={"status": "contacted"},
            headers=_h(super_token),
            timeout=15,
        )
        assert r.status_code == 200, r.text
        updated = r.json()
        assert updated["status"] == "contacted"

        # Confirm via GET list
        r = requests.get(f"{API}/leads", headers=_h(super_token), timeout=15)
        assert r.status_code == 200
        found = next((l for l in r.json() if l["id"] == lid), None)
        assert found and found["status"] == "contacted"

        # DELETE
        r = requests.delete(
            f"{API}/leads/{lid}", headers=_h(super_token), timeout=15
        )
        assert r.status_code == 204

        # Confirm removal
        r = requests.get(f"{API}/leads", headers=_h(super_token), timeout=15)
        assert all(l["id"] != lid for l in r.json())

    def test_patch_lead_admin_forbidden(self, super_token, admin_token):
        # Create tmp lead as public
        payload = {"nome": "TEST_perm", "email": "test_perm@example.com"}
        r = requests.post(f"{API}/leads", json=payload, timeout=15)
        assert r.status_code == 201
        lid = r.json()["id"]
        try:
            r = requests.patch(
                f"{API}/leads/{lid}",
                json={"status": "closed"},
                headers=_h(admin_token),
                timeout=15,
            )
            assert r.status_code == 403
        finally:
            requests.delete(
                f"{API}/leads/{lid}", headers=_h(super_token), timeout=15
            )


# --- Upgrade quota flow --------------------------------------------------
class TestUpgradeQuota:
    def test_set_free_then_create_docente_403(self, super_token):
        # Force studio demo to plan=free
        r = requests.patch(
            f"{API}/studios/{DEMO_STUDIO_ID}",
            json={"plan": "free"},
            headers=_h(super_token),
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("plan") == "free"

        # Login as admin to create docente → expect 403 "Limite del piano"
        admin_t = _login(ADMIN)
        payload = {
            "email": "TEST_iter15_doc@demo.it",
            "password": "Test1234!",
            "nome": "Test",
            "cognome": "Overquota",
        }
        r = requests.post(
            f"{API}/docenti",
            json=payload,
            headers=_h(admin_t),
            timeout=15,
        )
        assert r.status_code == 403, r.text
        detail = (r.json().get("detail") or "").lower()
        assert "limite del piano" in detail, detail

    def test_restore_business_plan(self, super_token):
        r = requests.patch(
            f"{API}/studios/{DEMO_STUDIO_ID}",
            json={"plan": "business"},
            headers=_h(super_token),
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json().get("plan") == "business"
