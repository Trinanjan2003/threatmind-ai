"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Sparkles, Copy, Check, Code2 } from "lucide-react";
import { PageHeader } from "@/components/features/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

const SAMPLES: Record<string, { lang: string; code: string }> = {
  sigma: {
    lang: "yaml",
    code: `title: Encoded PowerShell from Office Application
id: 7e1f4c2a-9d3b-4f5e-8a1c-2b3d4e5f6a7b
status: experimental
description: Detects Office apps spawning encoded PowerShell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    ParentImage|endswith:
      - '\\\\winword.exe'
      - '\\\\excel.exe'
    Image|endswith: '\\\\powershell.exe'
    CommandLine|contains:
      - '-enc'
      - '-EncodedCommand'
  condition: selection
level: high
tags:
  - attack.execution
  - attack.t1059.001`,
  },
  yara: {
    lang: "yara",
    code: `rule Suspicious_Encoded_PowerShell {
  meta:
    author = "ThreatMind AI"
    description = "Detects base64-encoded PowerShell payloads"
    mitre = "T1059.001"
  strings:
    $enc = "-EncodedCommand" ascii wide nocase
    $iex = "IEX" ascii wide nocase
    $dl  = "DownloadString" ascii wide nocase
  condition:
    $enc and ($iex or $dl)
}`,
  },
  suricata: {
    lang: "text",
    code: `alert http $HOME_NET any -> $EXTERNAL_NET any (
  msg:"ThreatMind C2 Beacon - periodic low-reputation HTTPS";
  flow:established,to_server;
  http.method; content:"GET";
  http.user_agent; content:"Mozilla/5.0";
  threshold: type both, track by_src, count 10, seconds 600;
  classtype:command-and-control;
  sid:9100001; rev:1;
)`,
  },
  splunk_spl: {
    lang: "text",
    code: `index=sysmon EventCode=1
  (ParentImage="*\\\\winword.exe" OR ParentImage="*\\\\excel.exe")
  Image="*\\\\powershell.exe"
  (CommandLine="*-enc*" OR CommandLine="*-EncodedCommand*")
| stats count by host, User, ParentImage, CommandLine
| where count > 0
| sort - count`,
  },
  kql: {
    lang: "kql",
    code: `DeviceProcessEvents
| where InitiatingProcessFileName in~ ("winword.exe", "excel.exe")
| where FileName =~ "powershell.exe"
| where ProcessCommandLine has_any ("-enc", "-EncodedCommand")
| project Timestamp, DeviceName, AccountName, InitiatingProcessFileName, ProcessCommandLine
| order by Timestamp desc`,
  },
};

const FORMATS = [
  { key: "sigma", label: "Sigma" },
  { key: "yara", label: "YARA" },
  { key: "suricata", label: "Suricata" },
  { key: "splunk_spl", label: "Splunk SPL" },
  { key: "kql", label: "KQL" },
];

export default function DetectionsPage() {
  const [format, setFormat] = React.useState("sigma");
  const [copied, setCopied] = React.useState(false);
  const sample = SAMPLES[format];

  function copy() {
    navigator.clipboard?.writeText(sample.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Detection Studio"
        description="Auto-generate detection content from confirmed findings"
        actions={
          <Button size="sm"><Sparkles className="size-4" /> Generate from Alert</Button>
        }
      />

      <Tabs value={format} onValueChange={setFormat}>
        <TabsList>
          {FORMATS.map((f) => (
            <TabsTrigger key={f.key} value={f.key}>{f.label}</TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <motion.div key={format} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <Card glass>
          <div className="flex items-center justify-between border-b border-border/60 px-4 py-2.5">
            <div className="flex items-center gap-2">
              <Code2 className="size-4 text-primary" />
              <span className="text-sm font-medium">Generated {FORMATS.find((f) => f.key === format)?.label} rule</span>
              <Badge variant="secondary" className="text-[10px]">T1059.001</Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={copy}>
              {copied ? <Check className="size-4 text-emerald-500" /> : <Copy className="size-4" />}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
          <CardContent className="p-0">
            <pre className={cn("overflow-x-auto p-4 font-mono text-xs leading-relaxed text-foreground/90")}>
              <code>{sample.code}</code>
            </pre>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
