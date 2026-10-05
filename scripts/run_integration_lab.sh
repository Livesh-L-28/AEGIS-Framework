#!/usr/bin/env bash
set -euo pipefail

# AEGIS Framework v0.1.0 — Real Infrastructure Lab Automation Script

echo "======================================================================"
echo "AEGIS Framework v0.1.0 — Real Infrastructure Integration Lab"
echo "======================================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cleanup() {
    echo ""
    echo "[Cleanup] Stopping integration containers..."
    docker compose -f integration/docker-compose.yml down --remove-orphans > /dev/null 2>&1 || true
    echo "[Cleanup] Completed."
}

trap cleanup EXIT

# 1. Check Prerequisites
echo "[Step 1] Checking prerequisites..."
if ! command -v docker > /dev/null 2>&1; then
    echo "ERROR: docker command not found in PATH." >&2
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running." >&2
    exit 1
fi

echo "  -> Docker daemon is running."

# 2. Start Observability & Demo Stack
echo "[Step 2] Starting local Prometheus, Loki, and Demo Workload on isolated ports..."
docker compose -f integration/docker-compose.yml up -d

# 3. Wait for Readiness
echo "[Step 3] Waiting for service readiness..."
for i in {1..30}; do
    if curl -s http://localhost:18080/health > /dev/null 2>&1 && \
       curl -s http://localhost:19090/-/ready > /dev/null 2>&1 && \
       curl -s http://localhost:3100/ready > /dev/null 2>&1; then
        echo "  -> All integration services are READY!"
        break
    fi
    sleep 1
done

# 4. Run Pytest Integration Suite
echo "[Step 4] Running Pytest Real Infrastructure Integration Suite..."
.venv/bin/pytest -m integration -v

# 5. Run Full Autonomous Investigation & Remediation Lab
echo "[Step 5] Running Full Autonomous Incident Investigation & Remediation Lab..."
.venv/bin/python integration/run_lab.py

echo ""
echo "======================================================================"
echo "INTEGRATION LAB COMPLETED: ALL PROVIDERS VALIDATED AGAINST REAL SERVICES"
echo "======================================================================"
