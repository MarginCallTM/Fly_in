"""Tests for Phase 4.1 - Dijkstra shortest path.

  Each test builds a tiny graph by hand and asserts the router
  returns the expected path and cost. The graphs are crafted to
  isolate one behaviour each (trivial path, no path, restricted
  cost, etc.) so a failing test points directly at the broken bit.

  Run with:    pytest test_router.py -v
  """

from __future__ import annotations

from zone import Zone, ZoneType
from connection import Connection
from graph import Graph
from router import Router


def _build_graph(
    zones: list[Zone], edges: list[tuple[str, str]],
) -> Graph:
    """Build and validate a Graph from raw zones and edges.

    Helper used by every test to keep fixtures compact. Adds all
    zones first, then connections, then validates.
    """
    g = Graph()
    for z in zones:
        g.add_zone(z)
    for a, b in edges:
        g.add_connection(Connection(a, b))
    g.validate()
    return g


def test_direct_path_two_zones() -> None:
    """T4.1 - shortest_path on a 2-zone graph: just start->end.

    The trivial case: the path contains exactly start and end,
    and the cost equals end.movement_cost() (1 for NORMAL).
    """
    start = Zone("start", 0, 0, is_start=True)
    end = Zone("end", 1, 0, is_end=True)
    graph = _build_graph([start, end], [("start", "end")])
    path = Router(graph).shortest_path("start", "end")
    assert path is not None
    assert [z.name for z in path.zones] == ["start", "end"]
    assert path.cost == 1


def test_no_path_returns_none() -> None:
    """T4.2 - if no route reaches end, shortest_path returns None.

    Two isolated components: start cannot reach end. The router
    must return None instead of raising or returning empty Path.
    """
    start = Zone("start", 0, 0, is_start=True)
    end = Zone("end", 1, 0, is_end=True)
    graph = _build_graph([start, end], [])  # no edge!
    assert Router(graph).shortest_path("start", "end") is None


def test_blocked_zone_skipped() -> None:
    """Blocked zones are never traversed.

    Two routes exist: start->wall->end (wall is BLOCKED) and
    start->detour->end. The router must pick the detour route
    and never touch the wall, even if it would be shorter.
    """
    start = Zone("start", 0, 0, is_start=True)
    wall = Zone("wall", 1, 0, zone_type=ZoneType.BLOCKED)
    detour = Zone("detour", 1, 1)
    end = Zone("end", 2, 0, is_end=True)
    graph = _build_graph(
        [start, wall, detour, end],
        [("start", "wall"), ("wall", "end"),
         ("start", "detour"), ("detour", "end")],
    )
    path = Router(graph).shortest_path("start", "end")
    assert path is not None
    assert "wall" not in [z.name for z in path.zones]


def test_restricted_zone_costs_two() -> None:
    """T4.3 - traversing a RESTRICTED zone costs 2, not 1.

    Path through restricted: start->slow(restricted)->end
    Path through normal:     start->fast(normal)->end
    Both have 3 zones, so a cost-1-per-zone algo would tie them.
    A correct Dijkstra picks the normal one (cost 2 vs 3).
    """
    start = Zone("start", 0, 0, is_start=True)
    slow = Zone("slow", 1, 0, zone_type=ZoneType.RESTRICTED)
    fast = Zone("fast", 1, 1, zone_type=ZoneType.NORMAL)
    end = Zone("end", 2, 0, is_end=True)
    graph = _build_graph(
        [start, slow, fast, end],
        [("start", "slow"), ("slow", "end"),
         ("start", "fast"), ("fast", "end")],
    )
    path = Router(graph).shortest_path("start", "end")
    assert path is not None
    assert "fast" in [z.name for z in path.zones]
    assert path.cost == 2  # fast (1) + end (1)


def test_path_on_real_easy_map() -> None:
    """Integration check: Dijkstra works on a real official map.

    Uses maps/easy/01_linear_path.txt - the simplest official
    map. Validates that the router behaves on real fixtures and
    not just on synthetic micro-graphs.
    """
    from map_parser import MapParser
    graph, _ = MapParser().parse("maps/easy/01_linear_path.txt")
    path = Router(graph).shortest_path("start", "goal")
    assert path is not None
    assert path.zones[0].name == "start"
    assert path.zones[-1].name == "goal"
    # 4 zones, 3 hops through NORMAL zones -> cost 3
    assert path.cost == 3
