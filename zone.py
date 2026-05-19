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


def occupancy(self) -> int:
