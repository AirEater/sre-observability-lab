from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_root_returns_200():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "sre-observability-demo"

def test_healthz_returns_200():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_returns_200():
    resp = client.get("/readyz")
    assert resp.status_code == 200


def test_simulate_error_returns_500():
    resp = client.get("/simulate-error")
    assert resp.status_code == 500


def test_simulate_cpu_returns_200():
    resp = client.get("/simulate-cpu")
    assert resp.status_code == 200
    assert resp.json()["status"] == "hot"


def test_simulate_latency_returns_200():
    with patch("app.main.time.sleep"):
        resp = client.get("/simulate-latency")
    assert resp.status_code == 200
    assert resp.json()["status"] == "slow"


def test_metrics_endpoint_exposes_prometheus_format():
    # 先打几次别的 endpoint,让 instrumentator 产生数据
    client.get("/")
    client.get("/healthz")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Prometheus exposition format 是 plaintext,直接 substring 检查即可
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


def test_simulated_incidents_counter_increments():
    # Counter 必须先 .inc() 一次才会出现在 /metrics 里
    client.get("/simulate-error")

    resp = client.get("/metrics")
    assert "simulated_incidents_total" in resp.text
    assert 'type="error"' in resp.text