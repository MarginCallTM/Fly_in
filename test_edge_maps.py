"""Tests for Phase 3.4 - edge-case map fixtures.

  Each fixture under maps/edge/ exercises an extreme topology that
  the rest of the pipeline (router + simulator) must handle without
  crashing or producing silent garbage.

  At this stage (router and simulator not yet implemented), the
  tests are limited to PARSING and structural invariants. As those
  modules come online, the tests will be extended to assert
  end-to-end behavior (turn counts, no-solution signaling, etc.).

  Run with:    pytest test_edge_maps.py -v
  """

from __future__ import annotations

from map_parser import MapParser
from zone import ZoneType


def test_one_drone_map_parses_with_single_drone() -> None:
    """maps/edge/one_drone.txt declares nb_drones=1 and parses OK.

    Smallest meaningful simulation: a single drone going from
    start to end. Guards against hidden assumptions about plural
    drones (loop ranges starting at 2, batching code, etc.).
    """
    graph, nb = MapParser().parse("maps/edge/one_drone.txt")
    assert nb == 1
    assert graph.start_hub is not None
    assert graph.end_hub is not None
    # Two zones total, one connection - the minimal viable graph.
    assert len(graph.zones) == 2
    assert len(graph.connections) == 1


def test_direct_path_map_has_start_to_end_connection() -> None:
    """maps/edge/direct_path.txt connects start_hub directly to end.

    There is no intermediate zone, so the router must produce a
    path of length 2 (start -> end), and the simulator must finish
    in exactly one turn. Useful to verify that the path-building
    logic handles the trivial 2-node case.
    """
    graph, nb = MapParser().parse("maps/edge/direct_path.txt")
    assert nb == 3
    assert graph.start_hub is not None
    assert graph.end_hub is not None
    direct = graph.get_connection(
        graph.start_hub.name, graph.end_hub.name
    )
    assert direct is not None
    assert direct.max_link_capacity == 3


def test_blocked_only_map_intermediate_is_blocked() -> None:
    """maps/edge/blocked_only.txt: only route crosses a BLOCKED zone.

    Structurally parses fine - no syntactic violation - but the
    only intermediate zone has zone_type BLOCKED, making any path
    invalid. The router MUST detect this and signal 'no solution'
    rather than picking the blocked path or looping forever.

    For now we only verify the topology; the no-solution behavior
    will be tested once router.py is implemented.
    """
    graph, _ = MapParser().parse("maps/edge/blocked_only.txt")
    assert graph.start_hub is not None
    assert graph.end_hub is not None
    wall = graph.get_zone("wall")
    assert wall.zone_type == ZoneType.BLOCKED
    # Confirm there is NO direct shortcut bypassing 'wall'.
    direct = graph.get_connection(
        graph.start_hub.name, graph.end_hub.name
    )
    assert direct is None
