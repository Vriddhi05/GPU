"""Deterministic synthetic telemetry and explainable anomaly detection."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import math
import random
from .schemas import Anomaly, GPU, LogEntry, TelemetryRecord

GPU_IDS = ["GPU-01", "GPU-02", "GPU-03", "GPU-04"]
THRESHOLDS = {"GPU-01": 75.0, "GPU-02": 75.0, "GPU-03": 85.0, "GPU-04": 75.0}
START = datetime(2025, 1, 20, 10, 0, tzinfo=timezone.utc)

def generate_telemetry(seed: int = 2025, count: int = 49) -> list[TelemetryRecord]:
    """Generate stable device readings; GPU-03 includes a controlled heat event."""
    rng = random.Random(seed)
    baselines = {"GPU-01": 55.0, "GPU-02": 53.0, "GPU-03": 65.0, "GPU-04": 58.0}
    utilization = {"GPU-01": 68.0, "GPU-02": 57.0, "GPU-03": 91.0, "GPU-04": 46.0}
    memory = {"GPU-01": 11.2, "GPU-02": 13.5, "GPU-03": 20.1, "GPU-04": 9.8}
    output: list[TelemetryRecord] = []
    for index in range(count):
        for gpu_index, gpu_id in enumerate(GPU_IDS):
            rise = max(0, index - 25) * (0.5 if gpu_id == "GPU-03" else 0.0)
            temp = baselines[gpu_id] + math.sin(index * 0.43 + gpu_index) * 2.1 + index * 0.1 + rise
            if gpu_id == "GPU-03" and index >= count - 3:
                temp += 16.0
            temp = round(temp + rng.uniform(-0.35, 0.35), 1)
            err = 2 if (gpu_id == "GPU-03" and index in (count - 3, count - 2)) else 0
            output.append(TelemetryRecord(
                record_id=f"REC-{gpu_index + 1:02d}-{index + 1:03d}",
                timestamp=START + timedelta(minutes=index), gpu_id=gpu_id,
                temperature_c=temp,
                utilization_pct=round(min(99.0, max(15.0, utilization[gpu_id] + math.sin(index * .17 + gpu_index) * 5)), 1),
                memory_used_gb=round(min(23.8, memory[gpu_id] + math.sin(index * .11 + gpu_index) * .45), 1),
                memory_total_gb=24.0, error_count=err,
            ))
    return output

def severity_for(rule: str, observed: float, threshold: float, error_count: int = 0) -> str:
    """High: >=10 C over limit or >=3 errors; Medium: >=5 C or >=2 errors; else Low."""
    if rule == "error_count":
        return "High" if error_count >= 3 else "Medium" if error_count >= 2 else "Low"
    delta = observed - threshold
    return "High" if delta >= 10 else "Medium" if delta >= 5 else "Low"

def detect_anomalies(records: list[TelemetryRecord], sustained_readings: int = 3) -> list[Anomaly]:
    """Create threshold, sustained heat, and error-count alerts with source records."""
    anomalies: list[Anomaly] = []
    sorted_records = sorted(records, key=lambda r: (r.timestamp, r.gpu_id))
    by_gpu: dict[str, list[TelemetryRecord]] = {gpu: [] for gpu in GPU_IDS}
    for record in sorted_records:
        by_gpu.setdefault(record.gpu_id, []).append(record)
        threshold = THRESHOLDS.get(record.gpu_id, 75.0)
        if record.temperature_c > threshold:
            anomalies.append(_anomaly(record, "temperature_threshold", threshold,
                                      f"Observed temperature exceeded the {threshold:.1f} °C threshold."))
        if record.error_count >= 2:
            anomalies.append(_anomaly(record, "error_count", 2.0,
                                      f"Abnormal error count: {record.error_count} errors in one reading.", record.error_count))
    for gpu_id, readings in by_gpu.items():
        for end in range(sustained_readings - 1, len(readings)):
            window = readings[end - sustained_readings + 1:end + 1]
            threshold = THRESHOLDS.get(gpu_id, 75.0)
            if all(r.temperature_c > threshold for r in window):
                record = window[-1]
                anomalies.append(_anomaly(record, "sustained_temperature", threshold,
                    f"Temperature stayed above {threshold:.1f} °C for {sustained_readings} consecutive readings."))
                break
    anomalies.sort(key=lambda a: a.timestamp, reverse=True)
    return anomalies

def _anomaly(record: TelemetryRecord, rule: str, threshold: float, description: str, error_count: int = 0) -> Anomaly:
    observed = float(error_count if rule == "error_count" else record.temperature_c)
    sev = severity_for(rule, observed, threshold, error_count)
    return Anomaly(id=f"AN-{record.gpu_id[-2:]}-{record.record_id[-3:]}-{rule[:3].upper()}",
        gpu_id=record.gpu_id, timestamp=record.timestamp, observed_value=observed,
        threshold=threshold, severity=sev, description=description, rule=rule,
        source_record_id=record.record_id, source_record=record)

def build_gpus(records: list[TelemetryRecord]) -> list[GPU]:
    latest: dict[str, TelemetryRecord] = {}
    for record in records:
        if record.gpu_id not in latest or record.timestamp > latest[record.gpu_id].timestamp:
            latest[record.gpu_id] = record
    return [GPU(id=gpu, temperature_c=latest[gpu].temperature_c,
        utilization_pct=latest[gpu].utilization_pct, memory_used_gb=latest[gpu].memory_used_gb,
        threshold_c=THRESHOLDS[gpu], health="Elevated" if latest[gpu].temperature_c >= THRESHOLDS[gpu] else "Normal")
        for gpu in GPU_IDS]

def build_logs(anomalies: list[Anomaly]) -> list[LogEntry]:
    return [LogEntry(id=f"LOG-{a.id}", timestamp=a.timestamp, gpu_id=a.gpu_id,
        event_type=a.rule, severity=a.severity, message=a.description, anomaly_id=a.id) for a in anomalies]
