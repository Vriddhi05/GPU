from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .schemas import Anomaly, Config, GPU, LogEntry, Summary, TelemetryRecord
from .telemetry import GPU_IDS, THRESHOLDS, build_gpus, build_logs, detect_anomalies, generate_telemetry

app = FastAPI(title="GPU Health Review API", version="1.0.0", description="Synthetic GPU telemetry and explainable anomaly events.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_methods=["*"], allow_headers=["*"])
RECORDS = generate_telemetry()
ANOMALIES = detect_anomalies(RECORDS)
LOGS = build_logs(ANOMALIES)

@app.get("/api/health")
def health(): return {"status": "ok", "mode": "synthetic", "version": app.version}

@app.get("/api/gpus", response_model=list[GPU])
def gpus(): return build_gpus(RECORDS)

@app.get("/api/telemetry", response_model=list[TelemetryRecord])
def telemetry(gpu_id: str | None = None, limit: int = Query(500, ge=1, le=2000)):
    if gpu_id and gpu_id not in GPU_IDS: raise HTTPException(404, detail=f"Unknown GPU identifier: {gpu_id}")
    rows = [r for r in RECORDS if not gpu_id or r.gpu_id == gpu_id]
    return rows[-limit:]

@app.get("/api/telemetry/{gpu_id}", response_model=list[TelemetryRecord])
def telemetry_for_gpu(gpu_id: str):
    if gpu_id not in GPU_IDS: raise HTTPException(404, detail=f"Unknown GPU identifier: {gpu_id}")
    return [r for r in RECORDS if r.gpu_id == gpu_id]

@app.get("/api/anomalies", response_model=list[Anomaly])
def anomalies(gpu_id: str | None = None, severity: str | None = None):
    if gpu_id and gpu_id not in GPU_IDS: raise HTTPException(404, detail=f"Unknown GPU identifier: {gpu_id}")
    if severity and severity.title() not in {"Low", "Medium", "High"}: raise HTTPException(422, detail="severity must be Low, Medium, or High")
    return [a for a in ANOMALIES if (not gpu_id or a.gpu_id == gpu_id) and (not severity or a.severity == severity.title())]

@app.get("/api/anomalies/{anomaly_id}", response_model=Anomaly)
def anomaly(anomaly_id: str):
    for item in ANOMALIES:
        if item.id == anomaly_id: return item
    raise HTTPException(404, detail="Anomaly not found")

@app.get("/api/logs", response_model=list[LogEntry])
def logs(gpu_id: str | None = None, severity: str | None = None):
    if gpu_id and gpu_id not in GPU_IDS: raise HTTPException(404, detail=f"Unknown GPU identifier: {gpu_id}")
    return [l for l in LOGS if (not gpu_id or l.gpu_id == gpu_id) and (not severity or l.severity == severity.title())]

@app.get("/api/summary", response_model=Summary)
def summary():
    return Summary(gpus=build_gpus(RECORDS), anomaly_count=len(ANOMALIES), error_count=sum(r.error_count for r in RECORDS), generated_at=datetime.now(timezone.utc))

@app.get("/api/config", response_model=Config)
def config():
    return Config(temperature_thresholds=THRESHOLDS, sustained_readings=3,
        severity_rules={"low": "below 5 °C over threshold", "medium": "5–9.9 °C over threshold or 2 errors", "high": "10+ °C over threshold or 3+ errors"})
