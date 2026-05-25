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

from zone import Zone, ZoneType
from connection import Connection
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
            self,
            start_name: str,
            end_name: str,
            blocked_zones: Optional[set[str]] = None,
            blocked_edges: Optional[set[Connection]] = None,
    ) -> Optional[Path]:
        """Find the shortest path between two zones.

        Args:
            start_name: Name of the source zone.
            end_name: Name of the destination zone.
            blocked_zones: Intermediate zone to skip (saturated).
            blocked_edges: COnnections to skip (saturated)

        Returns: The shortest Path (zones + cost) found, or None
            if no path exists (graph disconnected, target blocked,
            etc.). On ties, the path with more PRIORITY zones wins.
        """
        # None -> empty set: callers that ignore capacities keep
        # the original behaviour untouched
        blocked_zones = blocked_zones or set()
        blocked_edges = blocked_edges or set()
        heap: list[tuple[int, int, str]] = [(0, 0, start_name)]
        best: dict[str, tuple[int, int]] = {start_name: (0, 0)}
        predecessors: dict[str, Optional[str]] = {start_name: None}

        while heap:
            cost, penalty, name = heapq.heappop(heap)
            # Stale entry: a better (cost, penalty) was found.
            if (cost, penalty) > best[name]:
                continue
            if name == end_name:
                return self._build_path(
                    name, predecessors, cost
                )
            self._relax_neighbors(
                name, cost, penalty, heap, best, predecessors,
                blocked_zones, blocked_edges,
            )
        return None

    def _relax_neighbors(
            self,
            name: str,
            cost: int,
            penalty: int,
            heap: list[tuple[int, int, str]],
            best: dict[str, tuple[int, int]],
            predecessors: dict[str, Optional[str]],
            blocked_zones: set[str],
            blocked_edges: set[Connection],
    ) -> None:
        """Update neighbor (cost, penalty) if a better path found.

        Helper extracted from shortest_path. Modifies heap, best
        and predecessors in place. A neighbor is relaxed if the
        new (cost, penalty) tuple is lexicographically smaller
        than the one currently stored.
        """
        for neighbor in self.graph.get_neighbors(name):
            if not neighbor.is_accessible():
                continue  # BLOCKED zone, never enter it.
            if neighbor.name in blocked_zones:
                continue
            if blocked_edges:
                conn = self.graph.get_connection(
                    name, neighbor.name
                )
                if conn is not None and conn in blocked_edges:
                    continue  # link capacity already used up.
            new_cost = cost + neighbor.movement_cost()
            is_priority = neighbor.zone_type == ZoneType.PRIORITY
            new_penalty = penalty + (0 if is_priority else 1)
            new_key = (new_cost, new_penalty)
            existing = best.get(neighbor.name)
            if existing is None or new_key < existing:
                best[neighbor.name] = new_key
                predecessors[neighbor.name] = name
                heapq.heappush(
                    heap, (new_cost, new_penalty, neighbor.name)
                )

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

    def path_throughput(self, path: Path) -> int:
        """Compute the max drones-per-turn capacity of a path.

        The throughput is the smallest capacity along the way:
            - zone max_drones for intermediate zones (start and
              end are unlimited and skipped),
            - connection max_link_capacity for every consecutive
              pair of zones in the path.

        Args:
            path: A Path returned by shortest_path.

        Returns: The bottleneck capacity (>= 1 for any path
            returned by Dijkstra, since BLOCKED is skipped).
            Returns 0 for a degenerate path of length < 2.
        """
        if len(path) < 2:
            return 0
        capacities: list[int] = []
        for zone in path.zones:
            if not zone.is_start and not zone.is_end:
                capacities.append(zone.max_drones)
        for i in range(len(path.zones) - 1):
            conn = self.graph.get_connection(
                path.zones[i].name, path.zones[i + 1].name
            )
            if conn is not None:
                capacities.append(conn.max_link_capacity)
        return min(capacities) if capacities else 1

    def find_disjoint_paths(
        self, max_paths: Optional[int] = None,
    ) -> list[Path]:
        """Find several routes by greedy residual-capacity search

        Repeatedly takes the shortest path, then 'consumes' one
        capacity unit on every intermediate zone and connection
        it crosses. A zone/connection drops out once satured.
        Stops when no path remains, or after max_paths routes.

        Args:
            max_paaths: Optional cap on the number of routes (
            never need more parallel routes than drones)

        Returns: Routes in the order they were carved out (shortest
        first). May repeat a route when its capacity allows
        several drones in parallel.
        """
        if self.graph.start_hub is None or self.graph.end_hub is None:
            return []
        start_name = self.graph.start_hub.name
        end_name = self.graph.end_hub.name
        zone_load: dict[str, int] = {}
        edge_load: dict[Connection, int] = {}
        paths: list[Path] = []
        while max_paths is None or len(paths) < max_paths:
            path = self.shortest_path(
                start_name, end_name,
                self._saturated_zones(zone_load),
                self._saturated_edges(edge_load),
            )
            if path is None:
                break
            paths.append(path)
            self._consume(path, zone_load, edge_load)
        return paths

    def _saturated_zones(
            self, zone_load: dict[str, int],
    ) -> set[str]:
        """Return intermediate zone whose capacity is used up"""
        saturated: set[str] = set()
        for name, load in zone_load.items():
            zone = self.graph.get_zone(name)
            if zone.is_start or zone.is_end:
                continue
            if load >= zone.max_drones:
                saturated.add(name)
        return saturated

    def _saturated_edges(
            self, edge_load: dict[Connection, int]
    ) -> set[Connection]:
        """Return connections whose link capacity is used up"""
        return {
            conn for conn, load in edge_load.items()
            if load >= conn.max_link_capacity
        }

    def _consume(
            self,
            path: Path,
            zone_load: dict[str, int],
            edge_load: dict[Connection, int],
    ) -> None:
        """Charge one route's resources onto the load counters"""
        for zone in path.zones[1:-1]:  # skip start and end hubs
            zone_load[zone.name] = zone_load.get(zone.name, 0) + 1
        for i in range(len(path.zones) - 1):
            conn = self.graph.get_connection(
                path.zones[i].name, path.zones[i + 1].name
            )
            if conn is not None:
                edge_load[conn] = edge_load.get(conn, 0) + 1


