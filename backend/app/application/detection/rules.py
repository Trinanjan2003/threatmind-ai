"""Deterministic detection rules over normalized events.

Each rule is a pure predicate plus metadata (category, severity, MITRE mapping).
Rules are intentionally simple and explainable; the AI agents (Phase 3) add
behavioral and correlation-based detections on top. Keeping rules as data makes
them trivial to unit-test and extend.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.domain.enums import AlertCategory, Severity
from app.domain.events.normalized_event import NormalizedEvent


@dataclass(slots=True)
class DetectionRule:
    rule_id: str
    title: str
    description: str
    category: AlertCategory
    severity: Severity
    base_confidence: int
    technique_ids: list[str]
    predicate: Callable[[NormalizedEvent], bool]
    explanation: str = ""
    tags: list[str] = field(default_factory=list)

    def matches(self, event: NormalizedEvent) -> bool:
        try:
            return self.predicate(event)
        except Exception:  # noqa: BLE001 - a faulty rule must not break ingestion
            return False


# ── Predicate helpers ──
def _cmdline(e: NormalizedEvent) -> str:
    return (e.process.command_line or "").lower() if e.process else ""


def _parent(e: NormalizedEvent) -> str:
    return (e.process.parent_name or "").lower() if e.process else ""


def _image(e: NormalizedEvent) -> str:
    return (e.process.name or "").lower() if e.process else ""


def _filename(e: NormalizedEvent) -> str:
    return (e.file.name or "").lower() if e.file else ""


def _cloud_event(e: NormalizedEvent) -> str:
    return (e.cloud.event_name or "") if e.cloud else ""


_OFFICE_PARENTS = ("winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe")
_LOLBINS = ("powershell.exe", "cmd.exe", "wscript.exe", "cscript.exe", "mshta.exe", "rundll32.exe", "regsvr32.exe")


DEFAULT_RULES: list[DetectionRule] = [
    DetectionRule(
        rule_id="TM-0001",
        title="Encoded PowerShell execution",
        description="PowerShell invoked with an encoded command.",
        category=AlertCategory.LOTL,
        severity=Severity.HIGH,
        base_confidence=78,
        technique_ids=["T1059.001", "T1027"],
        explanation="Encoded PowerShell (-enc/-EncodedCommand) is commonly used to obfuscate malicious payloads.",
        predicate=lambda e: "powershell" in _image(e)
        and any(t in _cmdline(e) for t in ("-enc", "-encodedcommand", "frombase64string")),
    ),
    DetectionRule(
        rule_id="TM-0002",
        title="Office application spawned a script interpreter",
        description="A Microsoft Office process spawned a scripting/LOLBin process.",
        category=AlertCategory.LOTL,
        severity=Severity.HIGH,
        base_confidence=82,
        technique_ids=["T1566.001", "T1059.001"],
        explanation="Office spawning a script interpreter is a hallmark of macro-based initial access.",
        predicate=lambda e: any(p in _parent(e) for p in _OFFICE_PARENTS)
        and any(b in _image(e) for b in _LOLBINS),
    ),
    DetectionRule(
        rule_id="TM-0003",
        title="LSASS access by suspicious process",
        description="A non-system process accessed LSASS, consistent with credential dumping.",
        category=AlertCategory.CREDENTIAL_DUMPING,
        severity=Severity.CRITICAL,
        base_confidence=88,
        technique_ids=["T1003.001"],
        explanation="Reading LSASS memory is a primary technique for extracting credentials (e.g. Mimikatz).",
        predicate=lambda e: "lsass" in _cmdline(e) or "lsass.exe" in (e.message or "").lower(),
    ),
    DetectionRule(
        rule_id="TM-0004",
        title="Service installed from temporary directory",
        description="A new service was created pointing to a binary in a temp path.",
        category=AlertCategory.PERSISTENCE,
        severity=Severity.MEDIUM,
        base_confidence=68,
        technique_ids=["T1543.003"],
        explanation="Services launching from %TEMP% are a common persistence mechanism.",
        predicate=lambda e: e.action in ("process_create", "sysmon_1")
        and ("\\temp\\" in _image(e) or "/tmp/" in _image(e))
        and "service" in _cmdline(e),
    ),
    DetectionRule(
        rule_id="TM-0005",
        title="UAC bypass via fodhelper registry hijack",
        description="Registry modification under ms-settings consistent with fodhelper UAC bypass.",
        category=AlertCategory.PRIVILEGE_ESCALATION,
        severity=Severity.HIGH,
        base_confidence=80,
        technique_ids=["T1548.002"],
        explanation="Hijacking the ms-settings handler abuses auto-elevating fodhelper.exe to bypass UAC.",
        predicate=lambda e: e.action in ("registry_set", "registry_create")
        and "ms-settings" in (e.message or "").lower() + _cmdline(e),
    ),
    DetectionRule(
        rule_id="TM-0006",
        title="Mass file modification (possible ransomware)",
        description="High-volume file changes with a known ransomware extension.",
        category=AlertCategory.RANSOMWARE,
        severity=Severity.CRITICAL,
        base_confidence=85,
        technique_ids=["T1486"],
        explanation="Rapid mass file renames/encryption with ransomware extensions indicate impact-stage ransomware.",
        predicate=lambda e: any(
            ext in _filename(e) for ext in (".lockbit", ".encrypted", ".crypt", ".locked")
        ),
    ),
    DetectionRule(
        rule_id="TM-0007",
        title="IAM privilege escalation via policy attachment",
        description="A CloudTrail AttachUserPolicy/AttachRolePolicy granting broad permissions.",
        category=AlertCategory.CLOUD_ATTACK,
        severity=Severity.CRITICAL,
        base_confidence=84,
        technique_ids=["T1098"],
        explanation="Attaching administrative IAM policies can escalate a low-privilege identity to full control.",
        predicate=lambda e: _cloud_event(e) in ("AttachUserPolicy", "AttachRolePolicy", "PutUserPolicy"),
    ),
    DetectionRule(
        rule_id="TM-0008",
        title="Failed console/API authentication burst",
        description="Repeated authentication failures indicative of brute force.",
        category=AlertCategory.CREDENTIAL_DUMPING,
        severity=Severity.MEDIUM,
        base_confidence=60,
        technique_ids=["T1110"],
        explanation="A burst of failed logins suggests credential brute forcing or password spraying.",
        predicate=lambda e: "api_error" in e.tags
        and _cloud_event(e).lower().startswith("consolelogin"),
    ),
]
