"""The eight specialized threat-hunting agents.

Each agent has a narrow responsibility and contributes findings (with evidence)
to the shared HuntState. All agents degrade to deterministic heuristics when the
local LLM is unavailable, keeping hunts reproducible and explainable.
"""

from __future__ import annotations

from app.application.detection.engine import DetectionEngine
from app.domain.enums import AgentName
from app.infrastructure.agents.base import BaseAgent
from app.infrastructure.agents.state import Finding, HuntState
from app.infrastructure.mitre.knowledge_base import MITRE_TECHNIQUES, get_technique

# Lightweight local threat-intel reputation table (offline, free).
_BAD_INDICATORS = {
    "cdn-update-svc.top": "Newly-registered domain linked to commodity loaders",
    "185.234.219.10": "IP in a range associated with malware C2",
    ".lockbit": "Known ransomware file extension",
}


class ThreatIntelligenceAgent(BaseAgent):
    name = AgentName.THREAT_INTEL.value

    async def _execute(self, state: HuntState) -> HuntState:
        for ioc in state.iocs:
            value = str(ioc.get("value", "")).lower()
            for indicator, note in _BAD_INDICATORS.items():
                if indicator in value:
                    state.add_finding(
                        Finding(
                            agent=self.name,
                            title=f"Malicious indicator: {ioc.get('value')}",
                            detail=note,
                            confidence=82,
                            severity="high",
                            evidence_refs=[ioc.get("event_id", "ioc")],
                        )
                    )
        return state


class IOCCorrelationAgent(BaseAgent):
    name = AgentName.IOC_CORRELATION.value

    async def _execute(self, state: HuntState) -> HuntState:
        # Extract indicators from events (IPs, domains, hashes, file extensions).
        for ev in state.events:
            net = ev.get("network") or {}
            if net.get("dst_ip"):
                state.iocs.append({"type": "ip", "value": net["dst_ip"], "event_id": ev.get("event_hash", "")})
            if net.get("domain"):
                state.iocs.append({"type": "domain", "value": net["domain"], "event_id": ev.get("event_hash", "")})
            proc = ev.get("process") or {}
            for algo, h in (proc.get("hashes") or {}).items():
                state.iocs.append({"type": "file_hash", "value": h, "algo": algo, "event_id": ev.get("event_hash", "")})
        if state.iocs:
            hosts = {ev.get("host") for ev in state.events if ev.get("host")}
            if len(hosts) > 1:
                state.add_finding(
                    Finding(
                        agent=self.name,
                        title="Indicators correlated across multiple hosts",
                        detail=f"Related indicators observed across {len(hosts)} hosts, suggesting coordinated activity.",
                        confidence=70,
                        severity="high",
                        evidence_refs=[i.get("event_id", "") for i in state.iocs[:5]],
                    )
                )
        return state


class LogInvestigationAgent(BaseAgent):
    name = AgentName.LOG_INVESTIGATION.value

    async def _execute(self, state: HuntState) -> HuntState:
        # Use the deterministic detection engine over collected events as a base,
        # then optionally let the LLM add narrative context.
        from app.domain.events.normalized_event import NormalizedEvent  # local import

        suspicious = [
            ev for ev in state.events
            if any(
                kw in str(ev.get("process", {}).get("command_line", "")).lower()
                for kw in ("-enc", "powershell", "lsass", "mimikatz", "rundll32")
            )
        ]
        for ev in suspicious[:10]:
            cmd = ev.get("process", {}).get("command_line", "")
            state.add_finding(
                Finding(
                    agent=self.name,
                    title=f"Suspicious process activity on {ev.get('host', 'unknown')}",
                    detail=f"Observed command line: {cmd[:160]}",
                    confidence=66,
                    severity="medium",
                    technique_ids=["T1059.001"] if "powershell" in cmd.lower() else [],
                    evidence_refs=[ev.get("event_hash", "event")],
                )
            )
        return state


class MalwareAnalysisAgent(BaseAgent):
    name = AgentName.MALWARE_ANALYSIS.value

    async def _execute(self, state: HuntState) -> HuntState:
        for ev in state.events:
            img = str(ev.get("process", {}).get("name", "")).lower()
            if "\\temp\\" in img or "/tmp/" in img:  # nosec B108 - detection signature, not file I/O
                state.add_finding(
                    Finding(
                        agent=self.name,
                        title="Execution from temporary directory",
                        detail=f"Binary executed from a temp path: {img}. Common for dropped malware.",
                        confidence=64,
                        severity="medium",
                        technique_ids=["T1543.003"],
                        evidence_refs=[ev.get("event_hash", "event")],
                    )
                )
        return state


