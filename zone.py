from __future__ import annotations
from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """Types of zones defining movement cost and accessibility"""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """A node in the drone routing graph

    Args:
          name: Unique identifier for this zone.
          x: X coordinate (integer).
          y: Y coordinate (integer).
          zone_type: Movement rules for this zone.
          color: Optional display color (any single-word string).
          max_drones: Maximum drones allowed simultaneously.
          is_start: True if this is the start hub.
          is_end: True if this is the end hub.

    """

    def __init__(
            self,
            name: str,
            x: int,
            y: int,
            zone_type: ZoneType = ZoneType.NORMAL,
            color: Optional[str] = None,
            max_drones: int = 1,
            is_start: bool = False,
            is_end: bool = False,
    ) -> None:
        """Initialize a Zone. """
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.is_start = is_start
        self.is_end = is_end
        # Set of drone IDs currently occupying this zone
        self.current_drones: set[int] = set()

    def movement_cost(self) -> int:
        """Return the turn cost to enter this zone

        Returns: 2 for restricted zones, 1 for all others.
        """
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def is_accessible(self) -> bool:
        """Return False if this zone is blocked"""
        return self.zone_type != ZoneType.BLOCKED

    def occupancy(self) -> int:
        """Return the number of drones currently in this zone"""
        return len(self.current_drones)

    def is_full(self) -> bool:
        """Check if this zone has reached its capacity.

        Start and end zones have unlimited capacity
        so they are never considered full.

        returns: True if the zone cannot accept more drones.
        """
        if self.is_start or self.is_end:
            return False
        return self.occupancy() >= self.max_drones

    def can_accept(self) -> bool:
        """Check if a new drone can enter this zone.

        A drone can enter if the zone is not blocked AND not full.

        Returns: True if a drone is allowed to enter.
        """
        return self.is_accessible() and not self.is_full()

    def add_drone(self, drone_id: int) -> None:
        """Add a drone to this zone.

        Args:
            drone_id: Unique identifier of the drone to add.

        Raises:
            ValueError: If the zone cannot accept the drone
                (Blocked or full)
        """
        if not self.can_accept():
            raise ValueError(
                f"Zone '{self.name}' cannot accept the drone {drone_id}"
            )
        self.current_drones.add(drone_id)

    def remove_drone(self, drone_id: int) -> None:
        """Remove a drone from this zone.

        Args:
            drone_id: Unique identifier of the drone to remove.
        Raises:
            KeyError: If the drone is not currently in this zone.
        """

        if drone_id not in self.current_drones:
            raise KeyError(
                f"Drone {drone_id} is not in zone '{self.name}'"
            )
        self.current_drones.remove(drone_id)
