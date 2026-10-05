"""Lightweight demo microservice using standard library http.server exposing metrics and traces."""

import json
import os
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

SERVICE_NAME = os.getenv("SERVICE_NAME", "demo-service")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")

# State
incident_mode = False
request_count = 0
error_count = 0
total_latency_seconds = 0.0

# Store recent traces in Jaeger format for query compatibility
stored_traces: list[dict] = []


def push_loki_log(level: str, message: str, service: str = SERVICE_NAME):
    """Push structured log directly to Loki push API."""
    ts_ns = str(time.time_ns())
    payload = {
        "streams": [
            {
                "stream": {
                    "service": service,
                    "app": service,
                    "level": level,
                },
                "values": [[ts_ns, message]],
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LOKI_URL}/loki/api/v1/push",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=1.0):
            pass
    except Exception:
        pass


def record_trace(span_name: str, duration_ms: float, is_error: bool = False, error_msg: str | None = None):
    """Store trace span in Jaeger HTTP API format."""
    trace_id = uuid.uuid4().hex[:16]
    root_span_id = uuid.uuid4().hex[:16]
    child_span_id = uuid.uuid4().hex[:16]
    now_us = int(time.time() * 1_000_000)

    # 1. Root span (HTTP request)
    tags = [
        {"key": "http.method", "type": "string", "value": "GET"},
        {"key": "service.name", "type": "string", "value": SERVICE_NAME},
    ]
    if is_error:
        tags.append({"key": "error", "type": "bool", "value": True})
        if error_msg:
            tags.append({"key": "error.message", "type": "string", "value": error_msg})

    root_span = {
        "traceID": trace_id,
        "spanID": root_span_id,
        "operationName": span_name,
        "startTime": now_us,
        "duration": int(duration_ms * 1000),
        "tags": tags,
        "references": [],
    }

    # 2. Child span (Simulated DB / Downstream)
    child_tags = [
        {"key": "db.system", "type": "string", "value": "postgresql"},
    ]
    if is_error:
        child_tags.append({"key": "error", "type": "bool", "value": True})
        child_tags.append({"key": "error.message", "type": "string", "value": error_msg or "timeout"})

    child_span = {
        "traceID": trace_id,
        "spanID": child_span_id,
        "operationName": "database_query",
        "startTime": now_us + 1000,
        "duration": int(max(duration_ms - 2.0, 1.0) * 1000),
        "tags": child_tags,
        "references": [{"refType": "CHILD_OF", "traceID": trace_id, "spanID": root_span_id}],
    }

    trace = {
        "traceID": trace_id,
        "spans": [root_span, child_span],
    }
    stored_traces.append(trace)
    if len(stored_traces) > 200:
        stored_traces.pop(0)


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default request logging
        return

    def do_GET(self):
        global request_count, error_count, total_latency_seconds, incident_mode

        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": SERVICE_NAME, "incident_mode": incident_mode}).encode("utf-8"))
            return

        if self.path == "/metrics":
            avg_latency = (total_latency_seconds / request_count) if request_count > 0 else 0.0
            lines = [
                '# HELP http_requests_total Total number of HTTP requests.',
                '# TYPE http_requests_total counter',
                f'http_requests_total{{service="{SERVICE_NAME}"}} {request_count}',
                '# HELP http_errors_total Total number of HTTP 5xx errors.',
                '# TYPE http_errors_total counter',
                f'http_errors_total{{service="{SERVICE_NAME}"}} {error_count}',
                '# HELP http_request_duration_seconds Average latency in seconds.',
                '# TYPE http_request_duration_seconds gauge',
                f'http_request_duration_seconds{{service="{SERVICE_NAME}"}} {avg_latency}',
            ]
            body = "\n".join(lines) + "\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
            return

        if self.path.startswith("/api/traces"):
            only_errors = "error" in self.path
            matched = []
            for t in stored_traces:
                if only_errors:
                    has_err = any(any(tag.get("key") == "error" and tag.get("value") is True for tag in s.get("tags", [])) for s in t.get("spans", []))
                    if not has_err:
                        continue
                matched.append(t)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"data": matched}).encode("utf-8"))
            return

        if self.path.startswith("/api/request"):
            start = time.perf_counter()
            request_count += 1
            if incident_mode:
                time.sleep(0.1)
                error_count += 1
                dur = (time.perf_counter() - start) * 1000
                total_latency_seconds += dur / 1000
                msg = "database_timeout: Connection to replica pool timed out after 5000ms"
                push_loki_log("ERROR", msg)
                record_trace("GET /api/request", dur, is_error=True, error_msg=msg)
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "database_timeout", "incident_mode": True}).encode("utf-8"))
                return

            dur = (time.perf_counter() - start) * 1000
            total_latency_seconds += dur / 1000
            push_loki_log("INFO", "request_completed: HTTP 200 OK")
            record_trace("GET /api/request", dur, is_error=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "latency_ms": round(dur, 2)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        global incident_mode
        if self.path == "/api/incident":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                data = {}
            incident_mode = data.get("enabled", not incident_mode)
            level = "ERROR" if incident_mode else "INFO"
            push_loki_log(level, f"Incident mode changed to: {incident_mode}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"incident_mode": incident_mode}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), RequestHandler)
    server.serve_forever()
