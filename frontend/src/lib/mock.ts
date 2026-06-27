/** Deterministic mock data for a realistic SOC demo experience.
 *
 * Used as a fallback when the backend is unavailable so the premium UI is
 * always demonstrable. Values are hand-crafted to resemble genuine telemetry.
 */

import type {
  Alert,
  AlertCategory,
  DashboardOverview,
  Incident,
  Severity,
  TimelinePhase,
} from "./types";

const HOSTS = ["WIN-001", "WIN-014", "WIN-022", "DC-PRD-01", "LNX-APP-07", "K8S-NODE-3", "AWS-i-0a3f", "AZ-vm-prod-2"];
const USERS = ["svc_backup", "j.doe", "a.patel", "administrator", "root", "ec2-user", "m.chen", "SYSTEM"];

interface AlertTemplate {
  title: string;
  category: AlertCategory;
  severity: Severity;
  description: string;
  explanation: string;
  techniques: { technique_id: string; name: string; tactic: string }[];
}

const TEMPLATES: AlertTemplate[] = [
  {
    title: "Encoded PowerShell spawned from Office macro",
    category: "lotl",
    severity: "high",
    description: "winword.exe spawned powershell.exe with a Base64-encoded command.",
    explanation:
      "A Microsoft Word process launched PowerShell with an encoded command (-enc). This parent-child relationship is a classic macro-based initial-access pattern. The decoded payload attempts to download a second stage over HTTP.",
    techniques: [
      { technique_id: "T1059.001", name: "PowerShell", tactic: "execution" },
      { technique_id: "T1566.001", name: "Spearphishing Attachment", tactic: "initial_access" },
    ],
  },
  {
    title: "LSASS memory access by non-system process",
    category: "credential_dumping",
    severity: "critical",
    description: "Suspicious handle to lsass.exe requested by an unsigned binary.",
    explanation:
      "A non-system, unsigned process opened a handle to LSASS with PROCESS_VM_READ. This is consistent with credential-dumping tooling (e.g. Mimikatz) attempting to extract plaintext credentials and hashes from memory.",
    techniques: [{ technique_id: "T1003.001", name: "LSASS Memory", tactic: "credential_access" }],
  },
  {
    title: "Mass file rename with ransomware extension",
    category: "ransomware",
    severity: "critical",
    description: "Over 2,400 files renamed to *.lockbit within 90 seconds.",
    explanation:
      "A single process renamed thousands of files across multiple directories in under two minutes, appending a known ransomware extension. Volume-shadow-copy deletion was observed immediately prior, a hallmark of ransomware impact.",
    techniques: [
      { technique_id: "T1486", name: "Data Encrypted for Impact", tactic: "impact" },
      { technique_id: "T1490", name: "Inhibit System Recovery", tactic: "impact" },
    ],
  },
  {
    title: "New service installed for persistence",
    category: "persistence",
    severity: "medium",
    description: "A new Windows service pointing to a binary in %TEMP% was created.",
    explanation:
      "A service was registered with its ImagePath in a temporary directory and configured to auto-start. Legitimate software rarely installs services from %TEMP%; this is a common persistence mechanism.",
    techniques: [{ technique_id: "T1543.003", name: "Windows Service", tactic: "persistence" }],
  },
  {
    title: "Anomalous SMB lateral movement",
    category: "lateral_movement",
    severity: "high",
    description: "Admin share access to 12 hosts from a single workstation in 5 minutes.",
    explanation:
      "A workstation authenticated to administrative shares (ADMIN$, C$) across a dozen hosts in rapid succession using the same credential. This fan-out pattern indicates lateral movement following credential theft.",
    techniques: [
      { technique_id: "T1021.002", name: "SMB/Windows Admin Shares", tactic: "lateral_movement" },
      { technique_id: "T1570", name: "Lateral Tool Transfer", tactic: "lateral_movement" },
    ],
  },
  {
    title: "Beaconing to known C2 infrastructure",
    category: "c2",
    severity: "high",
    description: "Regular 60s-interval HTTPS connections to a low-reputation domain.",
    explanation:
      "An endpoint established highly periodic outbound connections (jitter < 5%) to a domain registered 3 days ago with no legitimate reputation. The regular beaconing cadence is characteristic of a command-and-control implant.",
    techniques: [
      { technique_id: "T1071.001", name: "Web Protocols", tactic: "c2" },
      { technique_id: "T1573", name: "Encrypted Channel", tactic: "c2" },
    ],
  },
  {
    title: "Large outbound transfer to cloud storage",
    category: "exfiltration",
    severity: "high",
    description: "8.2 GB uploaded to an unsanctioned cloud bucket after-hours.",
    explanation:
      "A host transferred several gigabytes to an external object-storage endpoint outside business hours, shortly after accessing a sensitive file share. The timing and volume suggest data exfiltration.",
    techniques: [{ technique_id: "T1567.002", name: "Exfiltration to Cloud Storage", tactic: "exfiltration" }],
  },
  {
    title: "IAM privilege escalation via policy attachment",
    category: "cloud_attack",
    severity: "critical",
    description: "AttachUserPolicy granted AdministratorAccess to a low-privilege user.",
    explanation:
      "A CloudTrail event shows a user attaching the AdministratorAccess managed policy to their own IAM identity, escalating from limited permissions to full account control. The acting key had no prior history of IAM actions.",
    techniques: [{ technique_id: "T1098", name: "Account Manipulation", tactic: "privilege_escalation" }],
  },
  {
    title: "Off-hours access to sensitive HR records by departing employee",
    category: "insider",
    severity: "medium",
    description: "Bulk download of personnel files by a user under offboarding.",
    explanation:
      "An employee flagged for offboarding accessed and downloaded an unusually large set of HR records at 02:14 local time. The behavior deviates sharply from the user's 90-day baseline.",
    techniques: [{ technique_id: "T1530", name: "Data from Cloud Storage", tactic: "collection" }],
  },
  {
    title: "UAC bypass via fodhelper registry hijack",
    category: "privilege_escalation",
    severity: "high",
    description: "Registry modification under HKCU consistent with fodhelper bypass.",
    explanation:
      "A process modified HKCU\\Software\\Classes\\ms-settings to hijack the auto-elevating fodhelper.exe, a well-documented technique to bypass User Account Control and execute code at high integrity.",
    techniques: [{ technique_id: "T1548.002", name: "Bypass UAC", tactic: "privilege_escalation" }],
  },
];

