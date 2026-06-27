import {
  LayoutDashboard,
  ShieldAlert,
  Siren,
  Crosshair,
  Grid3x3,
  GitBranch,
  Code2,
  MessageSquareText,
  Database,
  Users,
  ScrollText,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
  group: "Operations" | "Hunting" | "Engineering" | "Administration";
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, group: "Operations" },
  { label: "Alerts", href: "/alerts", icon: ShieldAlert, group: "Operations" },
  { label: "Incidents", href: "/incidents", icon: Siren, group: "Operations" },
  { label: "Threat Hunting", href: "/hunting", icon: Crosshair, group: "Hunting" },
  { label: "AI Investigation", href: "/chat", icon: MessageSquareText, group: "Hunting" },
  { label: "MITRE Matrix", href: "/mitre", icon: Grid3x3, group: "Hunting" },
  { label: "Attack Timeline", href: "/timeline", icon: GitBranch, group: "Hunting" },
  { label: "Detection Studio", href: "/detections", icon: Code2, group: "Engineering" },
  { label: "Data Sources", href: "/data-sources", icon: Database, group: "Engineering" },
  { label: "Users & Roles", href: "/admin/users", icon: Users, group: "Administration" },
  { label: "Audit Log", href: "/admin/audit", icon: ScrollText, group: "Administration" },
  { label: "Settings", href: "/settings", icon: Settings, group: "Administration" },
];

export const NAV_GROUPS = ["Operations", "Hunting", "Engineering", "Administration"] as const;
