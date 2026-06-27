"""Sysmon parser.

Accepts Sysmon events exported as JSON (one object per line / JSONL, or a JSON
array). Maps the most security-relevant event IDs (process creation, network
connection, image load, file create) into the normalized schema.
"""

from __future__ import annotations

import json
from typing import Any

from app.domain.enums import DataSourceType
from app.domain.events.normalized_event import (
    FileInfo,
    NetworkInfo,
    NormalizedEvent,
    ProcessInfo,
)
from app.infrastructure.parsers.base import LogParser, ParseResult

# Sysmon Event ID → human action label.
_EVENT_ACTIONS = {
    1: "process_create",
    3: "network_connect",
    7: "image_load",
    11: "file_create",
    12: "registry_create",
    13: "registry_set",
    22: "dns_query",
    23: "file_delete",
}


class SysmonParser(LogParser):
    source_type = DataSourceType.SYSMON

    def parse(self, raw: str | bytes) -> ParseResult:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        result = ParseResult()
        for record in self._iter_records(text, result):
            try:
                result.events.append(self._to_event(record))
            except Exception as exc:  # noqa: BLE001 - capture per-record errors
                result.errors.append(f"sysmon record error: {exc}")
        return result

    def _iter_records(self, text: str, result: ParseResult) -> list[dict[str, Any]]:
        text = text.strip()
        if not text:
            return []
        # Try a JSON array first, then fall back to JSONL.
        if text.startswith("["):
            try:
                data = json.loads(text)
                return data if isinstance(data, list) else [data]
            except json.JSONDecodeError as exc:
                result.errors.append(f"invalid JSON array: {exc}")
                return []
        records: list[dict[str, Any]] = []
        for i, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                result.errors.append(f"line {i}: {exc}")
        return records

    def _to_event(self, r: dict[str, Any]) -> NormalizedEvent:
        # Sysmon exports vary; support both flat and {EventData: {...}} shapes.
        data = {**r, **(r.get("EventData") or {})}
        event_id = int(data.get("EventID") or data.get("event_id") or 0)
        action = _EVENT_ACTIONS.get(event_id, f"sysmon_{event_id}")

        process = ProcessInfo(
            name=data.get("Image"),
            pid=_int(data.get("ProcessId")),
            command_line=data.get("CommandLine"),
            parent_name=data.get("ParentImage"),
            parent_pid=_int(data.get("ParentProcessId")),
            user=data.get("User"),
            hashes=_parse_hashes(data.get("Hashes")),
        )
        network = None
        if event_id == 3:
            network = NetworkInfo(
                src_ip=data.get("SourceIp"),
                src_port=_int(data.get("SourcePort")),
                dst_ip=data.get("DestinationIp"),
                dst_port=_int(data.get("DestinationPort")),
                protocol=data.get("Protocol"),
                domain=data.get("DestinationHostname"),
            )
        file_info = None
        if event_id in (11, 23):
            file_info = FileInfo(path=data.get("TargetFilename"), name=data.get("TargetFilename"))

        return NormalizedEvent(
            timestamp=self.parse_timestamp(data.get("UtcTime") or data.get("timestamp")),
            source_type=self.source_type,
            action=action,
            host=data.get("Computer") or data.get("host"),
            user=data.get("User"),
            message=data.get("RuleName") or action,
            process=process,
            network=network,
            file=file_info,
            raw=r,
        )


def _int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _parse_hashes(value: Any) -> dict[str, str]:
    """Parse Sysmon 'Hashes' field like 'SHA256=ABC,MD5=DEF'."""
    if not isinstance(value, str):
        return {}
    out: dict[str, str] = {}
    for part in value.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out
