"""A curated, offline subset of the MITRE ATT&CK knowledge base.

Kept local and free — no network calls. Covers the techniques referenced by the
detection rules and agents. Extendable by appending entries.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import MitreTactic
from app.domain.value_objects.mitre import MitreTechnique


@dataclass(frozen=True, slots=True)
class TechniqueRecord:
    technique_id: str
    name: str
    tactic: MitreTactic
    description: str


MITRE_TECHNIQUES: dict[str, TechniqueRecord] = {
    "T1566.001": TechniqueRecord("T1566.001", "Spearphishing Attachment", MitreTactic.INITIAL_ACCESS, "Adversaries send malicious attachments to gain access."),
    "T1059.001": TechniqueRecord("T1059.001", "PowerShell", MitreTactic.EXECUTION, "Abuse of PowerShell for execution."),
    "T1059.003": TechniqueRecord("T1059.003", "Windows Command Shell", MitreTactic.EXECUTION, "Abuse of cmd.exe for execution."),
    "T1204.002": TechniqueRecord("T1204.002", "Malicious File", MitreTactic.EXECUTION, "User executes a malicious file."),
    "T1543.003": TechniqueRecord("T1543.003", "Windows Service", MitreTactic.PERSISTENCE, "Persistence via a new/modified Windows service."),
    "T1547.001": TechniqueRecord("T1547.001", "Registry Run Keys / Startup Folder", MitreTactic.PERSISTENCE, "Persistence via autostart registry keys."),
    "T1548.002": TechniqueRecord("T1548.002", "Bypass User Account Control", MitreTactic.PRIVILEGE_ESCALATION, "UAC bypass to elevate privileges."),
    "T1098": TechniqueRecord("T1098", "Account Manipulation", MitreTactic.PRIVILEGE_ESCALATION, "Manipulating accounts to maintain or elevate access."),
    "T1070.004": TechniqueRecord("T1070.004", "File Deletion", MitreTactic.DEFENSE_EVASION, "Deleting files to evade defenses."),
    "T1027": TechniqueRecord("T1027", "Obfuscated Files or Information", MitreTactic.DEFENSE_EVASION, "Obfuscation such as encoded commands."),
    "T1003.001": TechniqueRecord("T1003.001", "LSASS Memory", MitreTactic.CREDENTIAL_ACCESS, "Dumping credentials from LSASS memory."),
    "T1110": TechniqueRecord("T1110", "Brute Force", MitreTactic.CREDENTIAL_ACCESS, "Repeated authentication attempts to guess credentials."),
    "T1021.002": TechniqueRecord("T1021.002", "SMB/Windows Admin Shares", MitreTactic.LATERAL_MOVEMENT, "Lateral movement via admin shares."),
    "T1570": TechniqueRecord("T1570", "Lateral Tool Transfer", MitreTactic.LATERAL_MOVEMENT, "Transferring tools between systems."),
    "T1071.001": TechniqueRecord("T1071.001", "Web Protocols", MitreTactic.COMMAND_AND_CONTROL, "C2 over HTTP/S web protocols."),
    "T1573": TechniqueRecord("T1573", "Encrypted Channel", MitreTactic.COMMAND_AND_CONTROL, "Encrypted C2 channel."),
    "T1567.002": TechniqueRecord("T1567.002", "Exfiltration to Cloud Storage", MitreTactic.EXFILTRATION, "Exfiltrating data to cloud storage."),
    "T1486": TechniqueRecord("T1486", "Data Encrypted for Impact", MitreTactic.IMPACT, "Ransomware encryption of data."),
    "T1490": TechniqueRecord("T1490", "Inhibit System Recovery", MitreTactic.IMPACT, "Deleting backups/shadow copies."),
    "T1530": TechniqueRecord("T1530", "Data from Cloud Storage", MitreTactic.COLLECTION, "Accessing data from cloud storage."),
}


def get_technique(technique_id: str) -> TechniqueRecord | None:
    return MITRE_TECHNIQUES.get(technique_id)


def technique_value_object(technique_id: str) -> MitreTechnique | None:
    rec = MITRE_TECHNIQUES.get(technique_id)
    if rec is None:
        return None
    return MitreTechnique(technique_id=rec.technique_id, name=rec.name, tactic=rec.tactic)
