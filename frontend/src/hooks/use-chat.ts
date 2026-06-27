"use client";

import * as React from "react";
import type { ChatMessage } from "@/lib/types";

const CANNED_ANSWER = `Based on correlated telemetry from **WIN-001**, I've identified a high-confidence intrusion chain:

**1. Initial Access (T1566.001)** — A macro-enabled document (invoice.docm) was opened, spawning encoded PowerShell from winword.exe.

**2. Credential Access (T1003.001)** — An unsigned binary opened a read handle to LSASS memory, consistent with credential dumping.

**3. Lateral Movement (T1021.002)** — The stolen credential accessed administrative shares across 12 hosts within 5 minutes.

**Assessment:** Coordinated, multi-stage attack scored **94/100**. Recommend immediate host isolation and a fleet-wide hunt for the same parent-child process lineage.`;

const AGENT_SEQUENCE = [
  "log_investigation",
  "ioc_correlation",
  "threat_intel",
  "mitre_mapping",
  "risk_scoring",
  "reporting",
];

/**
 * Chat hook that attempts a live backend WebSocket and transparently falls back
 * to a realistic local simulation when the backend/Ollama is unavailable — so
 * the experience is always demonstrable.
 */
export function useChat() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [busy, setBusy] = React.useState(false);

  const updateAssistant = React.useCallback((id: string, patch: Partial<ChatMessage>) => {
    setMessages((m) => m.map((msg) => (msg.id === id ? { ...msg, ...patch } : msg)));
  }, []);

  const simulate = React.useCallback(
    async (assistantId: string) => {
      for (let i = 0; i < AGENT_SEQUENCE.length; i++) {
        await new Promise((r) => setTimeout(r, 300));
        updateAssistant(assistantId, {
          agentSteps: AGENT_SEQUENCE.slice(0, i + 1).map((a) => ({ agent: a, status: "completed" })),
        });
      }
      const tokens = CANNED_ANSWER.split(" ");
      for (let i = 0; i < tokens.length; i++) {
        await new Promise((r) => setTimeout(r, 16));
        updateAssistant(assistantId, { content: tokens.slice(0, i + 1).join(" ") });
      }
      updateAssistant(assistantId, { streaming: false });
    },
    [updateAssistant]
  );

  const tryLiveWebSocket = React.useCallback(
    (question: string, assistantId: string): Promise<boolean> => {
      return new Promise((resolve) => {
        const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
        if (!base) return resolve(false);
        let opened = false;
        try {
          const token = window.localStorage.getItem("tmai_access_token") ?? "";
          const url = base.replace(/^http/, "ws") + `/api/v1/chat/ws?token=${token}`;
          const ws = new WebSocket(url);
          const steps: { agent: string; status: string }[] = [];
          let content = "";

          const timeout = setTimeout(() => {
            if (!opened) { ws.close(); resolve(false); }
          }, 1500);

          ws.onopen = () => {
            opened = true;
            clearTimeout(timeout);
            ws.send(JSON.stringify({ type: "user_message", content: question }));
          };
          ws.onmessage = (ev) => {
            const msg = JSON.parse(ev.data);
            if (msg.type === "agent_step") {
              steps.push({ agent: msg.agent, status: msg.status });
              updateAssistant(assistantId, { agentSteps: [...steps] });
            } else if (msg.type === "token") {
              content += msg.content;
              updateAssistant(assistantId, { content });
            } else if (msg.type === "done") {
              updateAssistant(assistantId, { streaming: false });
              ws.close();
              resolve(true);
            } else if (msg.type === "error") {
              ws.close();
              resolve(false);
            }
          };
          ws.onerror = () => { clearTimeout(timeout); resolve(false); };
        } catch {
          resolve(false);
        }
      });
    },
    [updateAssistant]
  );

  const send = React.useCallback(
    async (text: string) => {
      if (!text.trim() || busy) return;
      setBusy(true);
      const idx = messages.length;
      const assistantId = `a-${idx}`;
      setMessages((m) => [
        ...m,
        { id: `u-${idx}`, role: "user", content: text },
        { id: assistantId, role: "assistant", content: "", streaming: true, agentSteps: [] },
      ]);

      const live = await tryLiveWebSocket(text, assistantId);
      if (!live) await simulate(assistantId);
      setBusy(false);
    },
    [busy, messages.length, simulate, tryLiveWebSocket]
  );

  return { messages, busy, send };
}
