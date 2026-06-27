"""Parser registry — resolves a DataSourceType to its parser implementation.

Sysmon and CloudTrail are fully implemented in this phase. The remaining
supported sources are declared here and raise a clear NotImplementedError until
their parsers land, all following the same ``LogParser`` interface.
"""

from __future__ import annotations

from app.domain.enums import DataSourceType
from app.infrastructure.parsers.base import LogParser
from app.infrastructure.parsers.cloudtrail import CloudTrailParser
from app.infrastructure.parsers.sysmon import SysmonParser

_IMPLEMENTED: dict[DataSourceType, type[LogParser]] = {
    DataSourceType.SYSMON: SysmonParser,
    DataSourceType.CLOUDTRAIL: CloudTrailParser,
}


def get_parser(source_type: DataSourceType) -> LogParser:
    parser_cls = _IMPLEMENTED.get(source_type)
    if parser_cls is None:
        raise NotImplementedError(
            f"Parser for '{source_type.value}' is not yet implemented. "
            f"Implemented: {', '.join(s.value for s in _IMPLEMENTED)}."
        )
    return parser_cls()


def list_supported() -> dict[str, bool]:
    """Map every supported source type to whether its parser is implemented."""
    return {s.value: s in _IMPLEMENTED for s in DataSourceType}
