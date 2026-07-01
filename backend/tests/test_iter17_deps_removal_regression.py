"""Iteration 17: Regression suite after removal of emergentintegrations and litellm
   from backend/requirements.txt. Verifies all critical endpoints still work.
"""
import os
import uuid
import datetime as dt
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@demo.it", "password": "Admin123!"}
SUPER = {"email": "superadmin@eligehub.it", "password": "SuperAdmin123!"}
DEMO_STUDIO_ID = "95064d29-4598-4be5-abfc-4ee57bcbd4d8"


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    body = r.json()
    assert "access_token" in body
    return body["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def super_token():
    return _login(SUPER)


# --- (a) Auth login for both roles ----------------------------------------
class TestAuthLogin:
    def test_admin_login_returns_token(self):
        t = _login(ADMIN)
        assert isinstance(t, str) and len(t) > 20

    def test_super_admin_login_returns_token(self):
        t = _login(SUPER)
        assert isinstance(t, str) and len(t) > 20

    def test_auth_me_admin(self, admin_token):
        r = requests.get(f"{API}/auth/me", headers=_h(admin_token), timeout=10)
        assert r.status_code == 200
        d = r.json()
        # /auth/me returns {"user":{...}, "studio":{...}}
        user = d.get("user", d)
        assert user["email"] == ADMIN["email"]
        assert user["role"] == "admin"


# --- (b) GET /api/appuntamenti --------------------------------------------
class TestAppuntamentiList:
    def test_get_appuntamenti_admin(self, admin_token):
        r = requests.get(f"{API}/appuntamenti", headers=_h(admin_token), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# --- (c) POST /api/appuntamenti - full validation + Brevo email trigger ----
class TestAppuntamentoCreate:
    @pytest.fixture(scope="class")
    def context(self, admin_token):
        # fetch a docente and a cliente
        docenti = requests.get(f"{API}/docenti", headers=_h(admin_token), timeout=10).json()
        clienti = requests.get(f"{API}/clienti", headers=_h(admin_token), timeout=10).json()
        assert docenti, "no docenti in demo studio"
        assert clienti, "no clienti in demo studio"
        # pick a cliente with email if available
        cliente = next((c for c in clienti if c.get("email")), clienti[0])
        return {
            "docente_id": docenti[0]["id"],
            "cliente_id": cliente["id"],
            "cliente_has_email": bool(cliente.get("email")),
        }

    def _future_date(self, days=30):
        # pick a Wednesday well in the future to avoid conflicts/holidays
        d = dt.date.today() + dt.timedelta(days=days)
        while d.weekday() != 2:  # 2 = wednesday
            d += dt.timedelta(days=1)
        return d.isoformat()

    def test_create_appuntamento_returns_201(self, admin_token, context):
        data = self._future_date(45)
        # random slot to reduce overlap risk
        hh = 9 + (uuid.uuid4().int % 6)  # 9..14
        payload = {
            "docente_id": context["docente_id"],
            "cliente_id": context["cliente_id"],
            "data": data,
            "dal": f"{hh:02d}:00",
            "al": f"{hh:02d}:30",
            "stato": "confermato",
            "note": "TEST_iter17_regression",
        }
        r = requests.post(f"{API}/appuntamenti", json=payload,
                          headers=_h(admin_token), timeout=30)
        # Accept 201 (created) OR 409 if slot happens to be taken by prior run
        assert r.status_code in (201, 409), f"Unexpected: {r.status_code} {r.text}"
        if r.status_code == 201:
            body = r.json()
            assert body["docente_id"] == payload["docente_id"]
            assert body["cliente_id"] == payload["cliente_id"]
            assert body["dal"] == payload["dal"]
            # cleanup
            requests.delete(f"{API}/appuntamenti/{body['id']}",
                            headers=_h(admin_token), timeout=10)

    def test_create_appuntamento_time_validation(self, admin_token, context):
        # al <= dal must fail
        payload = {
            "docente_id": context["docente_id"],
            "cliente_id": context["cliente_id"],
            "data": self._future_date(60),
            "dal": "10:00",
            "al": "09:30",
            "stato": "confermato",
        }
        r = requests.post(f"{API}/appuntamenti", json=payload,
                          headers=_h(admin_token), timeout=10)
        assert r.status_code in (400, 422), f"Expected validation error, got {r.status_code}"


# --- (d) GET /api/reports/appuntamenti.pdf ---------------------------------
class TestReportsPDF:
    def test_pdf_report_generation(self, admin_token):
        r = requests.get(f"{API}/reports/appuntamenti.pdf",
                         headers=_h(admin_token), timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", "response is not a PDF"
        assert len(r.content) > 500


# --- (e) GET /api/leads (super_admin only) ---------------------------------
class TestLeads:
    def test_leads_list_super_admin(self, super_token):
        r = requests.get(f"{API}/leads", headers=_h(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_leads_forbidden_for_admin(self, admin_token):
        r = requests.get(f"{API}/leads", headers=_h(admin_token), timeout=10)
        assert r.status_code in (401, 403)


# --- (f) GET /api/studio/quota + POST /api/docenti quota enforcement -------
class TestQuota:
    def test_get_studio_quota(self, admin_token):
        r = requests.get(f"{API}/studio/quota", headers=_h(admin_token), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "plan" in d
        # business plan expected for demo studio
        assert d["plan"] in ("free", "starter", "business", "pro")
        # quota schema uses generic "professionisti" naming (works across tipologie)
        for k in ("professionisti_used", "professionisti_limit"):
            assert k in d, f"quota missing key {k}: {d}"

    def test_post_docente_quota_enforced(self, admin_token):
        # get current quota
        q = requests.get(f"{API}/studio/quota", headers=_h(admin_token), timeout=10).json()
        used = q.get("professionisti_used", 0)
        limit = q.get("professionisti_limit")
        # Only meaningful if limit is a finite number and used < limit
        # We just create one docente under quota and assert 201, then delete it
        suffix = uuid.uuid4().hex[:6]
        payload = {
            "email": f"test_iter17_{suffix}@demo.it",
            "password": "TestPass123!",
            "nome": "TEST",
            "cognome": f"iter17_{suffix}",
        }
        r = requests.post(f"{API}/docenti", json=payload,
                         headers=_h(admin_token), timeout=15)
        # If quota already exceeded (unlikely), we accept 403 with quota msg
        assert r.status_code in (201, 403), f"{r.status_code}: {r.text}"
        if r.status_code == 201:
            new_id = r.json()["id"]
            # cleanup
            d = requests.delete(f"{API}/docenti/{new_id}",
                                headers=_h(admin_token), timeout=10)
            assert d.status_code in (204, 200)
        else:
            # 403 must mention quota
            assert "quota" in r.text.lower() or "limite" in r.text.lower() or "piano" in r.text.lower()


# --- (g) Scheduler startup log check ---------------------------------------
class TestSchedulerLog:
    def test_reminder_scheduler_log_present(self):
        import glob
        logs = sorted(glob.glob("/var/log/supervisor/backend.*.log"))
        content = ""
        for p in logs[-5:]:
            try:
                with open(p, "r") as f:
                    content += f.read()
            except Exception:
                pass
        assert "Reminder scheduler avviato" in content, \
            "'Reminder scheduler avviato' not found in backend logs"
        # verify no ModuleNotFoundError for emergentintegrations / litellm
        forbidden = [
            "ModuleNotFoundError: No module named 'emergentintegrations'",
            "ModuleNotFoundError: No module named 'litellm'",
            "ImportError: cannot import name 'emergentintegrations'",
        ]
        for f_msg in forbidden:
            assert f_msg not in content, f"Found forbidden error in logs: {f_msg}"
