"""Router - shortest path finder over the zone graph.

Implements Dijkstra's algorithm from scratch using heapq as the
priority queue. The router only finds paths; it does NOT reserve
zone or connection capacity - that is the simulator's job. Two
drones can therefore be assigned the same path, and the simulator
later resolves the resulting conflicts turn by turn.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import heapq
from typing import Optional

from zone import Zone
from graph import Graph


@dataclass
class Path:
    """An ordered sequence of zones with its total movement cost.

    Attributes:
        zones: Zones traversed, in order, from start to end
            (both included).
        cost: Total cost in turns. Equals the sum of
            movement_cost() of every zone except the first one
            (start is the spawn point, not entered).
    """

    zones: list[Zone] = field(default_factory=list)
    cost: int = 0

    def __len__(self) -> int:
        """Return the number of zones in the path."""
        return len(self.zones)


class Router:
    """Compute shortest paths on a validated drone zone graph.

    Movement costs follow the destination zone's zone_type:
    normal/priority = 1, restricted = 2. BLOCKED zones are
    never entered, so any path crossing one is invalid by
    construction (Dijkstra skips them during expansion).

    Args:
        graph: A validated Graph (start_hub and end_hub set).
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize the router with a graph."""
        self.graph = graph

    def shortest_path(
            self, start_name: str, end_name: str,
    ) -> Optional[Path]:
        """Find the shortest path between two zones.

        Args:
            start_name: Name of the source zone.
            end_name: Name of the destination zone.

        Returns: The shortest Path (zones + cost) found, or None
            if no path exists (graph disconnected, target blocked,
            etc.).
        """
        # heap entries: (cost_so_far, zone_name)
        # heapq compares tuples lexicographically: equal costs
        # fall back to comparing names alphabetically. That gives
        # deterministic ordering without needing Zone __lt__.
        heap: list[tuple[int, str]] = [(0, start_name)]
        costs: dict[str, int] = {start_name: 0}
        predecessors: dict[str, Optional[str]] = {start_name: None}

        while heap:
            current_cost, name = heapq.heappop(heap)
            # Stale entry: a better cost has already been
            # recorded for this zone since we pushed it.
            if current_cost > costs[name]:
                continue
            if name == end_name:
                return self._build_path(
                    name, predecessors, current_cost
                )
            self._relax_neighbors(
                name, current_cost, heap, costs, predecessors
            )
        return None

    def _relax_neighbors(
            self,
            name: str,
            current_cost: int,
            heap: list[tuple[int, str]],
            costs: dict[str, int],
            predecessors: dict[str, Optional[str]],
    ) -> None:
        """Update neighbor costs if a shorter path is found.

        Helper extracted from shortest_path to keep the main loop
        under 25 lines. Modifies heap, costs and predecessors
        in place.
        """
        for neighbor in self.graph.get_neighbors(name):
            if not neighbor.is_accessible():
                continue  # BLOCKED zone, never enter it.
            new_cost = current_cost + neighbor.movement_cost()
            existing = costs.get(neighbor.name)
            if existing is None or new_cost < existing:
                costs[neighbor.name] = new_cost
                predecessors[neighbor.name] = name
                heapq.heappush(heap, (new_cost, neighbor.name))

    def _build_path(
            self,
            end_name: str,
            predecessors: dict[str, Optional[str]],
            cost: int,
    ) -> Path:
        """Walk the predecessor chain to rebuild the full path.

        Args:
            end_name: The destination reached by Dijkstra.
            predecessors: Map produced during the search.
            cost: Total path cost computed by Dijkstra.

        Returns: A Path object with zones in order start->end.
        """
        zones: list[Zone] = []
        cursor: Optional[str] = end_name
        while cursor is not None:
            zones.append(self.graph.get_zone(cursor))
            cursor = predecessors[cursor]
        zones.reverse()
        return Path(zones=zones, cost=cost)
