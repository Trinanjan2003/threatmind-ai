"""The common normalized event schema (ECS-inspired).

Every supported data source is parsed into this shape before storage and
detection, so the rest of the system is source-agnostic. The full event body
is stored in Elasticsearch; Postgres keeps only references where relational
links are required.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums import DataSourceType


@dataclass(slots=True)
class ProcessInfo:
    name: str | None = None
    pid: int | None = None
    command_line: str | None = None
    parent_name: str | None = None
    parent_pid: int | None = None
    user: str | None = None
    hashes: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class NetworkInfo:
    src_ip: str | None = None
    src_port: int | None = None
    dst_ip: str | None = None
    dst_port: int | None = None
    protocol: str | None = None
    domain: str | None = None
    bytes_sent: int | None = None
    bytes_received: int | None = None


@dataclass(slots=True)
class FileInfo:
    path: str | None = None
    name: str | None = None
    hash_sha256: str | None = None
    size: int | None = None


@dataclass(slots=True)
class CloudInfo:
    provider: str | None = None  # aws | azure | gcp
    account: str | None = None
    region: str | None = None
    service: str | None = None
    event_name: str | None = None


@dataclass(slots=True)
class NormalizedEvent:
    """Source-agnostic representation of a single security event."""

    timestamp: datetime
    source_type: DataSourceType
    action: str
    host: str | None = None
    user: str | None = None
    severity: str | None = None
    message: str | None = None
    process: ProcessInfo | None = None
    network: NetworkInfo | None = None
    file: FileInfo | None = None
    cloud: CloudInfo | None = None
    ingest_job_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def fingerprint(self) -> str:
        """Stable content hash for idempotent ingestion (dedup)."""
        basis = {
            "ts": self.timestamp.isoformat(),
            "src": self.source_type.value,
            "action": self.action,
            "host": self.host,
            "user": self.user,
            "raw": self.raw,
        }
        encoded = json.dumps(basis, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    def to_document(self) -> dict[str, Any]:
        """Serialize to an Elasticsearch document."""
        doc = asdict(self)
        doc["@timestamp"] = self.timestamp.isoformat()
        doc["source_type"] = self.source_type.value
        doc["event_hash"] = self.fingerprint()
        doc.pop("timestamp", None)
        return doc
