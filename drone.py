"""Drone class - mobile unit traversing the zone graph. """

from __future__ import annotations
from enum import Enum
from typing import Optional

from zone import Zone
from connection import Connection


class DroneStatus(Enum):
    """Lifecycle states of a drone during the simulation. """

    AT_START = "at_start"  # Still on the start hub
    MOVING = "moving"  # In a zone, ready to move next turn
    IN_TRANSIT = "in_transit"  # Reached the end hub
    ARRIVED = "arrived"     # Reached the end hub


class Drone:
    """A drone navigating from the start_hub to end_hub.

    Carries its panned path (computed by the router) and its
    current movement state. Movement decisions and conflict
    resolution are handled by the Simulator - This class only
    holds state and exposes small state-mutating helpers.

    Args:
        drone_id: Unique integer identifier.
        start_zone: The start_hub zone where the drone spawns.
    """

    def __init__(
            self,
            drone_id: int,
            start_zone: Zone,
    ) -> None:
        """Initialize a Drone at the start hub. """
        self.id = drone_id
        self.current_zone: Zone = start_zone
        # Path is assigned by the router before the simulation
        # starts. Index 0 = start_zone, last = end_zone.
        self.planned_path: list[Zone] = []
        self.path_index: int = 0
        self.status: DroneStatus = DroneStatus.AT_START
        # Only set while status == IN_TRANSIT (restricted moves)
        self.in_transit_connection: Optional[Connection] = None
        self.turns_remaining_transit: int = 0

    def next_zone(self) -> Optional[Zone]:
        """Return the next zone in the planned path.

        Returns: The zone right after current position in the
        planned path, or None if the drone has reached the
        end of its path.
        """
        next_index = self.path_index + 1
        if next_index >= len(self.planned_path):
            return None
        return self.planned_path[next_index]

    def is_arrived(self) -> bool:
        """Return True if the drone reached the end hub."""
        return self.status == DroneStatus.ARRIVED

    def start_transit(self, connection: Connection) -> None:
        """"Begin a multi-turn move over a connection.

        Called when a drone enters a connection leading to a
        restricted zone. The drone will spend one full turn on
        the link before arriving at the destination.

        Args:
            connection: The connection being entered.
        """
        self.status = DroneStatus.IN_TRANSIT
