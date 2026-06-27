"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, User, FileSearch, ShieldQuestion } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";

const SUGGESTIONS = [
  "Why was this alert generated?",
  "Investigate host WIN-001",
  "Find ransomware behavior",
  "Show suspicious PowerShell activity",
  "Explain possible credential theft",
];

const AGENT_SEQUENCE = [
  "log_investigation",
  "ioc_correlation",
  "threat_intel",
  "mitre_mapping",
  "risk_scoring",
  "reporting",
];

// Simulated analyst-quality answer (used when backend/Ollama is unavailable).
const CANNED_ANSWER = `Based on correlated telemetry from **WIN-001**, I've identified a high-confidence intrusion chain:

**1. Initial Access (T1566.001)** — A macro-enabled document (invoice.docm) was opened at 09:01 UTC, spawning an encoded PowerShell process from winword.exe.

**2. Credential Access (T1003.001)** — At 09:06, an unsigned binary opened a read handle to LSASS memory, consistent with credential dumping.

**3. Lateral Movement (T1021.002)** — The stolen credential was then used to access administrative shares across 12 hosts within 5 minutes.

**Assessment:** This is a coordinated, multi-stage attack with a **94/100 risk score**. I recommend immediate host isolation and a fleet-wide hunt for the same parent-child process lineage.`;

export default function ChatPage() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setBusy(true);
    setInput("");

    const userMsg: ChatMessage = { id: `u-${messages.length}`, role: "user", content: text };
    const assistantMsg: ChatMessage = {
      id: `a-${messages.length}`,
      role: "assistant",
      content: "",
      streaming: true,
      agentSteps: [],
    };
    setMessages((m) => [...m, userMsg, assistantMsg]);

    // Simulate the multi-agent orchestration steps.
    for (let i = 0; i < AGENT_SEQUENCE.length; i++) {
      await new Promise((r) => setTimeout(r, 320));
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantMsg.id
            ? { ...msg, agentSteps: AGENT_SEQUENCE.slice(0, i + 1).map((a) => ({ agent: a, status: "completed" })) }
            : msg
        )
      );
    }

    // Stream the answer token-by-token.
    const tokens = CANNED_ANSWER.split(" ");
    for (let i = 0; i < tokens.length; i++) {
      await new Promise((r) => setTimeout(r, 18));
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantMsg.id
            ? { ...msg, content: tokens.slice(0, i + 1).join(" ") }
            : msg
        )
      );
    }

    setMessages((m) => m.map((msg) => (msg.id === assistantMsg.id ? { ...msg, streaming: false } : msg)));
    setBusy(false);
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      <PageHeader
        title="AI Investigation Workspace"
        description="Ask natural-language questions; answers are backed by cited evidence."
        actions={<Badge variant="default" className="gap-1"><Sparkles className="size-3" /> Ollama · local</Badge>}
      />

      <Card glass className="flex flex-1 flex-col overflow-hidden">
        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-sky-500 shadow-lg shadow-primary/30">
                <ShieldQuestion className="size-7 text-white" />
              </div>
              <h3 className="mt-4 text-lg font-semibold">How can I help you investigate?</h3>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                I orchestrate 8 specialized agents to correlate logs, enrich IOCs, map MITRE techniques, and explain findings.
              </p>
              <div className="mt-5 flex max-w-lg flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="rounded-full border border-border bg-muted/40 px-3 py-1.5 text-xs transition-colors hover:border-primary/40 hover:bg-primary/10"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn("flex gap-3", msg.role === "user" && "flex-row-reverse")}
              >
                <div
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-lg",
                    msg.role === "user" ? "bg-secondary" : "bg-gradient-to-br from-primary to-sky-500"
                  )}
                >
                  {msg.role === "user" ? <User className="size-4" /> : <Sparkles className="size-4 text-white" />}
                </div>
                <div className={cn("max-w-[80%] space-y-2", msg.role === "user" && "items-end")}>
                  {msg.agentSteps && msg.agentSteps.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {msg.agentSteps.map((step) => (
                        <Badge key={step.agent} variant="secondary" className="gap-1 text-[10px]">
                          <FileSearch className="size-2.5" /> {step.agent.replace("_", " ")}
                        </Badge>
                      ))}
                    </div>
                  )}
                  <div
                    className={cn(
                      "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                      msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted/60"
                    )}
                  >
                    <div className="prose-sm whitespace-pre-wrap">{msg.content}</div>
                    {msg.streaming && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse-glow bg-primary align-middle" />}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        <div className="border-t border-border/60 p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="flex items-center gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a host, alert, or threat behavior…"
              disabled={busy}
              className="h-11"
            />
            <Button type="submit" size="icon" className="size-11 shrink-0" disabled={busy || !input.trim()}>
              <Send className="size-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
