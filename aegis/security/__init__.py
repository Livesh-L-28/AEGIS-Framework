"""AEGIS Framework Security — Fail-closed AI Trust and LLMFirewall-core integration."""

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# Try importing llmfirewall-core
try:
    from llmfirewall import Firewall as UpstreamLLMFirewall
    _LLMFIREWALL_AVAILABLE = True
except ImportError:
    _LLMFIREWALL_AVAILABLE = False


class FirewallDecisionAction(StrEnum):
    """Normalized action taken by security firewall."""

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"
    REDACT = "REDACT"


class SecurityRiskLevel(StrEnum):
    """Categorization of operational and security risk."""

    READ_ONLY = "READ_ONLY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FirewallScanResult(BaseModel):
    """Structured inspection outcome from LLM firewall."""

    allowed: bool
    action: FirewallDecisionAction
    reason: str
    risk_score: float = 0.0
    sanitized_text: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """Governed tool contract with permission controls."""

    name: str
    description: str
    risk_level: SecurityRiskLevel = SecurityRiskLevel.READ_ONLY
    is_read_only: bool = True
    parameters_schema: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ToolExecutionResult(BaseModel):
    """Outcome of governed tool execution attempt."""

    tool_name: str
    allowed: bool
    status: str  # "SUCCESS" | "DENIED" | "FAILED"
    result: Any = None
    reason: str = ""
    risk_level: SecurityRiskLevel = SecurityRiskLevel.READ_ONLY


