"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ShieldHalf, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    // Demo: skip real auth and enter the app. Real flow posts to /api/v1/auth/login.
    await new Promise((r) => setTimeout(r, 700));
    router.push("/dashboard");
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-4">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0 bg-grid-pattern bg-[size:48px_48px] opacity-30 [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />
      <div className="pointer-events-none absolute left-1/2 top-1/3 size-[500px] -translate-x-1/2 rounded-full bg-primary/20 blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-sm"
      >
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="relative flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-sky-500 shadow-xl shadow-primary/30">
            <ShieldHalf className="size-7 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight">ThreatMind AI</h1>
          <p className="text-sm text-muted-foreground">Enterprise SOC Platform</p>
        </div>

        <Card glass className="p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="email">Email</label>
              <Input id="email" type="email" placeholder="analyst@corp.com" defaultValue="priya@corp.com" required className="h-10" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium" htmlFor="password">Password</label>
              <Input id="password" type="password" placeholder="••••••••" defaultValue="demo-password" required className="h-10" />
            </div>
            <Button type="submit" className="h-10 w-full" disabled={loading}>
              {loading ? <Loader2 className="size-4 animate-spin" /> : null}
              Sign in
            </Button>
          </form>
          <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            Protected by MFA · SSO available
          </div>
        </Card>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          100% local & free · Powered by Ollama
        </p>
      </motion.div>
    </div>
  );
}
