"""
Iteration 18 backend regression tests:
- OTP passwordless (request / verify)
- Automated onboarding flow (start / verify-token / complete)
- Stripe checkout endpoints
- Payment plans listing
"""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://timeslot-manager-23.preview.emergentagent.com").rstrip("/")
SUPER_EMAIL = "info@eligesoft.com"
SUPER_PASSWORD = "19Elige20."


# ---------- Fixtures --------------------------------------------------------

@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def super_admin_token(api_client):
    r = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_EMAIL, "password": SUPER_PASSWORD
    })
    assert r.status_code == 200, f"super_admin login failed: {r.status_code} {r.text}"
    data = r.json()
    return data["access_token"]


@pytest.fixture
def unique_email():
    return f"test.iter18.{uuid.uuid4().hex[:10]}@example.com"


# ---------- 1. Onboarding /start (new email) -------------------------------

class TestOnboardingStartNew:
    def test_start_new_creates_studio_and_admin(self, api_client, unique_email):
        payload = {
            "nome": "Mario Rossi",
            "email": unique_email,
            "telefono": "3331112222",
            "tipologia": "studio_medico",
            "piano_interesse": "free",
            "privacy_accepted": True,
            "studio_nome": "Studio Mario Test",
        }
        r = api_client.post(f"{BASE_URL}/api/onboarding/start", json=payload)
        assert r.status_code in (200, 201), f"got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("ok") is True
        assert data.get("existing_account") is False
        assert "setup_token" in data and len(data["setup_token"]) > 10
        assert "setup_url" in data
        assert "studio_id" in data and len(data["studio_id"]) > 0
        assert data.get("email") == unique_email
        # Store for next tests via class attribute
        TestOnboardingStartNew.token = data["setup_token"]
        TestOnboardingStartNew.email = unique_email
        TestOnboardingStartNew.studio_id = data["studio_id"]

    def test_start_duplicate_email_returns_existing(self, api_client):
        # Same email as previous test
        email = getattr(TestOnboardingStartNew, "email", None)
        assert email, "prior test did not run"
        payload = {
            "nome": "Duplicate",
            "email": email,
            "tipologia": "studio_medico",
            "piano_interesse": "free",
            "privacy_accepted": True,
        }
        r = api_client.post(f"{BASE_URL}/api/onboarding/start", json=payload)
        assert r.status_code in (200, 201)
        data = r.json()
        assert data.get("ok") is True
        assert data.get("existing_account") is True
        assert data.get("email") == email
        # Must NOT expose setup_token in this case
        assert "setup_token" not in data or data.get("setup_token") is None


# ---------- 2. Onboarding /verify-token -------------------------------------

class TestOnboardingVerifyToken:
    def test_verify_valid_token(self, api_client):
        token = getattr(TestOnboardingStartNew, "token", None)
        assert token, "no token from start"
        r = api_client.get(f"{BASE_URL}/api/onboarding/verify-token", params={"token": token})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert "access_token" in data and len(data["access_token"]) > 10
        assert "user" in data and data["user"].get("email") == TestOnboardingStartNew.email
        assert "studio" in data and data["studio"].get("id") == TestOnboardingStartNew.studio_id
        # Studio must have plan=free, onboarding_completed=false, tipologia=studio_medico
        assert data["studio"].get("plan") == "free"
        assert data["studio"].get("onboarding_completed") is False
        assert data["studio"].get("tipologia") == "studio_medico"
        # User must be admin/active
        assert data["user"].get("role") == "admin"
        assert data["user"].get("active") is True
        # Save temp JWT
        TestOnboardingVerifyToken.jwt = data["access_token"]

    def test_verify_invalid_token(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/onboarding/verify-token", params={"token": "INVALID_TOKEN_XYZ"})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data


# ---------- 3. Onboarding /complete -----------------------------------------

class TestOnboardingComplete:
    def test_complete_success(self, api_client):
        token = getattr(TestOnboardingStartNew, "token", None)
        payload = {
            "token": token,
            "studio_nome": "Studio Mario Aggiornato",
            "tipologia": "studio_medico",
            "sede": "Milano",
            "telefono": "3339998877",
            "piva": "12345678901",
            "comunicazioni": "Segreteria aperta 9-18",
            "logo_base64": "",
            "new_password": "TestPassword123!",
        }
        r = api_client.post(f"{BASE_URL}/api/onboarding/complete", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert "access_token" in data
        assert data["studio"].get("onboarding_completed") is True
        assert data["studio"].get("nome") == "Studio Mario Aggiornato"
        assert data["studio"].get("sede") == "Milano"
        # Now try to login with the new password to verify persistence
        login_r = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TestOnboardingStartNew.email,
            "password": "TestPassword123!"
        })
        assert login_r.status_code == 200, login_r.text

    def test_complete_token_now_used(self, api_client):
        # Re-completing with same token should still succeed or fail depending on impl;
        # spec says token becomes "used" but endpoint doesn't explicitly reject reuse.
        # We only assert the used flag by verifying the token still verifies (JWT is fresh).
        # This is informational - just call complete again and check response.
        token = getattr(TestOnboardingStartNew, "token", None)
        r = api_client.post(f"{BASE_URL}/api/onboarding/complete", json={"token": token})
        # Endpoint doesn't block reuse, just log it. Accept 200 or 400.
        assert r.status_code in (200, 400)


# ---------- 4. OTP request/verify -------------------------------------------

