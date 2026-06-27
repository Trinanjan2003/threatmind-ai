"""AWS CloudTrail parser.

Accepts CloudTrail exports as a JSON object with a ``Records`` array (the native
format), a bare JSON array, or JSONL. Maps each API event into the normalized
schema with cloud context populated.
"""

from __future__ import annotations

import json
from typing import Any

from app.domain.enums import DataSourceType
from app.domain.events.normalized_event import (
    CloudInfo,
    NetworkInfo,
    NormalizedEvent,
)
from app.infrastructure.parsers.base import LogParser, ParseResult


class CloudTrailParser(LogParser):
    source_type = DataSourceType.CLOUDTRAIL

    def parse(self, raw: str | bytes) -> ParseResult:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        result = ParseResult()
        for record in self._iter_records(text, result):
            try:
                result.events.append(self._to_event(record))
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"cloudtrail record error: {exc}")
        return result

    def _iter_records(self, text: str, result: ParseResult) -> list[dict[str, Any]]:
        text = text.strip()
        if not text:
            return []
        if text.startswith("{"):
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                result.errors.append(f"invalid JSON object: {exc}")
                return []
            if isinstance(obj, dict) and "Records" in obj:
                return list(obj["Records"])
            return [obj]
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
        identity = r.get("userIdentity") or {}
        user = (
            identity.get("userName")
            or identity.get("arn")
            or identity.get("principalId")
            or identity.get("type")
        )
        event_name = r.get("eventName", "unknown")
        cloud = CloudInfo(
            provider="aws",
            account=r.get("recipientAccountId") or identity.get("accountId"),
            region=r.get("awsRegion"),
            service=r.get("eventSource"),
            event_name=event_name,
        )
        network = NetworkInfo(src_ip=r.get("sourceIPAddress"))
        tags = []
        if r.get("errorCode"):
            tags.append("api_error")
        if r.get("readOnly") is False:
            tags.append("mutating")

        return NormalizedEvent(
            timestamp=self.parse_timestamp(r.get("eventTime")),
            source_type=self.source_type,
            action=event_name,
            host=r.get("eventSource"),
            user=user,
            message=f"{r.get('eventSource')}:{event_name}",
            network=network,
            cloud=cloud,
            tags=tags,
            raw=r,
        )
