"""
Iteration 14 backend tests:
- Plan field on Studio (default 'free', persisted)
- Super admin PATCH /api/studios/{id} to change plan
- GET /api/studio/quota for admin/docente
- Enforcement quota professionisti: POST /api/docenti -> 403 when limit reached
- Pricing landing values (sanity by reading the rendered Landing.jsx is FE concern; here verify backend models)
"""
import os
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        # Fallback: read frontend/.env
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.strip().split("=", 1)[1]
                        break
        except FileNotFoundError:
            pass
    assert url, "REACT_APP_BACKEND_URL not configured"
    return url.rstrip("/")


BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

SUPER_EMAIL = "superadmin@eligehub.it"
SUPER_PASS = "SuperAdmin123!"
ADMIN_EMAIL = "admin@demo.it"
ADMIN_PASS = "Admin123!"
DEMO_STUDIO_ID = "95064d29-4598-4be5-abfc-4ee57bcbd4d8"


def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    token = r.json().get("access_token") or r.json().get("token")
    assert token
    return token


@pytest.fixture(scope="module")
def super_token():
    return _login(SUPER_EMAIL, SUPER_PASS)


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASS)


def H(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Restore demo studio to 'business' at the end of module run ----------
@pytest.fixture(scope="module", autouse=True)
def restore_business(super_token):
    yield
    requests.patch(f"{API}/studios/{DEMO_STUDIO_ID}", json={"plan": "business"}, headers=H(super_token), timeout=15)


# --- Tests ---------------------------------------------------------------
class TestStudioPlan:
    def test_demo_studio_starts_business(self, super_token):
        # Ensure baseline = business
        r = requests.patch(f"{API}/studios/{DEMO_STUDIO_ID}", json={"plan": "business"}, headers=H(super_token), timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["plan"] == "business"

    def test_quota_business_unlimited(self, admin_token):
        r = requests.get(f"{API}/studio/quota", headers=H(admin_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["plan"] == "business"
        assert data["professionisti_limit"] is None
        assert data["can_add_more"] is True
        assert isinstance(data["professionisti_used"], int)
        assert data["professionisti_used"] >= 2  # seed: Mario Rossi + Anna Verdi

    def test_super_admin_patch_plan_to_free(self, super_token):
        r = requests.patch(f"{API}/studios/{DEMO_STUDIO_ID}", json={"plan": "free"}, headers=H(super_token), timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["plan"] == "free"

    def test_quota_free_used_exceeds_limit(self, admin_token):
        r = requests.get(f"{API}/studio/quota", headers=H(admin_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["plan"] == "free"
        assert data["professionisti_limit"] == 1
        assert data["professionisti_used"] >= 2
        assert data["can_add_more"] is False

    def test_post_docenti_blocked_on_free(self, admin_token):
        payload = {
            "nome": "TESTQuota",
            "cognome": "Blocked",
            "email": "test_quota_blocked@example.com",
            "password": "Test123!",
            "telefono": "",
            "specializzazione": "",
            "color": "#7C3AED",
        }
        r = requests.post(f"{API}/docenti", json=payload, headers=H(admin_token), timeout=15)
        assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"
        detail = r.json().get("detail", "")
        assert "Free" in detail and "1 professionisti" in detail, f"unexpected detail: {detail}"

    def test_super_admin_patch_plan_to_pro(self, super_token):
        r = requests.patch(f"{API}/studios/{DEMO_STUDIO_ID}", json={"plan": "pro"}, headers=H(super_token), timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["plan"] == "pro"

    def test_quota_pro_5_limit(self, admin_token):
        r = requests.get(f"{API}/studio/quota", headers=H(admin_token), timeout=15)
        data = r.json()
        assert data["plan"] == "pro"
        assert data["professionisti_limit"] == 5
        # With 2 seeded docenti < 5 -> can_add_more True
        assert data["can_add_more"] is True

    def test_create_docente_works_on_pro(self, admin_token):
        payload = {
            "nome": "TESTProQuota",
            "cognome": "Allowed",
            "email": "test_pro_quota_allowed@example.com",
            "password": "Test123!",
            "telefono": "",
            "specializzazione": "",
            "color": "#7C3AED",
        }
        r = requests.post(f"{API}/docenti", json=payload, headers=H(admin_token), timeout=15)
        # If it already exists from a prior run, accept 400 and continue
        assert r.status_code in (201, 400), r.text
        if r.status_code == 201:
            created_id = r.json()["id"]
            # cleanup
            d = requests.delete(f"{API}/docenti/{created_id}", headers=H(admin_token), timeout=15)
            assert d.status_code in (200, 204)


class TestSuperAdminStudiosList:
    def test_list_studios_includes_plan(self, super_token):
        r = requests.get(f"{API}/studios", headers=H(super_token), timeout=15)
        assert r.status_code == 200, r.text
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        demo = next((s for s in items if s["id"] == DEMO_STUDIO_ID), None)
        assert demo is not None
        assert "plan" in demo
        assert demo["plan"] in ("free", "pro", "business")

    def test_patch_invalid_plan_rejected(self, super_token):
        r = requests.patch(
            f"{API}/studios/{DEMO_STUDIO_ID}", json={"plan": "ultimate"}, headers=H(super_token), timeout=15
        )
        assert r.status_code in (422, 400), f"expected 4xx, got {r.status_code} {r.text}"


class TestRegressionLogin:
    def test_admin_login_ok(self):
        token = _login(ADMIN_EMAIL, ADMIN_PASS)
        assert token

    def test_super_login_ok(self):
        token = _login(SUPER_EMAIL, SUPER_PASS)
        assert token