class MitreMappingAgent(BaseAgent):
    name = AgentName.MITRE_MAPPING.value

    async def _execute(self, state: HuntState) -> HuntState:
        # Ensure all technique ids referenced so far are valid and enriched.
        validated: set[str] = set()
        for tid in list(state.technique_ids):
            if get_technique(tid):
                validated.add(tid)
        state.technique_ids = validated
        if validated:
            tactics = {
                rec.tactic.value for t in validated if (rec := get_technique(t)) is not None
            }
            state.add_finding(
                Finding(
                    agent=self.name,
                    title="ATT&CK coverage of observed behavior",
                    detail=f"Activity maps to {len(validated)} techniques across tactics: {', '.join(sorted(tactics))}.",
                    confidence=72,
                    severity="info",
                    technique_ids=sorted(validated),
                    evidence_refs=["derived"],
                )
            )
        return state


class RiskScoringAgent(BaseAgent):
    name = AgentName.RISK_SCORING.value

    _SEV_WEIGHT = {"critical": 100, "high": 75, "medium": 50, "low": 25, "info": 10}

    async def _execute(self, state: HuntState) -> HuntState:
        if not state.findings:
            state.risk_score = 0
            return state
        # Weighted blend of the strongest findings + breadth of techniques.
        scored = [
            self._SEV_WEIGHT.get(f.severity, 40) * (f.confidence / 100) for f in state.findings
        ]
        top = sorted(scored, reverse=True)[:5]
        base = sum(top) / len(top)
        breadth_bonus = min(len(state.technique_ids) * 3, 20)
        state.risk_score = min(100, round(base + breadth_bonus))
        return state


class DetectionEngineeringAgent(BaseAgent):
    name = AgentName.DETECTION_ENGINEERING.value

    async def _execute(self, state: HuntState) -> HuntState:
        from app.infrastructure.detections.generators import generate_detection

        # Generate a Sigma rule for the highest-signal technique seen.
        if state.technique_ids:
            tid = sorted(state.technique_ids)[0]
            rule = generate_detection(fmt="sigma", technique_id=tid, context=state.focus or state.query)
            state.detections.append({"format": "sigma", "technique_id": tid, "content": rule})
        return state


class ReportingAgent(BaseAgent):
    name = AgentName.REPORTING.value

    async def _execute(self, state: HuntState) -> HuntState:
        # Try the LLM for a narrative summary; fall back to a structured template.
        findings_text = "\n".join(
            f"- [{f.severity}] {f.title} ({f.confidence}%): {f.detail}" for f in state.findings
        )
        llm_summary = await self._llm_or_none(
            system=(
                "You are a senior SOC analyst. Write a concise, factual incident "
                "summary from the findings. Only state what the evidence supports."
            ),
            user=f"Focus: {state.focus or state.query}\nFindings:\n{findings_text}",
        )
        if llm_summary:
            state.summary = llm_summary.strip()
        else:
            crit = sum(1 for f in state.findings if f.severity in ("critical", "high"))
            state.summary = (
                f"Hunt '{state.focus or state.query}' produced {len(state.findings)} findings "
                f"({crit} high-severity) with an aggregate risk score of {state.risk_score}/100, "
                f"spanning {len(state.technique_ids)} MITRE ATT&CK techniques."
            )
        state.report_markdown = _render_report(state)
        return state


def _render_report(state: HuntState) -> str:
    lines = [
        f"# Incident Report — {state.focus or state.query}",
        "",
        f"**Hunt ID:** `{state.hunt_id}`  ",
        f"**Risk Score:** {state.risk_score}/100  ",
        f"**Agents executed:** {', '.join(state.agent_trace)}",
        "",
        "## Summary",
        state.summary,
        "",
        "## Findings",
    ]
    for f in sorted(state.findings, key=lambda x: x.confidence, reverse=True):
        techniques = ", ".join(f.technique_ids) if f.technique_ids else "—"
        lines.append(f"- **{f.title}** _(severity: {f.severity}, confidence: {f.confidence}%)_")
        lines.append(f"  - {f.detail}")
        lines.append(f"  - MITRE: {techniques}")
    lines += ["", "## MITRE ATT&CK Techniques", ""]
    for tid in sorted(state.technique_ids):
        rec = MITRE_TECHNIQUES.get(tid)
        if rec:
            lines.append(f"- `{tid}` {rec.name} ({rec.tactic.value})")
    lines += ["", "## Recommended Actions", ""]
    lines += [
        "1. Isolate affected hosts pending confirmation.",
        "2. Reset credentials for impacted identities.",
        "3. Hunt fleet-wide for the same TTPs.",
        "4. Deploy the generated detection content.",
    ]
    return "\n".join(lines)


# Ordered roster used by the orchestrator.
AGENT_CLASSES: list[type[BaseAgent]] = [
    IOCCorrelationAgent,
    ThreatIntelligenceAgent,
    LogInvestigationAgent,
    MalwareAnalysisAgent,
    MitreMappingAgent,
    RiskScoringAgent,
    DetectionEngineeringAgent,
    ReportingAgent,
]
