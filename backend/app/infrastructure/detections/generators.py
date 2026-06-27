"""Generate detection content in multiple formats from a MITRE technique.

These are deterministic, template-based generators (no paid services). They
produce syntactically valid starting rules that an analyst can refine, mapped to
the technique's known behavior. The AI layer can enrich the description, but the
structure is guaranteed even without an LLM.
"""

from __future__ import annotations

from app.domain.enums import DetectionFormat
from app.infrastructure.mitre.knowledge_base import get_technique

# Per-technique detection hints used to fill templates.
_TECHNIQUE_HINTS: dict[str, dict[str, str]] = {
    "T1059.001": {
        "selection": "powershell.exe with -enc / -EncodedCommand",
        "image": "\\\\powershell.exe",
        "cmd_contains": "-enc",
    },
    "T1003.001": {
        "selection": "process accessing lsass.exe memory",
        "image": "\\\\lsass.exe",
        "cmd_contains": "lsass",
    },
    "T1543.003": {
        "selection": "service created from a temporary path",
        "image": "\\\\Temp\\\\",
        "cmd_contains": "create service",
    },
    "T1486": {
        "selection": "mass file modification with ransomware extension",
        "image": "*",
        "cmd_contains": ".lockbit",
    },
}


def _hint(technique_id: str) -> dict[str, str]:
    return _TECHNIQUE_HINTS.get(
        technique_id,
        {"selection": "suspicious behavior", "image": "\\\\suspicious.exe", "cmd_contains": "suspicious"},
    )


def _sigma(technique_id: str, name: str, context: str) -> str:
    h = _hint(technique_id)
    return f"""title: {name} ({technique_id})
id: auto-{technique_id.lower().replace('.', '-')}
status: experimental
description: Detects {h['selection']}. Context: {context}
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|endswith: '{h['image']}'
    CommandLine|contains: '{h['cmd_contains']}'
  condition: selection
level: high
tags:
  - attack.{technique_id.lower()}"""


def _yara(technique_id: str, name: str, context: str) -> str:
    h = _hint(technique_id)
    rule_name = f"TM_{technique_id.replace('.', '_')}"
    return f"""rule {rule_name} {{
  meta:
    author = "ThreatMind AI"
    description = "{name} - {h['selection']}"
    mitre = "{technique_id}"
    context = "{context}"
  strings:
    $a = "{h['cmd_contains']}" ascii wide nocase
  condition:
    $a
}}"""


def _suricata(technique_id: str, name: str, context: str) -> str:
    return f"""alert tcp $HOME_NET any -> $EXTERNAL_NET any (
  msg:"ThreatMind {name} ({technique_id})";
  flow:established,to_server;
  threshold: type both, track by_src, count 5, seconds 300;
  classtype:trojan-activity;
  sid:91{abs(hash(technique_id)) % 100000:05d}; rev:1;
)"""


def _splunk(technique_id: str, name: str, context: str) -> str:
    h = _hint(technique_id)
    return f"""index=sysmon EventCode=1
  Image="*{h['image'].replace(chr(92) + chr(92), chr(92))}*"
  CommandLine="*{h['cmd_contains']}*"
| stats count by host, User, Image, CommandLine
| where count > 0
| sort - count
``` {name} ({technique_id}) ```"""


def _kql(technique_id: str, name: str, context: str) -> str:
    h = _hint(technique_id)
    return f"""// {name} ({technique_id})
DeviceProcessEvents
| where FileName =~ "{h['image'].split(chr(92))[-1] or 'suspicious.exe'}"
| where ProcessCommandLine has "{h['cmd_contains']}"
| project Timestamp, DeviceName, AccountName, FileName, ProcessCommandLine
| order by Timestamp desc"""


_GENERATORS = {
    DetectionFormat.SIGMA: _sigma,
    DetectionFormat.YARA: _yara,
    DetectionFormat.SURICATA: _suricata,
    DetectionFormat.SPLUNK_SPL: _splunk,
    DetectionFormat.KQL: _kql,
}


def generate_detection(*, fmt: str, technique_id: str, context: str = "") -> str:
    """Generate a detection rule/query for a technique in the requested format."""
    fmt_enum = DetectionFormat(fmt)
    rec = get_technique(technique_id)
    name = rec.name if rec else technique_id
    return _GENERATORS[fmt_enum](technique_id, name, context or "auto-generated")
