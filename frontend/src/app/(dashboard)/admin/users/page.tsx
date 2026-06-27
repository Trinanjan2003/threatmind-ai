"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { UserPlus, Shield } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const USERS = [
  { name: "Ada Admin", email: "admin@corp.com", role: "Super Admin", mfa: true, active: true },
  { name: "Marcus Manager", email: "marcus@corp.com", role: "SOC Manager", mfa: true, active: true },
  { name: "Priya Analyst", email: "priya@corp.com", role: "Security Analyst", mfa: true, active: true },
  { name: "Sam Chen", email: "sam@corp.com", role: "Security Analyst", mfa: false, active: true },
  { name: "Riley Auditor", email: "riley@corp.com", role: "Read Only", mfa: true, active: true },
  { name: "Jordan Park", email: "jordan@corp.com", role: "Read Only", mfa: false, active: false },
];

const ROLE_VARIANT: Record<string, "default" | "secondary" | "warning" | "destructive"> = {
  "Super Admin": "destructive",
  "SOC Manager": "warning",
  "Security Analyst": "default",
  "Read Only": "secondary",
};

export default function UsersPage() {
  return (
    <div className="space-y-5">
      <PageHeader
        title="Users & Roles"
        description="Role-based access control across the platform"
        actions={<Button size="sm"><UserPlus className="size-4" /> Invite User</Button>}
      />

      <Card glass className="overflow-hidden">
        <div className="hidden grid-cols-[1fr_180px_120px_100px] gap-3 border-b border-border/60 bg-muted/30 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground md:grid">
          <span>User</span><span>Role</span><span>MFA</span><span>Status</span>
        </div>
        <div className="divide-y divide-border/50">
          {USERS.map((u, i) => (
            <motion.div
              key={u.email}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.04 }}
              className="grid grid-cols-1 items-center gap-3 px-4 py-3 md:grid-cols-[1fr_180px_120px_100px]"
            >
              <div className="flex items-center gap-3">
                <Avatar><AvatarFallback>{u.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback></Avatar>
                <div>
                  <p className="text-sm font-medium">{u.name}</p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                </div>
              </div>
              <div><Badge variant={ROLE_VARIANT[u.role]} className="gap-1"><Shield className="size-3" /> {u.role}</Badge></div>
              <div className="text-sm">{u.mfa ? <span className="text-emerald-500">Enabled</span> : <span className="text-muted-foreground">Disabled</span>}</div>
              <div><Badge variant={u.active ? "success" : "secondary"}>{u.active ? "Active" : "Inactive"}</Badge></div>
            </motion.div>
          ))}
        </div>
      </Card>
    </div>
  );
}
