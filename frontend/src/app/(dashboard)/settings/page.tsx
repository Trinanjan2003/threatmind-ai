"use client";

import * as React from "react";
import { PageHeader } from "@/components/features/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function SettingsPage() {
  return (
    <div className="space-y-5">
      <PageHeader title="Settings" description="Platform configuration" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card glass>
          <CardHeader>
            <CardTitle className="text-base">AI / LLM</CardTitle>
            <CardDescription>Local inference via Ollama — no data leaves your environment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Provider</span>
              <Badge variant="default">Ollama (local)</Badge>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">Base URL</span>
              <Input defaultValue="http://localhost:11434" className="max-w-[220px]" />
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">Model</span>
              <Input defaultValue="llama3.1" className="max-w-[220px]" />
            </div>
            <Button size="sm" variant="outline">Test Connection</Button>
          </CardContent>
        </Card>

        <Card glass>
          <CardHeader>
            <CardTitle className="text-base">Appearance</CardTitle>
            <CardDescription>Theme and display preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Theme</span>
              <ThemeToggle />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Density</span>
              <Badge variant="secondary">Comfortable</Badge>
            </div>
          </CardContent>
        </Card>

        <Card glass>
          <CardHeader>
            <CardTitle className="text-base">Security</CardTitle>
            <CardDescription>Authentication and session policy</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between"><span className="text-muted-foreground">MFA enforcement</span><Badge variant="success">Required for admins</Badge></div>
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Access token TTL</span><span>30 min</span></div>
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Rate limit</span><span>100 req / min</span></div>
          </CardContent>
        </Card>

        <Card glass>
          <CardHeader>
            <CardTitle className="text-base">Retention</CardTitle>
            <CardDescription>Event and audit data retention</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Event retention</span><span>90 days</span></div>
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Audit retention</span><span>1 year</span></div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
