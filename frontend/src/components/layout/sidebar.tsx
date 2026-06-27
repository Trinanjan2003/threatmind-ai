"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { ShieldHalf } from "lucide-react";
import { NAV_GROUPS, NAV_ITEMS } from "@/lib/nav";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border/60 bg-card/30 backdrop-blur-xl lg:flex">
      <div className="flex h-16 items-center gap-2.5 border-b border-border/60 px-5">
        <div className="relative flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-sky-500 shadow-lg shadow-primary/30">
          <ShieldHalf className="size-5 text-white" />
          <span className="absolute -right-0.5 -top-0.5 size-2.5 animate-pulse-glow rounded-full bg-emerald-400 ring-2 ring-card" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-tight">ThreatMind</p>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground">AI SOC Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {NAV_GROUPS.map((group) => (
          <div key={group}>
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
              {group}
            </p>
            <ul className="space-y-0.5">
              {NAV_ITEMS.filter((i) => i.group === group).map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        active
                          ? "text-foreground"
                          : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                      )}
                    >
                      {active && (
                        <motion.span
                          layoutId="sidebar-active"
                          className="absolute inset-0 rounded-lg bg-primary/10 ring-1 ring-primary/20"
                          transition={{ type: "spring", stiffness: 400, damping: 32 }}
                        />
                      )}
                      <Icon className={cn("relative size-4 shrink-0", active && "text-primary")} />
                      <span className="relative">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-border/60 p-4">
        <div className="rounded-lg bg-gradient-to-br from-primary/10 to-transparent p-3 ring-1 ring-primary/15">
          <p className="text-xs font-medium">Local & Free</p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            Powered by Ollama. No data leaves your environment.
          </p>
        </div>
      </div>
    </aside>
  );
}