// Simple seeded PRNG for deterministic output.
function makeRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

function pad(n: number): string {
  return n.toString(16).padStart(4, "0");
}

export function mockAlerts(count = 48): Alert[] {
  const rng = makeRng(1337);
  const statuses: Alert["status"][] = ["new", "triaging", "investigating", "resolved", "false_positive"];
  const sources: Alert["source"][] = ["rule", "ai", "hybrid"];
  const now = Date.UTC(2026, 5, 27, 14, 0, 0);

  return Array.from({ length: count }, (_, i) => {
    const t = TEMPLATES[Math.floor(rng() * TEMPLATES.length)];
    const minutesAgo = Math.floor(rng() * 60 * 72);
    const ts = new Date(now - minutesAgo * 60_000).toISOString();
    const confidence = 55 + Math.floor(rng() * 45);
    return {
      id: `al-${pad(i)}-${pad(Math.floor(rng() * 65535))}`,
      title: t.title,
      description: t.description,
      category: t.category,
      severity: t.severity,
      confidence,
      confidence_label:
        confidence >= 85 ? "very_high" : confidence >= 65 ? "high" : "medium",
      status: statuses[Math.floor(rng() * statuses.length)],
      source: sources[Math.floor(rng() * sources.length)],
      host: HOSTS[Math.floor(rng() * HOSTS.length)],
      user_principal: USERS[Math.floor(rng() * USERS.length)],
      explanation: t.explanation,
      evidence: [
        { summary: t.description, event_id: `evt-${pad(i)}`, source: "sysmon" },
        { summary: "Correlated network connection to suspicious endpoint", event_id: `evt-${pad(i + 1)}`, source: "zeek" },
      ],
      techniques: t.techniques.map((te) => ({
        ...te,
        url: `https://attack.mitre.org/techniques/${te.technique_id.replace(".", "/")}/`,
      })),
      first_seen: ts,
      last_seen: ts,
    };
  });
}

export function mockOverview(): DashboardOverview {
  const alerts = mockAlerts();
  const byStatus: Record<string, number> = {};
  const bySeverity: Record<string, number> = {};
  for (const a of alerts) {
    byStatus[a.status] = (byStatus[a.status] ?? 0) + 1;
    bySeverity[a.severity] = (bySeverity[a.severity] ?? 0) + 1;
  }
  return {
    alerts_by_status: byStatus,
    alerts_by_severity: bySeverity,
    open_alerts: (byStatus.new ?? 0) + (byStatus.triaging ?? 0) + (byStatus.investigating ?? 0),
  };
}

