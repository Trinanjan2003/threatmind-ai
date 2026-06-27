"""Unit tests for the Sysmon and CloudTrail parsers."""

from __future__ import annotations

import json

from app.domain.enums import DataSourceType
from app.infrastructure.parsers import CloudTrailParser, SysmonParser, get_parser


class TestSysmonParser:
    def test_parses_process_create_jsonl(self) -> None:
        record = {
            "EventID": 1,
            "UtcTime": "2026-06-27 09:01:20.123",
            "Computer": "WIN-001",
            "User": "CORP\\j.doe",
            "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "ParentImage": "C:\\Program Files\\Microsoft Office\\winword.exe",
            "CommandLine": "powershell.exe -enc SQBFAFgA",
            "ProcessId": "4321",
            "ParentProcessId": "1000",
            "Hashes": "SHA256=ABC123,MD5=DEF456",
        }
        result = SysmonParser().parse(json.dumps(record))
        assert not result.errors
        assert len(result.events) == 1
        ev = result.events[0]
        assert ev.source_type == DataSourceType.SYSMON
        assert ev.action == "process_create"
        assert ev.host == "WIN-001"
        assert ev.process is not None
        assert ev.process.parent_name.endswith("winword.exe")
        assert ev.process.hashes["sha256"] == "ABC123"

    def test_parses_json_array(self) -> None:
        records = [{"EventID": 3, "DestinationIp": "10.0.0.5", "DestinationPort": "443"}]
        result = SysmonParser().parse(json.dumps(records))
        assert len(result.events) == 1
        assert result.events[0].network is not None
        assert result.events[0].network.dst_ip == "10.0.0.5"

    def test_invalid_line_recorded_as_error(self) -> None:
        result = SysmonParser().parse('{"EventID": 1}\nNOT JSON\n')
        assert len(result.events) == 1
        assert len(result.errors) == 1

    def test_empty_input(self) -> None:
        result = SysmonParser().parse("")
        assert result.total == 0


class TestCloudTrailParser:
    def test_parses_records_envelope(self) -> None:
        payload = {
            "Records": [
                {
                    "eventTime": "2026-06-27T09:30:00Z",
                    "eventSource": "iam.amazonaws.com",
                    "eventName": "AttachUserPolicy",
                    "awsRegion": "us-east-1",
                    "sourceIPAddress": "203.0.113.10",
                    "recipientAccountId": "123456789012",
                    "userIdentity": {"userName": "intern", "type": "IAMUser"},
                    "readOnly": False,
                }
            ]
        }
        result = CloudTrailParser().parse(json.dumps(payload))
        assert len(result.events) == 1
        ev = result.events[0]
        assert ev.cloud is not None
        assert ev.cloud.event_name == "AttachUserPolicy"
        assert ev.cloud.provider == "aws"
        assert ev.user == "intern"
        assert "mutating" in ev.tags

    def test_registry_resolves_parser(self) -> None:
        assert isinstance(get_parser(DataSourceType.SYSMON), SysmonParser)
        assert isinstance(get_parser(DataSourceType.CLOUDTRAIL), CloudTrailParser)