class NoSolutionError(Exception):
    """Raised when no route connects the start hub to the end hub."""


class PathPlanner:
    """Distribute drones over the available routes (lem-in style)

    Builds on Router.find_disjoint_paths, which eturns a set of
    capacity-respecting lanes (a route may appear severak times,
    once per parallel unit of capacity). Each lane carries drones
    one at a time, so spreading the well is what keeps the overall
    turn count low.

    Args:
        graph: A validated Graph (start_hub and end_hub set)
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize the plannner with a graph and its router"""
        self.graph = graph
        self.router = Router(graph)

    def find_all_useful_paths(self, nb_drones: int) -> list[Path]:
        """Return the lanes drones can travel on.

        Never returns nore lanes than drones: extra parallel
        capacity beyond the fleet size would stay unused.

        Args:
            nb_drones: Number of drones to route.

        Returns: Lanes (shortest first), possibly with
        repeats standing for a route's parrallel capacity.
        """
        return self.router.find_disjoint_paths(max_paths=nb_drones)

    def assign_drones_to_paths(
            self, nb_drones: int, paths: list[Path]
    ) -> list[Path]:
        """Assign each drone to the lane that delivers it soonest

        Greedy rule: a lane already carrying k drones delivers its
        next drone at turn k + lane.cost (one drone enters per turn).
        We place each drone on the lane with the smallest such arrival
        turn, filling short lanes first and spilling onto longer ones
        only when worthwhile.

        Args:
            nb_drones: Number of drones to place.
            paths: Lanes from find_all_useful_paths.

        Returns: A list of lenght nb_drones; element i
        is the lane assigned to drone i.

        Raises:
            NoSolutionError: If no lane exists while drone remain.
        """
        if nb_drones > 0 and not paths:
            raise NoSolutionError(
                "No route connects the start hub to the end hub"
            )
        counts: list[int] = [0] * len(paths)
        assignment: list[Path] = []
        for _ in range(nb_drones):
            chosen = self._earliest_lane(paths, counts)
            assignment.append(paths[chosen])
            counts[chosen] += 1
        return assignment

    def _earliest_lane(
            self, paths: list[Path], counts: list[int]
    ) -> int:
        """Index of the lane delivering its next drone soonest. """
        best_index = 0
        best_arrival = counts[0] + paths[0].cost
        for i in range(1, len(paths)):
            arrival = counts[i] + paths[i].cost
            if arrival < best_arrival:
                best_arrival = arrival
                best_index = i
        return best_index

    def plan(self, nb_drones: int) -> list[Path]:
        """One-shot: find lanes, then assign drones to them.

        Convenience entry point for the simulator (Phase 5).

        Args:
            nb_drones: Number of drones to route.

        Returns: A list of length nb_drones; element i is
            the lane assigned to drone i.
        """
        paths = self.find_all_useful_paths(nb_drones)
        return self.assign_drones_to_paths(nb_drones, paths)
