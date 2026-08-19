"""Canon database subsystem: parsed source, search, entities, and queries.

This module builds and serves the read-only Canon index over the Mushoku
Tensei novel text. The raw TXT and its chunk index remain authoritative for
evidence; structured extraction is always verified against them.
"""

from overlord_worldsim.canon.model import (
    Chunk,
    Scene,
    SkippedLine,
    Unit,
    UnitKind,
    Volume,
)
from overlord_worldsim.canon.parse import (
    PARSED_ARTIFACT_VERSION,
    ParsedDocument,
    parse_header_line,
    parse_source,
)

__all__ = [
    "PARSED_ARTIFACT_VERSION",
    "Chunk",
    "ParsedDocument",
    "Scene",
    "SkippedLine",
    "Unit",
    "UnitKind",
    "Volume",
    "parse_header_line",
    "parse_source",
]