class LLMFirewallAdapter:
    """Fail-closed adapter for llmfirewall-core 1.0.0.

    CRITICAL SECURITY INVARIANT:
    If llmfirewall-core is unavailable, misconfigured, or raises any exception,
    this adapter FAILS CLOSED (allowed = False, action = BLOCK).
    """

    def __init__(self, fail_closed: bool = True) -> None:
        self.fail_closed = fail_closed
        self._firewall: Any = None
        self._init_firewall()

    def _init_firewall(self) -> None:
        if not _LLMFIREWALL_AVAILABLE:
            return
        try:
            self._firewall = UpstreamLLMFirewall()
        except Exception:
            self._firewall = None

    def is_available(self) -> bool:
        """Check whether upstream firewall engine is initialized."""
        return _LLMFIREWALL_AVAILABLE and self._firewall is not None

    def inspect_prompt(
        self,
        prompt: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> FirewallScanResult:
        """Inspect input prompt for injection, secret leakage, or malicious instructions.

        Fails closed on error or absence of firewall.
        """
        if not self.is_available():
            if self.fail_closed:
                return FirewallScanResult(
                    allowed=False,
                    action=FirewallDecisionAction.BLOCK,
                    reason="llmfirewall-core is unavailable; failing closed for safety.",
                    sanitized_text=prompt,
                )
            return FirewallScanResult(
                allowed=True,
                action=FirewallDecisionAction.ALLOW,
                reason="Firewall bypassed (fail_closed=False).",
                sanitized_text=prompt,
            )

        try:
            res = self._firewall.check_prompt(
                prompt=prompt,
                user_id=user_id,
                session_id=session_id,
            )
            llm_action = getattr(res.decision, "action", None)
            action_name = getattr(llm_action, "name", "BLOCK") if llm_action else "BLOCK"

            if action_name == "ALLOW":
                action = FirewallDecisionAction.ALLOW
                is_allow = True
            elif action_name == "REDACT":
                action = FirewallDecisionAction.REDACT
                is_allow = True
            elif action_name == "WARN":
                action = FirewallDecisionAction.WARN
                is_allow = True
            else:
                action = FirewallDecisionAction.BLOCK
                is_allow = False

            return FirewallScanResult(
                allowed=is_allow,
                action=action,
                reason=getattr(res.decision, "reason", "Inspected by llmfirewall-core"),
                risk_score=float(getattr(res.risk_score, "score", 0.0) if hasattr(res, "risk_score") else 0.0),
                sanitized_text=getattr(res, "processed_text", prompt),
            )
        except Exception as exc:
            if self.fail_closed:
                return FirewallScanResult(
                    allowed=False,
                    action=FirewallDecisionAction.BLOCK,
                    reason=f"Firewall execution error; failing closed: {exc}",
                    sanitized_text=prompt,
                )
            return FirewallScanResult(
                allowed=True,
                action=FirewallDecisionAction.ALLOW,
                reason=f"Firewall bypassed on error: {exc}",
                sanitized_text=prompt,
            )

    def inspect_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> FirewallScanResult:
        """Inspect tool invocation call for malicious parameter injection."""
        if not self.is_available():
            if self.fail_closed:
                return FirewallScanResult(
                    allowed=False,
                    action=FirewallDecisionAction.BLOCK,
                    reason="llmfirewall-core unavailable; failing closed on tool invocation.",
                )
            return FirewallScanResult(allowed=True, action=FirewallDecisionAction.ALLOW, reason="Bypassed")

        try:
            res = self._firewall.check_tool_call(
                tool_call_or_name=tool_name,
                arguments=arguments or {},
            )
            is_allow = getattr(res, "is_allowed", False)
            return FirewallScanResult(
                allowed=is_allow,
                action=FirewallDecisionAction.ALLOW if is_allow else FirewallDecisionAction.BLOCK,
                reason=getattr(res, "reason", "Tool check completed"),
                risk_score=float(getattr(res.risk_score, "score", 0.0) if hasattr(res, "risk_score") else 0.0),
            )
        except Exception as exc:
            if self.fail_closed:
                return FirewallScanResult(
                    allowed=False,
                    action=FirewallDecisionAction.BLOCK,
                    reason=f"Firewall tool inspection exception; failing closed: {exc}",
                )
            return FirewallScanResult(allowed=True, action=FirewallDecisionAction.ALLOW, reason=str(exc))


class GovernedToolGateway:
    """Gateway enforcing deny-by-default, schema checks, and firewall boundaries."""

    def __init__(self, firewall: LLMFirewallAdapter | None = None) -> None:
        self.firewall = firewall or LLMFirewallAdapter()
        self._registry: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_tool(
        self,
        tool_def: ToolDefinition,
        handler: Callable[..., Any],
    ) -> None:
        """Register an authorized tool."""
        self._registry[tool_def.name] = tool_def
        self._handlers[tool_def.name] = handler

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolExecutionResult:
        """Execute tool strictly adhering to deny-by-default rules."""
        args = arguments or {}

        # 1. Deny unknown or unregistered tools
        if tool_name not in self._registry or not self._registry[tool_name].enabled:
            return ToolExecutionResult(
                tool_name=tool_name,
                allowed=False,
                status="DENIED",
                reason=f"Tool '{tool_name}' is not registered or disabled (Deny-by-default).",
                risk_level=SecurityRiskLevel.CRITICAL,
            )

        tool_def = self._registry[tool_name]

        # 2. Block non-read-only tools if governed execution enforces read-only trust plane
        if not tool_def.is_read_only:
            return ToolExecutionResult(
                tool_name=tool_name,
                allowed=False,
                status="DENIED",
                reason=f"Tool '{tool_name}' is mutating / dangerous. Arbitrary side effects denied.",
                risk_level=tool_def.risk_level,
            )

        # 3. Parameter schema validation
        required = tool_def.parameters_schema.get("required", [])
        for req in required:
            if req not in args:
                return ToolExecutionResult(
                    tool_name=tool_name,
                    allowed=False,
                    status="DENIED",
                    reason=f"Schema validation error: missing required param '{req}'",
                    risk_level=tool_def.risk_level,
                )

        # 4. LLM Firewall inspection
        fw_res = self.firewall.inspect_tool_call(tool_name, args)
        if not fw_res.allowed or fw_res.action == FirewallDecisionAction.BLOCK:
            return ToolExecutionResult(
                tool_name=tool_name,
                allowed=False,
                status="DENIED",
                reason=f"Security firewall blocked tool call: {fw_res.reason}",
                risk_level=tool_def.risk_level,
            )

        # 5. Safe execution
        handler = self._handlers[tool_name]
        try:
            result = handler(**args)
            return ToolExecutionResult(
                tool_name=tool_name,
                allowed=True,
                status="SUCCESS",
                result=result,
                reason="Tool executed within security boundaries.",
                risk_level=tool_def.risk_level,
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=tool_name,
                allowed=True,
                status="FAILED",
                reason=f"Tool execution exception: {exc}",
                risk_level=tool_def.risk_level,
            )


__all__ = [
    "FirewallDecisionAction",
    "FirewallScanResult",
    "GovernedToolGateway",
    "LLMFirewallAdapter",
    "SecurityRiskLevel",
    "ToolDefinition",
    "ToolExecutionResult",
]
