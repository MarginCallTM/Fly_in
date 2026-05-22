"""Pytest suite for MapParser Session B - zone parsing.

Covers: zone attributes, metadata loading, is_start/is_end flags,
comments/blank-line filtering, nb_drones parsing, and all error
cases for zone declarations and file-level structure.

Run with:    pytest test_session_b.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from map_parser import MapParser, MapParseError
from zone import ZoneType


# --- Helpers ------------------------------------------------


def _write_map(tmp_path: Path, content: str) -> str:
    """Write a one-shot map file and return its path as a str.

    pytest's tmp_path fixture gives a fresh folder per test so
    fixtures from different tests cannot pollute each other.
    """
    map_file = tmp_path / "fixture.txt"
    map_file.write_text(content)
    return str(map_file)


# Minimal valid map (no connections required by Graph.validate).
# Tests append their own extra lines on top of this base.
_BASE_MAP = (
    "nb_drones: 2\n"
    "start_hub: A 0 0\n"
    "end_hub: B 10 10\n"
)


# --- Zone attributes: happy path ----------------------------


def test_zone_defaults(tmp_path: Path) -> None:
    """A hub with no metadata uses the correct default values.

    Validates:
        - zone_type defaults to NORMAL
        - max_drones defaults to 1
        - color defaults to None (not set)
    """
    content = _BASE_MAP + "hub: C 5 5\n"
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    zone = graph.get_zone("C")
    assert zone.zone_type == ZoneType.NORMAL
    assert zone.max_drones == 1
    assert zone.color is None


def test_zone_metadata_all_fields(tmp_path: Path) -> None:
    """Metadata zone=restricted, color=red, max_drones=3 all loaded.

    This is the T2.2 validation test from the TODO. Checks that
    all three optional metadata keys are parsed and stored on the
    Zone object with the correct Python types (enum, str, int).
    """
    content = (
        _BASE_MAP
        + "hub: C 5 5 [zone=restricted, color=red, max_drones=3]\n"
    )
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    zone = graph.get_zone("C")
    assert zone.zone_type == ZoneType.RESTRICTED
    assert zone.color == "red"
    assert zone.max_drones == 3


def test_all_zone_types_accepted(tmp_path: Path) -> None:
    """All four valid zone types parse without error.

    The four types are normal, blocked, restricted, priority.
    Each maps to a ZoneType enum value; confirms none are
    accidentally rejected by the parser.
    """
    content = (
        "nb_drones: 1\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
        "hub: C 1 1 [zone=normal]\n"
        "hub: D 2 2 [zone=blocked]\n"
        "hub: E 3 3 [zone=restricted]\n"
        "hub: F 4 4 [zone=priority]\n"
    )
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    assert graph.get_zone("C").zone_type == ZoneType.NORMAL
    assert graph.get_zone("D").zone_type == ZoneType.BLOCKED
    assert graph.get_zone("E").zone_type == ZoneType.RESTRICTED
    assert graph.get_zone("F").zone_type == ZoneType.PRIORITY


def test_start_hub_flag(tmp_path: Path) -> None:
    """The start_hub keyword sets is_start=True, is_end=False.

    The simulator identifies the departure zone via this flag,
    set at parse time and not derived later.
    """
    graph, _ = MapParser().parse(
        _write_map(tmp_path, _BASE_MAP)
    )
    zone_a = graph.get_zone("A")
    assert zone_a.is_start is True
    assert zone_a.is_end is False


def test_end_hub_flag(tmp_path: Path) -> None:
    """The end_hub keyword sets is_end=True, is_start=False.

    Mirror of test_start_hub_flag for the arrival zone.
    """
    graph, _ = MapParser().parse(
        _write_map(tmp_path, _BASE_MAP)
    )
    zone_b = graph.get_zone("B")
    assert zone_b.is_end is True
    assert zone_b.is_start is False


def test_zone_coordinates_stored(tmp_path: Path) -> None:
    """Zone x and y coordinates are stored as integers.

    Validates the string-to-int conversion happened and the
    values are accessible as integers after parsing.
    """
    content = _BASE_MAP + "hub: C 12 34\n"
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    zone = graph.get_zone("C")
    assert zone.x == 12
    assert zone.y == 34


# --- File-level happy path ----------------------------------


def test_nb_drones_returned(tmp_path: Path) -> None:
    """parse() returns the correct nb_drones value.

    The second element of the returned (graph, nb_drones) tuple
    must match the integer from the 'nb_drones:' line.
    """
    content = (
        "nb_drones: 7\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
    )
    _, nb = MapParser().parse(_write_map(tmp_path, content))
    assert nb == 7


def test_comments_and_blank_lines_ignored(tmp_path: Path) -> None:
    """Lines starting with '#' and empty lines are silently skipped.

    This is the T2.3 validation test. The parser must produce a
    valid Graph even when comments and blank lines are scattered
    throughout the file.
    """
    content = (
        "# This is a comment\n"
        "\n"
        "nb_drones: 3\n"
        "# Another comment\n"
        "\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
        "\n"
        "# Final comment\n"
    )
    graph, nb = MapParser().parse(_write_map(tmp_path, content))
    assert nb == 3
    assert "A" in graph.zones
    assert "B" in graph.zones


# --- Zone format errors -------------------------------------


def test_dash_in_zone_name_raises(tmp_path: Path) -> None:
    """A zone name containing '-' must raise MapParseError.

    This is the T2.9 validation test. Zone names with dashes
    would make 'connection: A-B' ambiguous (impossible to know
    where one zone name ends and the other begins).
    """
    content = (
        "nb_drones: 2\n"
        "start_hub: my-start 0 0\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_invalid_zone_type_raises(tmp_path: Path) -> None:
    """An unknown zone type like 'flying' must raise MapParseError.

    This is the T2.5 validation test. Only normal, blocked,
    restricted, and priority are valid values for 'zone='.
    """
    content = _BASE_MAP + "hub: C 5 5 [zone=flying]\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_non_integer_coordinates_raise(tmp_path: Path) -> None:
    """Non-integer coordinates like '0.5' must raise MapParseError.

    Coordinates are declared as integers in the subject format.
    Floats and strings must be rejected with a clear error.
    """
    content = (
        "nb_drones: 2\n"
        "start_hub: A 0.5 0\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_unknown_zone_metadata_key_raises(tmp_path: Path) -> None:
    """An unrecognised metadata key on a zone must raise MapParseError.

    Only 'zone', 'color', and 'max_drones' are allowed. Rejecting
    unknown keys catches silent typos like 'max_drone=' (missing s).
    """
    content = _BASE_MAP + "hub: C 5 5 [speed=fast]\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


# --- Structural errors --------------------------------------


def test_double_start_hub_raises(tmp_path: Path) -> None:
    """Two 'start_hub:' declarations must raise MapParseError.

    This is the T2.4 validation test. The subject requires exactly
    one departure zone; the second declaration must be caught and
    rejected with a clear error referencing the offending line.
    """
    content = (
        "nb_drones: 2\n"
        "start_hub: A 0 0\n"
        "start_hub: A2 1 1\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_double_end_hub_raises(tmp_path: Path) -> None:
    """Two 'end_hub:' declarations must raise MapParseError.

    Mirror of test_double_start_hub_raises for the arrival zone.
    Exactly one end hub is required by the subject.
    """
    content = (
        "nb_drones: 2\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
        "end_hub: B2 11 11\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_missing_start_hub_raises(tmp_path: Path) -> None:
    """A map with no 'start_hub:' must raise MapParseError.

    Graph.validate() runs at the end of parse() and raises
    ValueError when start_hub is None. The parser wraps that
    into MapParseError(0, ...) — line 0 signals a whole-file
    structural problem, not a specific malformed line.
    """
    content = (
        "nb_drones: 2\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_missing_end_hub_raises(tmp_path: Path) -> None:
    """A map with no 'end_hub:' must raise MapParseError.

    Mirror of test_missing_start_hub_raises.
    """
    content = (
        "nb_drones: 2\n"
        "start_hub: A 0 0\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


# --- nb_drones errors ---------------------------------------


def test_duplicate_nb_drones_raises(tmp_path: Path) -> None:
    """Two 'nb_drones:' declarations must raise MapParseError.

    The drone count must appear exactly once. The second occurrence
    is rejected immediately when the parser encounters it.
    """
    content = (
        "nb_drones: 2\n"
        "nb_drones: 3\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_non_integer_nb_drones_raises(tmp_path: Path) -> None:
    """A non-integer value for nb_drones must raise MapParseError.

    'nb_drones: two' cannot be converted to int; the parser must
    surface a clear MapParseError, not a raw Python ValueError.
    """
    content = (
        "nb_drones: two\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_zero_nb_drones_raises(tmp_path: Path) -> None:
    """nb_drones: 0 must raise MapParseError.

    Zero drones is meaningless for the simulation. The subject
    requires a strictly positive integer (> 0).
    """
    content = (
        "nb_drones: 0\n"
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_missing_nb_drones_raises(tmp_path: Path) -> None:
    """A map with no 'nb_drones:' line must raise MapParseError.

    The check runs after the full file is read. The parser raises
    MapParseError(0, ...) since there is no specific line to blame
    — the problem is the absence of a required declaration.
    """
    content = (
        "start_hub: A 0 0\n"
        "end_hub: B 10 10\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))
