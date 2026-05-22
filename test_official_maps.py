"""Smoke tests on the 10 official Fly-in maps.

  Each shipped map is loaded through MapParser and checked for
  basic invariants: it parses without exception, nb_drones matches
  the documented value, and the graph has the required hubs.

  These tests complement the unit tests in test_session_b.py and
  test_session_c.py by validating the parser on real-world content
  rather than synthetic micro-maps.

  Run with:    pytest test_official_maps.py -v
"""

from __future__ import annotations

import pytest

from map_parser import MapParser

# (file path, expected nb_drones) — values from the subject PDF.
OFFICIAL_MAPS = [
    ("maps/easy/01_linear_path.txt", 2),
    ("maps/easy/02_simple_fork.txt", 4),
    ("maps/easy/03_basic_capacity.txt", 4),
    ("maps/medium/01_dead_end_trap.txt", 5),
    ("maps/medium/02_circular_loop.txt", 6),
    ("maps/medium/03_priority_puzzle.txt", 5),
    ("maps/hard/01_maze_nightmare.txt", 8),
    ("maps/hard/02_capacity_hell.txt", 12),
    ("maps/hard/03_ultimate_challenge.txt", 15),
    ("maps/challenger/01_the_impossible_dream.txt", 25),
]


@pytest.mark.parametrize(
    "map_path, expected_drones", OFFICIAL_MAPS
)
def test_official_map_parses(
    map_path: str, expected_drones: int
) -> None:
    """An official map must parse cleanly and match expectations.

    Validates that:
        - MapParser.parse() does not raise on the real map file
        - the returned nb_drones matches the value documented
        in the subject PDF
        - the graph has a start_hub and an end_hub registered
        - the graph contains at least 2 zones and 1 connection
        (sanity check: a usable map cannot be empty)
    """
    graph, nb_drones = MapParser().parse(map_path)
    assert nb_drones == expected_drones
    assert graph.start_hub is not None
    assert graph.end_hub is not None
    assert len(graph.zones) >= 2
    assert len(graph.connections) >= 1


def test_space_separated_metadata_correctly_parsed() -> None:
    """Regression test: space-separated metadata is split correctly.

    The official maps use spaces (not commas) between metadata
    entries inside [...]. _parse_metadata must split on whitespace
    so that '[color=yellow max_drones=2]' becomes two distinct
    entries, not a single color='yellow max_drones=2' string.

    This test guards against the regression we hit when first
    leading the official medium and hard maps.
    """
    graph, _ = MapParser().parse(
        "maps/easy/02_simple_fork.txt"
    )
    # 'junction' is declared as: [color=yellow max_drones=2]
    junction = graph.get_zone("junction")
    assert junction.color == "yellow"
    assert junction.max_drones == 2
    # 'goal' is declared as: [color=red max_drones=3]
    goal = graph.get_zone("goal")
    assert goal.color == "red"
    assert goal.max_drones == 3
