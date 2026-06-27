"""Domain enumerations shared across entities, the API, and persistence."""

from __future__ import annotations

from enum import StrEnum


class RoleName(StrEnum):
    SUPER_ADMIN = "super_admin"
    SOC_MANAGER = "soc_manager"
    ANALYST = "analyst"
    READ_ONLY = "read_only"


class Permission(StrEnum):
    DASHBOARD_READ = "dashboard:read"
    ALERTS_READ = "alerts:read"
    ALERTS_WRITE = "alerts:write"
    INCIDENTS_READ = "incidents:read"
    INCIDENTS_WRITE = "incidents:write"
    HUNTS_RUN = "hunts:run"
    INVESTIGATIONS_RUN = "investigations:run"
    DETECTIONS_READ = "detections:read"
    DETECTIONS_WRITE = "detections:write"
    DATASOURCES_READ = "datasources:read"
    DATASOURCES_WRITE = "datasources:write"
    AUDIT_READ = "audit:read"
    USERS_MANAGE = "users:manage"
    ROLES_MANAGE = "roles:manage"
    SETTINGS_MANAGE = "settings:manage"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def weight(self) -> int:
        return {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1,
        }[self]


class AlertCategory(StrEnum):
    RANSOMWARE = "ransomware"
    CREDENTIAL_DUMPING = "credential_dumping"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PERSISTENCE = "persistence"
    LATERAL_MOVEMENT = "lateral_movement"
    LOTL = "lotl"
    EXFILTRATION = "exfiltration"
    C2 = "c2"
    INSIDER = "insider"
    CLOUD_ATTACK = "cloud_attack"
    OTHER = "other"


class AlertStatus(StrEnum):
    NEW = "new"
    TRIAGING = "triaging"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    SUPPRESSED = "suppressed"


class AlertSource(StrEnum):
    RULE = "rule"
    AI = "ai"
    HYBRID = "hybrid"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    CLOSED = "closed"


class DataSourceType(StrEnum):
    SYSMON = "sysmon"
    WINDOWS_EVENT = "windows_event"
    LINUX_AUDITD = "linux_auditd"
    CROWDSTRIKE = "crowdstrike"
    SENTINEL = "sentinel"
    SPLUNK = "splunk"
    ELASTIC = "elastic"
    ZEEK = "zeek"
    SURICATA = "suricata"
    EDR = "edr"
    FIREWALL = "firewall"
    DNS = "dns"
    PROXY = "proxy"
    CLOUDTRAIL = "cloudtrail"
    AZURE_ACTIVITY = "azure_activity"
    GCP_AUDIT = "gcp_audit"


class IOCType(StrEnum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    REGISTRY_KEY = "registry_key"
    PROCESS = "process"
    MUTEX = "mutex"


class Reputation(StrEnum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    BENIGN = "benign"
    UNKNOWN = "unknown"


class MitreTactic(StrEnum):
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "c2"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class AgentName(StrEnum):
    ORCHESTRATOR = "orchestrator"
    THREAT_INTEL = "threat_intel"
    IOC_CORRELATION = "ioc_correlation"
    LOG_INVESTIGATION = "log_investigation"
    MALWARE_ANALYSIS = "malware_analysis"
    MITRE_MAPPING = "mitre_mapping"
    RISK_SCORING = "risk_scoring"
    REPORTING = "reporting"
    DETECTION_ENGINEERING = "detection_engineering"


class DetectionFormat(StrEnum):
    SIGMA = "sigma"
    YARA = "yara"
    SURICATA = "suricata"
    SPLUNK_SPL = "splunk_spl"
    KQL = "kql"


class InvestigationType(StrEnum):
    CHAT = "chat"
    AUTONOMOUS_HUNT = "autonomous_hunt"
    ALERT_TRIAGE = "alert_triage"