export function mockIncidents(): Incident[] {
  return [
    {
      id: "inc-2026-0042",
      title: "LockBit-style ransomware on finance segment",
      summary:
        "Multi-stage intrusion beginning with a malicious macro, escalating through credential theft and lateral movement, culminating in ransomware deployment across 14 hosts in the finance VLAN.",
      severity: "critical",
      status: "investigating",
      risk_score: 94,
      alert_count: 11,
      opened_at: "2026-06-27T09:12:00Z",
    },
    {
      id: "inc-2026-0041",
      title: "Cloud IAM privilege escalation in prod account",
      summary:
        "A compromised access key was used to attach administrative IAM policies and create persistence backdoors in the production AWS account.",
      severity: "critical",
      status: "contained",
      risk_score: 88,
      alert_count: 6,
      opened_at: "2026-06-26T18:40:00Z",
    },
    {
      id: "inc-2026-0039",
      title: "Suspected C2 beaconing from developer workstation",
      summary:
        "Periodic encrypted beaconing to newly-registered infrastructure detected on a developer endpoint; investigation ongoing to determine implant family.",
      severity: "high",
      status: "open",
      risk_score: 71,
      alert_count: 4,
      opened_at: "2026-06-27T11:05:00Z",
    },
    {
      id: "inc-2026-0037",
      title: "Insider data staging prior to departure",
      summary:
        "A departing employee accessed and staged sensitive HR and customer records; DLP and UEBA signals correlated into a single insider-threat case.",
      severity: "medium",
      status: "open",
      risk_score: 58,
      alert_count: 3,
      opened_at: "2026-06-25T02:30:00Z",
    },
  ];
}

export function mockTimeline(): TimelinePhase[] {
  return [
    { phase: "initial_access", title: "Phishing attachment opened", description: "User opened invoice.docm; macro executed.", occurred_at: "2026-06-27T09:01:00Z", technique_id: "T1566.001" },
    { phase: "execution", title: "Encoded PowerShell launched", description: "winword.exe → powershell.exe -enc …", occurred_at: "2026-06-27T09:01:20Z", technique_id: "T1059.001" },
    { phase: "persistence", title: "Service installed", description: "Auto-start service from %TEMP%.", occurred_at: "2026-06-27T09:03:10Z", technique_id: "T1543.003" },
    { phase: "privilege_escalation", title: "UAC bypass", description: "fodhelper registry hijack to high integrity.", occurred_at: "2026-06-27T09:04:05Z", technique_id: "T1548.002" },
    { phase: "credential_access", title: "LSASS dumped", description: "Credentials extracted from memory.", occurred_at: "2026-06-27T09:06:42Z", technique_id: "T1003.001" },
    { phase: "lateral_movement", title: "SMB fan-out", description: "Admin-share access to 12 hosts.", occurred_at: "2026-06-27T09:11:00Z", technique_id: "T1021.002" },
    { phase: "collection", title: "Sensitive shares enumerated", description: "Finance file shares crawled.", occurred_at: "2026-06-27T09:18:00Z", technique_id: "T1039" },
    { phase: "impact", title: "Ransomware deployed", description: "Mass encryption + shadow-copy deletion.", occurred_at: "2026-06-27T09:24:30Z", technique_id: "T1486" },
  ];
}

/** Trend series for the dashboard (last 14 days). */
export function mockTrends(): { date: string; alerts: number; incidents: number; resolved: number }[] {
  const rng = makeRng(99);
  return Array.from({ length: 14 }, (_, i) => {
    const d = new Date(Date.UTC(2026, 5, 14 + i));
    const alerts = 30 + Math.floor(rng() * 70);
    return {
      date: d.toISOString().slice(5, 10),
      alerts,
      incidents: Math.floor(alerts / 12),
      resolved: Math.floor(alerts * (0.5 + rng() * 0.4)),
    };
  });
}

/** Threat heatmap: host × category intensity. */
export function mockHeatmap(): { host: string; category: AlertCategory; value: number }[] {
  const rng = makeRng(7);
  const cats: AlertCategory[] = ["ransomware", "credential_dumping", "lateral_movement", "c2", "exfiltration", "persistence"];
  const out: { host: string; category: AlertCategory; value: number }[] = [];
  for (const host of HOSTS.slice(0, 8)) {
    for (const category of cats) {
      out.push({ host, category, value: Math.floor(rng() * 10) });
    }
  }
  return out;
}
