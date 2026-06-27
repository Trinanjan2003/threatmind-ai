/** Condensed MITRE ATT&CK matrix data for visualization (Enterprise subset). */

export interface MitreTechniqueCell {
  id: string;
  name: string;
  coverage: number; // 0-100 detection coverage
  alerts: number;
}

export interface MitreTacticColumn {
  tactic: string;
  label: string;
  techniques: MitreTechniqueCell[];
}

export const MITRE_MATRIX: MitreTacticColumn[] = [
  {
    tactic: "initial_access",
    label: "Initial Access",
    techniques: [
      { id: "T1566", name: "Phishing", coverage: 88, alerts: 14 },
      { id: "T1190", name: "Exploit Public-Facing App", coverage: 72, alerts: 3 },
      { id: "T1078", name: "Valid Accounts", coverage: 64, alerts: 7 },
    ],
  },
  {
    tactic: "execution",
    label: "Execution",
    techniques: [
      { id: "T1059", name: "Command & Scripting", coverage: 94, alerts: 22 },
      { id: "T1053", name: "Scheduled Task/Job", coverage: 70, alerts: 4 },
      { id: "T1204", name: "User Execution", coverage: 60, alerts: 9 },
    ],
  },
  {
    tactic: "persistence",
    label: "Persistence",
    techniques: [
      { id: "T1543", name: "Create System Process", coverage: 82, alerts: 6 },
      { id: "T1547", name: "Boot/Logon Autostart", coverage: 75, alerts: 5 },
      { id: "T1136", name: "Create Account", coverage: 55, alerts: 2 },
    ],
  },
  {
    tactic: "privilege_escalation",
    label: "Priv. Escalation",
    techniques: [
      { id: "T1548", name: "Abuse Elevation Control", coverage: 80, alerts: 8 },
      { id: "T1068", name: "Exploit for Priv Esc", coverage: 48, alerts: 1 },
      { id: "T1098", name: "Account Manipulation", coverage: 66, alerts: 4 },
    ],
  },
  {
    tactic: "defense_evasion",
    label: "Defense Evasion",
    techniques: [
      { id: "T1070", name: "Indicator Removal", coverage: 71, alerts: 5 },
      { id: "T1027", name: "Obfuscated Files", coverage: 68, alerts: 11 },
      { id: "T1562", name: "Impair Defenses", coverage: 59, alerts: 3 },
    ],
  },
  {
    tactic: "credential_access",
    label: "Credential Access",
    techniques: [
      { id: "T1003", name: "OS Credential Dumping", coverage: 90, alerts: 7 },
      { id: "T1110", name: "Brute Force", coverage: 85, alerts: 18 },
      { id: "T1555", name: "Credentials from Stores", coverage: 52, alerts: 2 },
    ],
  },
  {
    tactic: "lateral_movement",
    label: "Lateral Movement",
    techniques: [
      { id: "T1021", name: "Remote Services", coverage: 86, alerts: 9 },
      { id: "T1570", name: "Lateral Tool Transfer", coverage: 64, alerts: 3 },
    ],
  },
  {
    tactic: "exfiltration",
    label: "Exfiltration",
    techniques: [
      { id: "T1567", name: "Exfil over Web Service", coverage: 78, alerts: 4 },
      { id: "T1048", name: "Exfil over Alt Protocol", coverage: 56, alerts: 2 },
    ],
  },
  {
    tactic: "impact",
    label: "Impact",
    techniques: [
      { id: "T1486", name: "Data Encrypted for Impact", coverage: 92, alerts: 6 },
      { id: "T1490", name: "Inhibit System Recovery", coverage: 74, alerts: 3 },
    ],
  },
];
