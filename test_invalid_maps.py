"""Tests for Phase 3.3 - invalid map fixtures.

  Each fixture under maps/invalid/ is crafted to trigger one specific
  MapParseError. The test asserts both that the exception is raised
  AND that its line_no attribute matches the offending line.

  This complements the synthetic tests in test_session_b.py and
  test_session_c.py: those use tmp_path fixtures, these use real
  files on disk so we can also run them manually via:

      make run MAP=maps/invalid/double_start.txt

  Run with:    pytest test_invalid_maps.py -v
  """

from __future__ import annotations

import pytest

from map_parser import MapParser, MapParseError

# (map path, expected line number where the parser must abort).
# Each entry pairs a real fixture with the line we expect the
# parser to flag - this is what subject rule VII.4 requires.
INVALID_MAPS = [
    ("maps/invalid/double_start.txt", 4),
    ("maps/invalid/bad_zone_type.txt", 5),
    ("maps/invalid/duplicate_connection.txt", 6),
    ("maps/invalid/unknown_zone_in_connection.txt", 5),
    ("maps/invalid/negative_capacity.txt", 5),
    ("maps/invalid/dash_in_name.txt", 3),
]


@pytest.mark.parametrize(
    "map_path, expected_line", INVALID_MAPS
)
def test_invalid_map_raises_at_expected_line(
        map_path: str, expected_line: int,
) -> None:
    """Each invalid fixture raises MapParseError at the right line.

    Validates two things at once:
        - the parser surfaces a MapParseError (not a raw ValueError
          or some unrelated exception),
        - the error carries the line number of the actual offence,
          which is what subject rule VII.4 requires for diagnostics.
    """
    with pytest.raises(MapParseError) as excinfo:
        MapParser().parse(map_path)
    assert excinfo.value.line_no == expected_line
