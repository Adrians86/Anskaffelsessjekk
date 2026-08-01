"""B1/B7 — FastAPI endpoint tests (httpx TestClient against the real engine)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_stats_endpoint():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "kpi" in data and "health" in data
    kpi = data["kpi"]
    assert kpi["total_invoices"] >= 4
    assert kpi["verdi_funnet"] == pytest.approx(22310.0, abs=1)


def test_invoices_list():
    r = client.get("/api/invoices")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 4
    first = rows[0]
    assert "invoice_number" in first
    assert "verdict" in first
    assert first["verdict"] in ("AVVIK", "TIL_VURDERING", "SAMSVAR")


def test_invoices_filter_verdict():
    r = client.get("/api/invoices?verdict=AVVIK")
    assert r.status_code == 200
    rows = r.json()
    assert all(row["verdict"] == "AVVIK" for row in rows)


def test_invoices_search():
    r = client.get("/api/invoices?search=F-1003")
    assert r.status_code == 200
    rows = r.json()
    assert any("F-1003" in row["invoice_number"] for row in rows)


def test_invoice_detail():
    listing = client.get("/api/invoices").json()
    inv_id = listing[0]["id"]
    r = client.get(f"/api/invoices/{inv_id}")
    assert r.status_code == 200
    data = r.json()
    assert "findings" in data
    assert "lines" in data
    assert data["verdict"] in ("AVVIK", "TIL_VURDERING", "SAMSVAR")


def test_invoice_detail_not_found():
    r = client.get("/api/invoices/99999")
    assert r.status_code == 404


def test_suppliers_list():
    r = client.get("/api/suppliers")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 2
    assert "name" in rows[0]
    assert "org_number" in rows[0]


def test_suppliers_search():
    r = client.get("/api/suppliers?search=Hydraulikk")
    assert r.status_code == 200
    rows = r.json()
    assert any("Hydraulikk" in row["name"] for row in rows)


def test_supplier_detail():
    listing = client.get("/api/suppliers").json()
    sup_id = listing[0]["id"]
    r = client.get(f"/api/suppliers/{sup_id}")
    assert r.status_code == 200
    data = r.json()
    assert "invoices" in data
    assert "contracts" in data


def test_supplier_not_found():
    r = client.get("/api/suppliers/99999")
    assert r.status_code == 404
