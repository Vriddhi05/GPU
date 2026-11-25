from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import TelemetryRecord
from backend.telemetry import detect_anomalies, generate_telemetry, severity_for

client = TestClient(app)

def test_generation_is_reproducible_and_complete():
    assert generate_telemetry() == generate_telemetry()
    records = generate_telemetry()
    assert len(records) == 49 * 4
    assert {r.gpu_id for r in records} == {"GPU-01", "GPU-02", "GPU-03", "GPU-04"}

def test_threshold_detection_is_explainable_and_traceable():
    alerts = detect_anomalies(generate_telemetry())
    assert alerts
    for alert in alerts:
        assert alert.source_record.record_id == alert.source_record_id
        assert alert.source_record.gpu_id == alert.gpu_id
        assert alert.rule in {"temperature_threshold", "sustained_temperature", "error_count"}

def test_sustained_temperature_detection():
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    records = [TelemetryRecord(record_id=f"r{i}", timestamp=start + timedelta(minutes=i), gpu_id="GPU-01", temperature_c=80, utilization_pct=60, memory_used_gb=8, memory_total_gb=24, error_count=0) for i in range(3)]
    assert any(a.rule == "sustained_temperature" for a in detect_anomalies(records))

def test_error_detection_and_severity():
    assert severity_for("error_count", 3, 1, 3) == "High"
    assert severity_for("temperature_threshold", 83, 75) == "Medium"
    assert severity_for("temperature_threshold", 77, 75) == "Low"
    assert any(a.rule == "error_count" for a in detect_anomalies(generate_telemetry()))

def test_api_health_and_validation():
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/gpus").json()) == 4
    assert client.get("/api/telemetry/GPU-99").status_code == 404
    assert client.get("/api/anomalies", params={"severity": "critical"}).status_code == 422

def test_api_filtering_and_sort_order():
    response = client.get("/api/anomalies", params={"gpu_id": "GPU-03", "severity": "high"})
    rows = response.json()
    assert rows and all(r["gpu_id"] == "GPU-03" and r["severity"] == "High" for r in rows)
    assert [r["timestamp"] for r in rows] == sorted([r["timestamp"] for r in rows], reverse=True)
