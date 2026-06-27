"""Log parsers — one per data source, all implementing the LogParser interface."""

from app.infrastructure.parsers.base import LogParser, ParseResult
from app.infrastructure.parsers.cloudtrail import CloudTrailParser
from app.infrastructure.parsers.registry import get_parser, list_supported
from app.infrastructure.parsers.sysmon import SysmonParser

__all__ = [
    "CloudTrailParser",
    "LogParser",
    "ParseResult",
    "SysmonParser",
    "get_parser",
    "list_supported",
]
