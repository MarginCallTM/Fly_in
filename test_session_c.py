"""Pytest suite for MapParser Session C - connection parsing.

Each test writes a tiny map to a temporary file, runs MapParser
on it, and checks either the resulting Graph (happy path) or
that the expected exception is raised (error cases).

Run with:    pytest test_session_c.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from map_parser import MapParser, MapParseError


# --- Helpers ------------------------------------------------


def _write_map(tmp_path: Path, content: str) -> str:
    """Write a one-shot map file and return its path as a str.

    pytest's tmp_path fixture gives us a fresh empty folder per
    test, so two tests cannot pollute each other's fixtures.
    """
    map_file = tmp_path / "fixture.txt"
    map_file.write_text(content)
    return str(map_file)


# Base map shared by most tests: 1 start, 1 end, 1 normal hub.
# Each test appends its own 'connection:' lines on top of this.
_BASE_ZONES = (
    "nb_drones: 2\n"
    "start_hub: A 0 0\n"
    "end_hub: B 10 10\n"
    "hub: C 5 5\n"
)


# --- Happy path --------------------------------------------


def test_single_connection_default_capacity(
        tmp_path: Path,
) -> None:
    """A bare 'connection: A-B' should parse with default cap=1.

    Validates:
        - the connection is added to graph.connections
        - both endpoint names are correctly extracted
        - max_link_capacity defaults to 1 when no metadata
    """
    content = _BASE_ZONES + "connection: A-B\n"
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    assert len(graph.connections) == 1
    conn = graph.connections[0]
    assert {conn.zone_a, conn.zone_b} == {"A", "B"}
    assert conn.max_link_capacity == 1


def test_connection_with_explicit_capacity(
        tmp_path: Path,
) -> None:
    """'connection: A-B [max_link_capacity=3]' should set cap=3.

    Validates that the metadata block is read and the integer
    capacity overrides the default.
    """
    content = (
        _BASE_ZONES
        + "connection: A-B [max_link_capacity=3]\n"
    )
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    assert graph.connections[0].max_link_capacity == 3


def test_multiple_connections_all_kept(tmp_path: Path) -> None:
    """Several connections in the same file are all preserved.

    Validates that the parser does not silently overwrite or
    drop entries when more than one 'connection:' line appears.
    """
    content = (
        _BASE_ZONES
        + "connection: A-C\n"
        + "connection: C-B [max_link_capacity=2]\n"
    )
    graph, _ = MapParser().parse(_write_map(tmp_path, content))
    assert len(graph.connections) == 2


# --- Format errors -----------------------------------------


def test_missing_dash_raises(tmp_path: Path) -> None:
    """'connection: AB' (no dash) must raise MapParseError.

    Without a '-' there is no way to split into two endpoint
    names. The parser must fail loudly instead of guessing.
    """
    content = _BASE_ZONES + "connection: AB\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_too_many_dashes_raises(tmp_path: Path) -> None:
    """'connection: A-B-C' must raise MapParseError.

    Zone names cannot contain '-' (enforced by _parse_zone),
    so exactly one dash is expected. Three tokens is ambiguous
    and the parser must reject it.
    """
    content = _BASE_ZONES + "connection: A-B-C\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_self_loop_raises(tmp_path: Path) -> None:
    """'connection: A-A' must raise MapParseError.

    A connection from a zone to itself is degenerate (no
    movement happens). The parser refuses it to keep the
    graph semantically meaningful.
    """
    content = _BASE_ZONES + "connection: A-A\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_empty_endpoint_raises(tmp_path: Path) -> None:
    """'connection: -A' must raise MapParseError.

    Even with a dash present, both sides must contain a
    non-empty zone name. '-A' has an empty left endpoint.
    """
    content = _BASE_ZONES + "connection: -A\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_empty_body_raises(tmp_path: Path) -> None:
    """'connection:' with nothing after the colon must fail.

    No endpoints means nothing to build. The parser raises
    before reaching _split_endpoints.
    """
    content = _BASE_ZONES + "connection:\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


# --- Graph-level errors (raised by Graph.add_connection) ---


def test_unknown_zone_raises(tmp_path: Path) -> None:
    """'connection: A-X' (X never declared) must fail.

    Graph.add_connection checks that both endpoints exist in
    the zones dict and raises ValueError. We accept either
    ValueError or MapParseError (depending on how the parser
    wraps the error in task 2.8 later).
    """
    content = _BASE_ZONES + "connection: A-X\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_duplicate_connection_raises(tmp_path: Path) -> None:
    """'A-B' then 'B-A' must be detected as the same edge.

    Connection.__eq__ uses frozenset({a, b}) so the order
    does not matter. Graph.add_connection refuses the second
    declaration, enforcing subject rule VII.4.
    """
    content = (
        _BASE_ZONES
        + "connection: A-B\n"
        + "connection: B-A\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


# --- Metadata errors ---------------------------------------


def test_unknown_metadata_key_raises(tmp_path: Path) -> None:
    """Only 'max_link_capacity' is allowed on a connection.

    'color=red' is valid on a zone but NOT on a connection.
    Rejecting unknown keys catches typos like
    'max_link_capacityy=' or 'max_link_capa=' early.
    """
    content = _BASE_ZONES + "connection: A-B [color=red]\n"
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_zero_capacity_raises(tmp_path: Path) -> None:
    """'max_link_capacity=0' is not > 0 and must fail.

    A connection that nothing can cross is meaningless. The
    subject specifies that capacities are positive integers.
    """
    content = (
        _BASE_ZONES
        + "connection: A-B [max_link_capacity=0]\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_negative_capacity_raises(tmp_path: Path) -> None:
    """'max_link_capacity=-1' must fail.

    Same rule as the zero case: capacity must be strictly
    positive. Negative values would also break the
    'has_capacity()' logic in Connection.
    """
    content = (
        _BASE_ZONES
        + "connection: A-B [max_link_capacity=-1]\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))


def test_non_integer_capacity_raises(tmp_path: Path) -> None:
    """'max_link_capacity=abc' must fail.

    The parser converts the value with int(); a non-integer
    must surface as a MapParseError with a clear line number,
    NOT as a raw ValueError bubbling up to the user.
    """
    content = (
        _BASE_ZONES
        + "connection: A-B [max_link_capacity=abc]\n"
    )
    with pytest.raises(MapParseError):
        MapParser().parse(_write_map(tmp_path, content))
