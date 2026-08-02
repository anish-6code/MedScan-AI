#!/usr/bin/env python3
"""
scripts/device_simulator.py

Simulates a bedside IoT device posting vitals readings every N seconds.
Useful for demonstrating real-time dashboard updates without real hardware.

Usage:
    # Inside Docker or with API running locally:
    python scripts/device_simulator.py --patient-id <uuid> --interval 5
    python scripts/device_simulator.py --patient-id <uuid> --interval 2 --anomaly

Environment:
    API_URL   — base URL of the FastAPI backend (default: http://localhost:8000)
    API_TOKEN — JWT token for authentication
"""
import argparse
import math
import os
import random
import sys
import time

import requests

API_URL   = os.environ.get("API_URL",   "http://localhost:8000")
API_TOKEN = os.environ.get("API_TOKEN", "")


def _headers() -> dict:
    if not API_TOKEN:
        print("⚠  API_TOKEN env var not set — requests will likely 401", file=sys.stderr)
    return {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}


# ── Physiological ranges ───────────────────────────────────────────────────────

NORMAL = {
    "heart_rate":       (65, 85),
    "spo2":             (96, 99),
    "systolic_bp":      (110, 130),
    "diastolic_bp":     (70, 85),
    "temperature":      (36.4, 37.2),
    "respiratory_rate": (14, 18),
}

ANOMALY = {
    "heart_rate":       (110, 145),   # tachycardia
    "spo2":             (88, 93),     # hypoxemia
    "systolic_bp":      (160, 185),   # hypertensive
    "diastolic_bp":     (100, 120),
    "temperature":      (38.5, 40.1), # fever
    "respiratory_rate": (24, 32),     # tachypnea
}


def _generate(t: int, anomaly: bool) -> dict:
    """Generate one plausible reading with slight sinusoidal drift."""
    ranges = ANOMALY if anomaly else NORMAL
    reading = {}
    for key, (lo, hi) in ranges.items():
        mid = (lo + hi) / 2
        amp = (hi - lo) / 4
        drift = amp * math.sin(t / 20)            # slow oscillation
        noise = random.uniform(-amp * 0.2, amp * 0.2)
        reading[key] = round(mid + drift + noise, 1)
    return reading


def run(patient_id: str, interval: float, anomaly: bool, count: int) -> None:
    url = f"{API_URL}/vitals/{patient_id}"
    print(f"🩺 Simulator started → {url}")
    print(f"   Mode: {'⚠ ANOMALY' if anomaly else '✓ NORMAL'}  |  interval: {interval}s  |  count: {count or '∞'}\n")

    sent = 0
    try:
        while count == 0 or sent < count:
            payload = {
                "source": "simulator",
                **_generate(sent, anomaly),
            }
            try:
                r = requests.post(url, json=payload, headers=_headers(), timeout=5)
                if r.status_code == 201:
                    d = r.json()
                    print(
                        f"[{sent:04d}] ♥ {d['heart_rate']} bpm | "
                        f"SpO₂ {d['spo2']}% | "
                        f"BP {d['systolic_bp']}/{d['diastolic_bp']} | "
                        f"Temp {d['temperature']}°C | "
                        f"RR {d['respiratory_rate']}"
                    )
                else:
                    print(f"[{sent:04d}] ✗ HTTP {r.status_code}: {r.text[:120]}", file=sys.stderr)
            except requests.RequestException as e:
                print(f"[{sent:04d}] ✗ Request failed: {e}", file=sys.stderr)

            sent += 1
            if count == 0 or sent < count:
                time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n⏹  Stopped after {sent} readings.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="MedScan vitals device simulator")
    p.add_argument("--patient-id", required=True,      help="Patient UUID")
    p.add_argument("--interval",   type=float, default=5.0, help="Seconds between readings")
    p.add_argument("--anomaly",    action="store_true", help="Send out-of-range values")
    p.add_argument("--count",      type=int,   default=0,   help="Number of readings (0=infinite)")
    args = p.parse_args()
    run(args.patient_id, args.interval, args.anomaly, args.count)
