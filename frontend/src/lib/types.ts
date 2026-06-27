/** Shared domain types mirrored from the backend API. */

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type AlertStatus =
  | "new"
  | "triaging"
  | "investigating"
  | "resolved"
  | "false_positive"
  | "suppressed";

export type AlertCategory =
  | "ransomware"
  | "credential_dumping"
  | "privilege_escalation"
  | "persistence"
  | "lateral_movement"
  | "lotl"
  | "exfiltration"
  | "c2"
  | "insider"
  | "cloud_attack"
  | "other";

export interface Evidence {
  summary: string;
  event_id?: string | null;
  source?: string | null;
  fields?: Record<string, unknown>;
}

export interface Technique {
  technique_id: string;
  name: string;
  tactic: string;
  url: string;
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  category: AlertCategory;
  severity: Severity;
  confidence: number;
  confidence_label: string;
  status: AlertStatus;
  source: "rule" | "ai" | "hybrid";
  host?: string | null;
  user_principal?: string | null;
  explanation?: string | null;
  evidence: Evidence[];
  techniques: Technique[];
  assigned_to?: string | null;
  first_seen?: string | null;
  last_seen?: string | null;
}

export interface Incident {
  id: string;
  title: string;
  summary: string;
  severity: Severity;
  status: "open" | "investigating" | "contained" | "closed";
  risk_score: number;
  alert_count: number;
  opened_at: string;
  closed_at?: string | null;
}

export interface TimelinePhase {
  phase: string;
  title: string;
  description: string;
  occurred_at: string;
  technique_id?: string;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface DashboardOverview {
  alerts_by_status: Record<string, number>;
  alerts_by_severity: Record<string, number>;
  open_alerts: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  evidence?: Evidence[];
  agentSteps?: { agent: string; status: string }[];
  streaming?: boolean;
}
