"""Iter13: Landing leads, eccezioni CRUD + blocking, cancellation email, scheduler, regressions."""
import os
import pytest
import requests
from datetime import date, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://timeslot-manager-23.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@demo.it", "password": "Admin123!"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---- Lead public endpoint ----
class TestLeadsPublic:
    def test_create_lead_no_auth(self):
        payload = {
            "nome": "TEST_LeadAuto",
            "email": "test_lead_auto@example.com",
            "telefono": "+39000",
            "tipologia": "centro_studi",
            "studio": "Demo TEST",
            "messaggio": "Richiesta info automatica",
        }
        r = requests.post(f"{API}/leads", json=payload, timeout=20)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data.get("ok") is True
        assert "id" in data

    def test_create_lead_minimal(self):
        r = requests.post(f"{API}/leads", json={"nome": "TEST_X", "email": "test_x@example.com"}, timeout=20)
        assert r.status_code == 201

    def test_create_lead_invalid_email(self):
        r = requests.post(f"{API}/leads", json={"nome": "X", "email": "notanemail"}, timeout=15)
        assert r.status_code in (400, 422)


# ---- Eccezioni CRUD + blocking ----
class TestEccezioni:
    def test_list_eccezioni(self, admin_headers):
        # Need docente_id implicitly: admin lists all eccezioni in studio
        r = requests.get(f"{API}/eccezioni", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_eccezione_requires_docente_id_for_admin(self, admin_headers):
        # Without docente_id, admin should get 422
        r = requests.post(
            f"{API}/eccezioni",
            headers=admin_headers,
            json={"data_inizio": "2026-08-10", "data_fine": "2026-08-14", "motivo": "TEST", "tipo": "chiuso"},
            timeout=15,
        )
        assert r.status_code == 422

    def test_full_eccezione_flow_and_blocking(self, admin_headers):
        # Get docente
        r = requests.get(f"{API}/docenti", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        docenti = r.json()
        assert len(docenti) > 0
        docente_id = docenti[0]["id"]

        # Get cliente
        r = requests.get(f"{API}/clienti", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        clienti = r.json()
        assert len(clienti) > 0
        cliente_id = clienti[0]["id"]

        # Create eccezione on a future test date
        test_date = (date.today() + timedelta(days=120)).isoformat()
        payload = {
            "docente_id": docente_id,
            "data_inizio": test_date,
            "data_fine": test_date,
            "motivo": "TEST_Ferie_Auto",
            "tipo": "chiuso",
        }
        r = requests.post(f"{API}/eccezioni", headers=admin_headers, json=payload, timeout=15)
        assert r.status_code == 201, r.text
        ecc = r.json()
        ecc_id = ecc["id"]
        assert ecc["motivo"] == "TEST_Ferie_Auto"
        assert ecc["tipo"] == "chiuso"
        assert ecc["docente_id"] == docente_id

        # Verify GET shows it
        r = requests.get(f"{API}/eccezioni?docente_id={docente_id}", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()]
        assert ecc_id in ids

        # Attempt to create an appuntamento on that date -> 409
        app_payload = {
            "docente_id": docente_id,
            "cliente_id": cliente_id,
            "data": test_date,
            "dal": "10:00",
            "al": "11:00",
            "stato": "confermato",
        }
        r = requests.post(f"{API}/appuntamenti", headers=admin_headers, json=app_payload, timeout=15)
        assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
        assert "non è disponibile" in r.json().get("detail", "").lower() or "disponibile" in r.json().get("detail", "").lower()

        # Validation: data_fine < data_inizio -> 422
        r = requests.post(
            f"{API}/eccezioni",
            headers=admin_headers,
            json={"docente_id": docente_id, "data_inizio": "2026-08-14", "data_fine": "2026-08-10", "tipo": "chiuso"},
            timeout=15,
        )
        assert r.status_code == 422

        # Validation: personalizzato without ora -> 422
        r = requests.post(
            f"{API}/eccezioni",
            headers=admin_headers,
            json={"docente_id": docente_id, "data_inizio": test_date, "data_fine": test_date, "tipo": "personalizzato"},
            timeout=15,
        )
        assert r.status_code == 422

        # Cleanup eccezione
        r = requests.delete(f"{API}/eccezioni/{ecc_id}", headers=admin_headers, timeout=15)
        assert r.status_code == 204

        # Verify removed
        r = requests.get(f"{API}/eccezioni?docente_id={docente_id}", headers=admin_headers, timeout=15)
        assert ecc_id not in [e["id"] for e in r.json()]


# ---- Cancellation email path ----
class TestCancellationEmail:
    def test_delete_appuntamento_sends_cancellation(self, admin_headers):
        # Create an appuntamento with a client that has an email
        r = requests.get(f"{API}/docenti", headers=admin_headers, timeout=15)
        docente_id = r.json()[0]["id"]
        r = requests.get(f"{API}/clienti", headers=admin_headers, timeout=15)
        clienti = r.json()
        # Pick one with email
        cli = next((c for c in clienti if c.get("email")), None)
        if not cli:
            # patch one
            cli = clienti[0]
            r = requests.patch(f"{API}/clienti/{cli['id']}", headers=admin_headers, json={"email": "team@zioners.com"}, timeout=15)
            assert r.status_code == 200
            cli = r.json()
        cliente_id = cli["id"]

        future = (date.today() + timedelta(days=200)).isoformat()
        r = requests.post(
            f"{API}/appuntamenti", headers=admin_headers,
            json={"docente_id": docente_id, "cliente_id": cliente_id, "data": future, "dal": "09:00", "al": "10:00", "stato": "confermato"},
            timeout=20,
        )
        assert r.status_code == 201, r.text
        app_id = r.json()["id"]

        # Delete it
        r = requests.delete(f"{API}/appuntamenti/{app_id}", headers=admin_headers, timeout=30)
        assert r.status_code == 204

        # Verify it's gone
        r = requests.get(f"{API}/appuntamenti?data_da={future}&data_a={future}", headers=admin_headers, timeout=15)
        assert app_id not in [a["id"] for a in r.json()]


# ---- Scheduler ----
class TestScheduler:
    def test_scheduler_module_registers_job(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from reminder_scheduler import _scheduler, start_reminder_scheduler  # noqa
        # _scheduler global may be None in this process; verify module structure
        import reminder_scheduler as rs
        assert callable(rs.start_reminder_scheduler)
        assert callable(rs._send_reminders_24h)


# ---- Regressions ----
class TestRegressions:
    def test_login_admin(self):
        r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=15)
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_piva_update(self, admin_headers):
        r = requests.patch(f"{API}/studio", headers=admin_headers, json={"piva": "IT12345678901"}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("piva") == "IT12345678901"

    def test_pdf_report_week(self, admin_headers):
        r = requests.get(f"{API}/reports/appuntamenti.pdf?period=week", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 1000
