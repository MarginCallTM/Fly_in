"""Connection class - bidirectional edge between two zones."""

from __future__ import annotations


class Connection:
    """An edge in the drone routing graph.

    Bidirectional connection between two zones. Tracks drones
    currently in transit (used for multi-turn moves toward
    restricted zones) and enforces capacity limits.

    Args:
        zone_a: Name of the first enpoint zone.
        zone_b: Name of the second enpoint zone.
        max_link_capacity: Max drone simultaneously crossing.
    """

    def __init__(
            self,
            zone_a: str,
            zone_b: str,
            max_link_capacity: int = 1,
    ) -> None:
        """Initialize a Connection."""
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        # Drones currently sitting on the link (multi-turn transit)
        self.drones_in_transit: set[int] = set()

    def connects(self, zone_name: str) -> bool:
        """Check if this connection touches a given zone>

        Args:
            zone_name: Name of the zone to test.

            Returns: True if the zone is one of the endpoints.
        """
        return zone_name in (self.zone_a, self.zone_b)

    def other_end(self, zone_name: str) -> str:
        """Return the opposite endpoint of a given zone.

        Args:
            zone_name: Name of one endpoint of this connection.

        Returns: Name of the other endpoint.

        Raises:
            ValueError: If zone)name is not one of the endpoints
        """

        if zone_name == self.zone_a:
            return self.zone_b
        if zone_name == self.zone_b:
            return self.zone_a
        raise ValueError(
            f"Zone '{zone_name} is not part of the connection"
        )

    def has_capacity(self) -> bool:
        """Return True if at least one more drone can traverse."""
        return len(self.drones_in_transit) < self.max_link_capacity

    def occupy(self, drone_id: int) -> None:
        """Add a drone to the in-transit set.

        Args:
            drone_id: Unique identifier of the drone.

        Raises:
            ValueError: If the connection has no remaining capacity
        """
        if not self.has_capacity():
            raise ValueError(
                f"Connection {self.zone_a}-{self.zone_b} is full"
            )
        self.drones_in_transit.add(drone_id)

    def __eq__(self, other: object) -> bool:
        """Two connections are equal if endpoints match (any order)"""
        if not isinstance(other, Connection):
            return NotImplemented
        return (
            frozenset({self.zone_a, self.zone_b})
            == frozenset({other.zone_a, other.zone_b})
        )

    def __hash__(self) -> int:
        """Hash based on the unordered pair of endpoints."""
        return hash(frozenset({self.zone_a, self.zone_b}))

    def __repr__(self) -> str:
        """Compact human-readable representation."""
        return (
            f"Connection({self.zone_a}-{self.zone_b}, "
            f"cap={self.max_link_capacity})"
        )