class TestOtp:
    def test_otp_request_unknown_email_returns_ok(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/otp/request", json={
            "email": f"nonexistent.{uuid.uuid4().hex[:8]}@example.com"
        })
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_otp_request_known_email_returns_ok(self, api_client):
        # Use super_admin email (definitely exists)
        r = api_client.post(f"{BASE_URL}/api/auth/otp/request", json={"email": SUPER_EMAIL})
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_otp_verify_malformed_short(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/otp/verify", json={
            "email": SUPER_EMAIL, "code": "123"
        })
        assert r.status_code == 400
        assert "non valido" in r.json().get("detail", "").lower()

    def test_otp_verify_malformed_non_digit(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/otp/verify", json={
            "email": SUPER_EMAIL, "code": "abcdef"
        })
        assert r.status_code == 400
        assert "non valido" in r.json().get("detail", "").lower()

    def test_otp_verify_wrong_code_returns_401(self, api_client, unique_email):
        # First, create a NEW admin via onboarding so we have a fresh OTP record
        r = api_client.post(f"{BASE_URL}/api/onboarding/start", json={
            "nome": "OTP Tester",
            "email": unique_email,
            "tipologia": "centro_studi",
            "piano_interesse": "free",
            "privacy_accepted": True,
        })
        assert r.status_code in (200, 201), r.text
        # Onboarding start creates an OTP for this user. Now try wrong code.
        # We do NOT hit the rate limit here because this is the first verify call.
        r2 = api_client.post(f"{BASE_URL}/api/auth/otp/verify", json={
            "email": unique_email, "code": "999999"
        })
        # Must be 401 with 'Codice non corretto'
        assert r2.status_code == 401, f"expected 401, got {r2.status_code} {r2.text}"
        assert "non corretto" in r2.json().get("detail", "").lower()

    def test_otp_verify_lockout_after_5_wrong(self, api_client, unique_email):
        # Create fresh account with fresh OTP
        r = api_client.post(f"{BASE_URL}/api/onboarding/start", json={
            "nome": "Lockout Tester",
            "email": unique_email,
            "tipologia": "centro_studi",
            "piano_interesse": "free",
            "privacy_accepted": True,
        })
        assert r.status_code in (200, 201)
        # 5 wrong attempts → each returns 401
        for i in range(5):
            resp = api_client.post(f"{BASE_URL}/api/auth/otp/verify", json={
                "email": unique_email, "code": "000000"
            })
            assert resp.status_code == 401, f"attempt {i+1}: got {resp.status_code}"
        # 6th attempt should return 429 (Troppi tentativi)
        resp6 = api_client.post(f"{BASE_URL}/api/auth/otp/verify", json={
            "email": unique_email, "code": "000000"
        })
        assert resp6.status_code == 429, f"6th attempt: expected 429, got {resp6.status_code} {resp6.text}"
        assert "troppi" in resp6.json().get("detail", "").lower()


# ---------- 5. Payments plans (public) -------------------------------------

class TestPaymentsPlans:
    def test_list_plans(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/payments/plans")
        assert r.status_code == 200
        plans = r.json()
        assert isinstance(plans, list)
        ids = {p["id"]: p for p in plans}
        assert "pro" in ids and "business" in ids
        assert ids["pro"]["amount"] == 29.0
        assert ids["pro"]["currency"] == "eur"
        assert ids["business"]["amount"] == 89.0
        assert ids["business"]["currency"] == "eur"


# ---------- 6. Stripe checkout session (admin required) --------------------

class TestStripeCheckout:
    """Uses the admin created via onboarding in TestOnboardingComplete."""

    def _admin_client(self, api_client):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        # login the fresh admin we made
        email = getattr(TestOnboardingStartNew, "email", None)
        assert email
        r = s.post(f"{BASE_URL}/api/auth/login", json={
            "email": email, "password": "TestPassword123!"
        })
        assert r.status_code == 200, r.text
        tok = r.json()["access_token"]
        s.headers.update({"Authorization": f"Bearer {tok}"})
        return s, r.json()

    def test_create_checkout_session_pro(self, api_client):
        s, _ = self._admin_client(api_client)
        r = s.post(f"{BASE_URL}/api/payments/checkout/session", json={
            "plan": "pro",
            "origin_url": "https://timeslot-manager-23.preview.emergentagent.com"
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "url" in data and data["url"].startswith("https://")
        assert "session_id" in data and len(data["session_id"]) > 5
        TestStripeCheckout.session_id = data["session_id"]

    def test_create_checkout_session_unauthenticated(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/payments/checkout/session", json={
            "plan": "pro",
            "origin_url": "https://timeslot-manager-23.preview.emergentagent.com"
        })
        # Should be 401 or 403
        assert r.status_code in (401, 403), f"got {r.status_code}: {r.text}"

    def test_checkout_status_invalid_session(self, api_client):
        s, _ = self._admin_client(api_client)
        r = s.get(f"{BASE_URL}/api/payments/checkout/status/nonexistent_session_id_xyz")
        assert r.status_code == 404

    def test_checkout_status_valid_session(self, api_client):
        # Poll status for the session we just created — should return payment_status/status
        sid = getattr(TestStripeCheckout, "session_id", None)
        if not sid:
            pytest.skip("no session_id available")
        s, _ = self._admin_client(api_client)
        r = s.get(f"{BASE_URL}/api/payments/checkout/status/{sid}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "payment_status" in data
        assert "status" in data
        assert data.get("plan") == "pro"

    def test_create_checkout_invalid_plan(self, api_client):
        s, _ = self._admin_client(api_client)
        r = s.post(f"{BASE_URL}/api/payments/checkout/session", json={
            "plan": "enterprise",
            "origin_url": "https://foo.com"
        })
        # 400 or 422 (pydantic validation on Literal)
        assert r.status_code in (400, 422)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
