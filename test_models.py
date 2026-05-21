"""Tests for Phase 1 models: Zone, Connection, Drone, Graph."""

import pytest

from zone import Zone, ZoneType
from connection import Connection
from drone import Drone, DroneStatus
from graph import Graph


# ── zone.py ──────────────────────────────────────────────────────────


def test_zone_type_values() -> None:
    """T1.1 — ZoneType has exactly 4 members."""
    expected = {"NORMAL", "BLOCKED", "RESTRICTED", "PRIORITY"}
    assert {m.name for m in ZoneType} == expected


def test_movement_cost() -> None:
    """T1.2 — RESTRICTED costs 2, all others cost 1."""
    assert Zone("a", 0, 0, ZoneType.NORMAL).movement_cost() == 1
    assert Zone("b", 0, 0, ZoneType.PRIORITY).movement_cost() == 1
    assert Zone("c", 0, 0, ZoneType.BLOCKED).movement_cost() == 1
    assert Zone("d", 0, 0, ZoneType.RESTRICTED).movement_cost() == 2


def test_is_full_unlimited_for_start_end() -> None:
    """T1.3 — start and end zones are never full."""
    start = Zone("s", 0, 0, max_drones=1, is_start=True)
    end = Zone("e", 1, 0, max_drones=1, is_end=True)
    start.current_drones = {1, 2, 3}
    end.current_drones = {1, 2, 3}
    assert not start.is_full()
    assert not end.is_full()


def test_is_full_respects_max_drones() -> None:
    """T1.4 — is_full returns True when occupancy >= max_drones."""
    zone = Zone("z", 0, 0, max_drones=2)
    assert not zone.is_full()
    zone.current_drones = {1}
    assert not zone.is_full()
    zone.current_drones = {1, 2}
    assert zone.is_full()


def test_add_drone_raises_on_full_or_blocked() -> None:
    """T1.5 — add_drone raises ValueError if full or blocked."""
    full_zone = Zone("f", 0, 0, max_drones=1)
    full_zone.current_drones = {1}
    with pytest.raises(ValueError):
        full_zone.add_drone(2)

    blocked = Zone("b", 0, 0, ZoneType.BLOCKED)
    with pytest.raises(ValueError):
        blocked.add_drone(1)


def test_remove_drone_raises_if_absent() -> None:
    """T1.6 — remove_drone raises KeyError for unknown drone_id."""
    zone = Zone("z", 0, 0)
    with pytest.raises(KeyError):
        zone.remove_drone(99)


# ── connection.py ─────────────────────────────────────────────────────


def test_connects() -> None:
    """T1.7 — connects returns True only for its two endpoints."""
    conn = Connection("alpha", "beta")
    assert conn.connects("alpha")
    assert conn.connects("beta")
    assert not conn.connects("gamma")


def test_other_end() -> None:
    """T1.8 — other_end returns the opposite zone."""
    conn = Connection("alpha", "beta")
    assert conn.other_end("alpha") == "beta"
    assert conn.other_end("beta") == "alpha"
    with pytest.raises(ValueError):
        conn.other_end("unknown")


def test_occupy_and_release_cycle() -> None:
    """T1.9 — full occupy/release cycle respects capacity."""
    conn = Connection("a", "b", max_link_capacity=1)
    assert conn.has_capacity()
    conn.occupy(1)
    assert not conn.has_capacity()
    with pytest.raises(ValueError):
        conn.occupy(2)
    conn.release(1)
    assert conn.has_capacity()
    with pytest.raises(KeyError):
        conn.release(99)


def test_connection_equality_and_hash() -> None:
    """T1.10 — a-b equals b-a; set deduplicates correctly."""
    ab = Connection("a", "b")
    ba = Connection("b", "a")
    assert ab == ba
    assert hash(ab) == hash(ba)
    assert len({ab, ba}) == 1


# ── drone.py ──────────────────────────────────────────────────────────


def test_next_zone_empty_and_end_of_path() -> None:
    """T1.11 — next_zone returns None if path is empty or done."""
    start = Zone("s", 0, 0, is_start=True)
    drone = Drone(1, start)
    assert drone.next_zone() is None

    end = Zone("e", 1, 0, is_end=True)
    drone.planned_path = [start, end]
    drone.path_index = 1  # pointing at last zone — nothing after
    assert drone.next_zone() is None


def test_transit_one_tick() -> None:
    """T1.12 — start_transit then one tick_transit signals done."""
    start = Zone("s", 0, 0, is_start=True)
    drone = Drone(1, start)
    conn = Connection("s", "mid")
    drone.start_transit(conn)
    assert drone.status == DroneStatus.IN_TRANSIT
    assert drone.turns_remaining_transit == 1
    assert drone.tick_transit() is True
    assert drone.turns_remaining_transit == 0


def test_is_arrived() -> None:
    """T1.13 — is_arrived reflects DroneStatus.ARRIVED."""
    start = Zone("s", 0, 0, is_start=True)
    drone = Drone(1, start)
    assert not drone.is_arrived()
    drone.status = DroneStatus.ARRIVED
    assert drone.is_arrived()


# ── graph.py ──────────────────────────────────────────────────────────


def test_add_and_get_zone() -> None:
    """T1.14 — add_zone/get_zone round-trip; errors on duplicate/miss."""
    g = Graph()
    z = Zone("hub1", 0, 0)
    g.add_zone(z)
    assert g.get_zone("hub1") is z
    with pytest.raises(KeyError):
        g.get_zone("nowhere")
    with pytest.raises(ValueError):
        g.add_zone(Zone("hub1", 1, 1))


def test_add_connection_rejects_duplicates() -> None:
    """T1.15 — add_connection raises ValueError for a-b and b-a."""
    g = Graph()
    g.add_zone(Zone("a", 0, 0))
    g.add_zone(Zone("b", 1, 0))
    g.add_connection(Connection("a", "b"))
    with pytest.raises(ValueError):
        g.add_connection(Connection("a", "b"))
    with pytest.raises(ValueError):
        g.add_connection(Connection("b", "a"))


def test_get_neighbors() -> None:
    """T1.16 — get_neighbors returns directly connected zones."""
    g = Graph()
    for name, x in [("a", 0), ("b", 1), ("c", 2)]:
        g.add_zone(Zone(name, x, 0))
    g.add_connection(Connection("a", "b"))
    g.add_connection(Connection("a", "c"))
    neighbor_names = {z.name for z in g.get_neighbors("a")}
    assert neighbor_names == {"b", "c"}
    assert g.get_neighbors("b") == [g.get_zone("a")]


def test_get_connection_both_directions() -> None:
    """T1.17 — get_connection works regardless of argument order."""
    g = Graph()
    g.add_zone(Zone("x", 0, 0))
    g.add_zone(Zone("y", 1, 0))
    conn = Connection("x", "y")
    g.add_connection(conn)
    assert g.get_connection("x", "y") is conn
    assert g.get_connection("y", "x") is conn
    assert g.get_connection("x", "z") is None


def test_validate_missing_hubs() -> None:
    """T1.18 — validate raises if start or end hub is absent."""
    g = Graph()
    with pytest.raises(ValueError):
        g.validate()
    g.add_zone(Zone("s", 0, 0, is_start=True))
    with pytest.raises(ValueError):
        g.validate()
    g.add_zone(Zone("e", 1, 0, is_end=True))
    g.validate()  # both present — must not raise
