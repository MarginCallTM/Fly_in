"""Graph class - the zone/connection graph for drone routing."""

from __future__ import annotations
from typing import Optional

from zone import Zone
from connection import Connection


class Graph:
    """Undirected graph of zones connected by bidirectional links.

    Zones are nodes; connections are edges. Built incrementally:
    add all zones first, then connections. Call validate() once
    the graph is fully assembled.

    Attributions:
        Zones: Zone objects indexed by name for O(1) lookup.
        connections: All edges in the graph/
        start_hub: The unique arrival zone (set by add_zone).
    """

    def __init__(self) -> None:
        """Initialize an empty graph """
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone node to the graph.

        Args:
            zone: The zone to add.

        Raises:
            ValueError: If the name is already taken, or if a
            second start/end hub is added.
        """
        if zone.name in self.zones:
            raise ValueError(
                f"Zone '{zone.name}' already exists in the graph"
            )
        if zone.is_start and self.start_hub is not None:
            raise ValueError("A start_hub is already defined")
        if zone.is_end and self.end_hub is not None:
            raise ValueError("An end_hub is already defined")
        self.zones[zone.name] = zone
        if zone.is_start:
            self.start_hub = zone
        if zone.is_end:
            self.end_hub = zone

    def add_connection(self, conn: Connection) -> None:
        """Add an edge between two zones.

        Args:
            conn: The connection to add.

        Raises:
            ValueError: If an endpoint zone is unknow, or if an
                equivalent connection (a-b or b-a) already exits.
        """
        for zone_name in (conn.zone_a, conn.zone_b):
            if zone_name not in self.zones:
                raise ValueError(
                    f"Zone '{zone_name}' not found in graph"
                )
        # Connection.__eq__ uses frozenset -> catches a-b and b-a
        if conn in self.connections:
            raise ValueError(
                f"Connection {conn.zone_a}-{conn.zone_b} "
                f"already exists (or its reverse)"
            )
        self.connections.append(conn)

    def get_zone(self, name: str) -> Zone:
        """Return the zone with the given name.

        Args:
            name: Zone identifier.

        Raises:
            KeyError: If no zone with that name exists.
        """
        if name not in self.zones:
            raise KeyError(f"Zone '{name}' not found in graph")
        return self.zones[name]

    def get_neighbors(self, zone_name: str) -> list[Zone]:
        """Return all zones directly connected to a given zone.

        This is the core method used by the pathfinding router.

        Args:
            zone_name: Name of the source zone.

        Returns: List of neighboring Zone objects (empty if none).
        """
        neighbors: list[Zone] = []
        for conn in self.connections:
            if conn.connects(zone_name):
                neighbors_name = conn.other_end(zone_name)
                neighbors.append(self.zones[neighbors_name])
        return neighbors

    def get_connection(
            self, z1: str, z2: str
    ) -> Optional[Connection]:
        """Find the connection between two zones (order-independent)

        Args:
            z1: Name of the endpoint.
            z2: Name of the other endpoint.

        Returns: The connection object, or None if not found.
        """
        for conn in self.connections:
            if conn.connects(z1) and conn.connects(z2):
                return conn
        return None

    def validate(self) -> None:
        """Check that the graph is structurally complete.

        Raises:
            ValueError: If start_hub or end_hub is missing.
        """

        if self.start_hub is None:
            raise ValueError("Graph has no start_hub defined")
        if self.end_hub is None:
            raise ValueError("Graph has no end_hub defined")
