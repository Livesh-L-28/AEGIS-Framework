"""Framework-neutral GitHub webhook verification and event ingestion abstraction.

Decoupled from specific web servers (FastAPI, Flask, etc.). Applications pass
raw payload bytes, event header, and HMAC signature for validation.
"""

import hashlib
import hmac
import json
from typing import Any

from pydantic import BaseModel, Field


class WebhookIngestResult(BaseModel):
    """Normalized output from webhook ingestion."""

    valid: bool
    event_type: str
    action: str = ""
    repository: str = ""
    sender: str = ""
    deployment_info: dict[str, Any] = Field(default_factory=dict)
    commit_info: dict[str, Any] = Field(default_factory=dict)
    raw_event: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class GitHubWebhookHandler:
    """Verifies HMAC SHA-256 signatures and normalizes GitHub push, PR, and deployment events."""

    def __init__(self, secret: str | None = None) -> None:
        self.secret = secret

    def verify_signature(self, payload_bytes: bytes, signature_header: str | None) -> bool:
        """Validate GitHub X-Hub-Signature-256 HMAC."""
        if not self.secret:
            # If no secret configured, allow (e.g. testing)
            return True
        if not signature_header:
            return False

        if not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header[7:]
        computed_sig = hmac.new(
            self.secret.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed_sig, expected_sig)

    def process_webhook(
        self,
        event_name: str,
        payload_bytes: bytes,
        signature_header: str | None = None,
    ) -> WebhookIngestResult:
        """Ingest and normalize GitHub webhook event."""
        if not self.verify_signature(payload_bytes, signature_header):
            return WebhookIngestResult(
                valid=False,
                event_type=event_name,
                error="Invalid HMAC SHA-256 signature",
            )

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            return WebhookIngestResult(
                valid=False,
                event_type=event_name,
                error=f"Malformed JSON payload: {e}",
            )

        repo = payload.get("repository", {}).get("full_name", "")
        sender = payload.get("sender", {}).get("login", "")
        action = payload.get("action", "")

        dep_info: dict[str, Any] = {}
        commit_info: dict[str, Any] = {}

        if event_name == "deployment":
            dep = payload.get("deployment", {})
            dep_info = {
                "deployment_id": str(dep.get("id")),
                "ref": dep.get("ref"),
                "sha": dep.get("sha"),
                "environment": dep.get("environment"),
                "created_at": dep.get("created_at"),
            }
        elif event_name == "deployment_status":
            dep_status = payload.get("deployment_status", {})
            dep = payload.get("deployment", {})
            dep_info = {
                "deployment_id": str(dep.get("id")),
                "status": dep_status.get("state"),
                "sha": dep.get("sha"),
                "environment": dep_status.get("environment"),
            }
        elif event_name == "push":
            commit_info = {
                "ref": payload.get("ref"),
                "before": payload.get("before"),
                "after": payload.get("after"),
                "head_commit": payload.get("head_commit", {}),
            }

        return WebhookIngestResult(
            valid=True,
            event_type=event_name,
            action=action,
            repository=repo,
            sender=sender,
            deployment_info=dep_info,
            commit_info=commit_info,
            raw_event=payload,
        )


__all__ = ["GitHubWebhookHandler", "WebhookIngestResult"]
