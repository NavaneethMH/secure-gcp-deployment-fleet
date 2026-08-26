"""
Local Model Armor-compatible security layer.

Provides:
- User prompt sanitization
- Model response sanitization
- Prompt injection detection
- Jailbreak detection
- Sensitive-data redaction
- Generic sanitize() API
- Security status reporting
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArmorResult:
    allowed: bool
    sanitized_text: str
    reason: str
    provider: str = "local"
    violations: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return not self.allowed


# ---------------------------------------------------------------------------
# Security patterns
# ---------------------------------------------------------------------------

PROMPT_INJECTION_PATTERNS = (
    re.compile(
        r"\bignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdisregard\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bforget\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\breveal\s+(?:the\s+)?system\s+prompt\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bshow\s+(?:me\s+)?(?:the\s+)?system\s+prompt\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bexpose\s+(?:the\s+)?system\s+prompt\b",
        re.IGNORECASE,
    ),
)

JAILBREAK_PATTERNS = (
    re.compile(r"\bDAN\s+mode\b", re.IGNORECASE),
    re.compile(
        r"\bbypass\s+(?:your\s+)?(?:safety|security)\s+(?:rules|restrictions|filters)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdisable\s+(?:your\s+)?(?:safety|security)\s+(?:rules|filters)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bignore\s+(?:your\s+)?safety\s+(?:rules|policies|restrictions)\b",
        re.IGNORECASE,
    ),
)

GOOGLE_API_KEY_PATTERN = re.compile(
    r"\bAIza[0-9A-Za-z_-]{20,}\b"
)

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    r".*?"
    r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)

GENERIC_SECRET_PATTERN = re.compile(
    r"(?i)\b("
    r"api[_-]?key|"
    r"access[_-]?token|"
    r"auth[_-]?token|"
    r"client[_-]?secret|"
    r"secret[_-]?key|"
    r"password"
    r")\s*[:=]\s*([^\s,;]+)"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _blocked_result(
    *,
    operation: str,
    reason: str,
    violation: str,
) -> ArmorResult:
    return ArmorResult(
        allowed=False,
        sanitized_text="",
        reason=reason,
        provider="local",
        violations=(violation,),
        metadata={
            "operation": operation,
            "security_action": "block",
        },
    )


def _detect_prompt_injection(text: str) -> list[str]:
    violations: list[str] = []

    if any(
        pattern.search(text)
        for pattern in PROMPT_INJECTION_PATTERNS
    ):
        violations.append("prompt_injection")

    if any(
        pattern.search(text)
        for pattern in JAILBREAK_PATTERNS
    ):
        violations.append("jailbreak_indicator")

    return violations


def _redact_secrets(
    text: str,
) -> tuple[str, list[str]]:
    sanitized = text
    violations: list[str] = []

    # Google API key
    if GOOGLE_API_KEY_PATTERN.search(sanitized):
        sanitized = GOOGLE_API_KEY_PATTERN.sub(
            "[REDACTED]",
            sanitized,
        )
        violations.append(
            "sensitive_data:google_api_key"
        )

    # PEM private key
    if PRIVATE_KEY_PATTERN.search(sanitized):
        sanitized = PRIVATE_KEY_PATTERN.sub(
            "[REDACTED]",
            sanitized,
        )
        violations.append(
            "sensitive_data:private_key"
        )

    # Generic secrets
    if GENERIC_SECRET_PATTERN.search(sanitized):
        sanitized = GENERIC_SECRET_PATTERN.sub(
            lambda match: f"{match.group(1)}=[REDACTED]",
            sanitized,
        )
        violations.append(
            "sensitive_data:generic_secret"
        )

    return sanitized, violations


# ---------------------------------------------------------------------------
# Core sanitizer
# ---------------------------------------------------------------------------

def _sanitize(
    value: Any,
    *,
    operation: str,
) -> ArmorResult:

    # Invalid type
    if not isinstance(value, str):
        return _blocked_result(
            operation=operation,
            reason="Input must be a string.",
            violation="invalid_input_type",
        )

    # Empty input
    if not value.strip():
        return _blocked_result(
            operation=operation,
            reason="Input must not be empty.",
            violation="empty_input",
        )

    text = value.strip()

    # Prompt injection / jailbreak detection
    injection_violations = _detect_prompt_injection(text)

    if injection_violations:
        return ArmorResult(
            allowed=False,
            sanitized_text="",
            reason=(
                "Security policy blocked potentially malicious "
                "model-control content."
            ),
            provider="local",
            violations=tuple(injection_violations),
            metadata={
                "operation": operation,
                "security_action": "block",
            },
        )

    # Sensitive data redaction
    sanitized, sensitive_violations = _redact_secrets(text)

    if sensitive_violations:
        return ArmorResult(
            allowed=True,
            sanitized_text=sanitized,
            reason=(
                "Input passed security checks with "
                "sensitive values redacted."
            ),
            provider="local",
            violations=tuple(sensitive_violations),
            metadata={
                "operation": operation,
                "security_action": "redact",
            },
        )

    # Normal safe input
    return ArmorResult(
        allowed=True,
        sanitized_text=sanitized,
        reason="Input passed local security checks.",
        provider="local",
        violations=(),
        metadata={
            "operation": operation,
            "security_action": "allow",
        },
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_user_prompt(
    value: Any,
) -> ArmorResult:
    """
    Sanitize an incoming user prompt.
    """
    return _sanitize(
        value,
        operation="user_prompt",
    )


def sanitize_model_response(
    value: Any,
) -> ArmorResult:
    """
    Sanitize model-generated output.
    """
    return _sanitize(
        value,
        operation="model_response",
    )


def sanitize(
    value: Any,
    *,
    operation: str,
) -> ArmorResult:
    """
    Generic security sanitization API.
    """

    if operation == "user_prompt":
        return sanitize_user_prompt(value)

    if operation == "model_response":
        return sanitize_model_response(value)

    raise ValueError(
        "Unsupported security operation. "
        "Expected 'user_prompt' or 'model_response'."
    )


# ---------------------------------------------------------------------------
# Security status
# ---------------------------------------------------------------------------

def model_armor_status() -> dict[str, Any]:
    """
    Return non-sensitive Model Armor/security status.

    No API keys, tokens, credentials, or secret values are exposed.
    """

    return {
        "provider": "local",
        "available": True,
        "enabled": True,
        "configured": False,

        # Configuration indicators only.
        # These never expose the actual values.
        "project_configured": False,
        "location_configured": False,
        "template_configured": False,

        "mode": "local",
        "fallback": True,
        "service": "local-security-filter",

        "message": (
            "Local Model Armor-compatible security checks are active."
        ),
    }


__all__ = [
    "ArmorResult",
    "sanitize",
    "sanitize_user_prompt",
    "sanitize_model_response",
    "model_armor_status",
]
