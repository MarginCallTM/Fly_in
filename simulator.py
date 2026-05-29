from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from zone import Zone, ZoneType
from graph import Graph
from drone import Drone, DroneStatus
from router import PathPlanner
from connection import Connection


@dataclass
class Movement:
    """One drone's displayed move during a single simulation turn.

    Stores just enough to render the output line from the subject.
    The destination is a zone name for a normal move (or an arrival),
    or a connection label while the drone is still in flight toward
    a restricted zone.

    Attributes:
            drone_id: Unique identifier of the moving drone.
            destination: Zone name, or connection label if in transit.
            is_transit: True while crossing a connection (multi-turn move)
            let's the renderer style it differently
    """
    drone_id: int
    destination: str
    is_transit: bool = False

    def __str__(self) -> str:
        """Return the subject's output token, e.g ''D1-roof1''"""
        return f"D{self.drone_id}-{self.destination}"


class Simulator:
    """Turn-by-turn engine moving all drones from start to end.

    Builds a fleet of drones at the start hub, assigns each a lane
    via the pathPlanner, then repeatedly plays turns until every
    drone has reached the end hub. Capacity bookkeeping live in
    the Zone/Connection models; this class only decides who moves.

    Args:
        graph: A validated Graph (start_hub and end_hub set)
        nb_drones: Number of drones to route.
    """

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        """Initialize the simulator (drones spawned later, in run)"""
        self.graph = graph
        self.nb_drones = nb_drones
        self.planner = PathPlanner(graph)
        self.drones: list[Drone] = []
        self.history: list[list[Movement]] = []
        self.snapshots: list[dict[int, str]] = []
        # Generous bound to break a runway/deadlocked simulation
        self.max_turns = 1000

    def _setup_drones(self) -> None:
        """Spawn all drones at the start hub and assign their lanes.

        Drone i (1-indexed for the D<ID> ouput) gets the lane
        at index i-1 returned by PathPlanner.plan. The lane's
        zone list becomes the drone's planned path.

        Raises:
            ValueError: If the graph has no start hub.
            NoSolutionError: If no route reaches the end hub.
        """
        start = self.graph.start_hub
        if start is None:
            raise ValueError("Graph has no start_hub defined")
        lanes = self.planner.plan(self.nb_drones)
        for drone_id in range(1, self.nb_drones + 1):
            drone = Drone(drone_id, start)
            drone.planned_path = lanes[drone_id - 1].zones
            self.drones.append(drone)
            start.add_drone(drone_id)

    def _all_arrived(self) -> bool:
        """Returns True once every drone reached the end hub"""
        return all(drone.is_arrived() for drone in self.drones)

    def run(self) -> int:
        """Play the simulation until all drones arrive.

        Returns:
            The total number of turns played.

        Raises:
            RuntimeError: If max_turns is exceeded
            (deadlock or unreachable end hub)
        """
        self._setup_drones()
        self.snapshots.append(self._snapshot())  # turn 0 : initial frame
        turn = 0
        while not self._all_arrived():
            if turn >= self.max_turns:
                raise RuntimeError(
                    "Simulation exceeded max_turns "
                    f"({self.max_turns}); possible deadlock"
                )
            self.history.append(self._step())
            self.snapshots.append(self._snapshot())
            turn += 1
        return turn

    def _step(self) -> list[Movement]:
        """Play one turn: move every drone that legally can.

        Drones are handled most-advanced-first (highest
        path_index), so a slot freed by a leaving drone is
        reusable the same turn - that is the simultaneous
        realase of VII.3

        Returns:
            Movements done this turn (waiting drone are omitted.)
        """
        incoming = self._count_incoming()
        link_loads = self._link_loads_at_start()
        moves: list[Movement] = []
        for drone in self._active_drones_ordered():
            move = self._move_one(drone, incoming, link_loads)
            if move is not None:
                moves.append(move)
        return moves

    def _count_incoming(self) -> dict[str, int]:
        """Count drones in flight toward each restricted zone.

        A drone on a connection is not yet in its target's
        occupancy, so we track these pending arrivals to avoid
        overbooking the restricted zone at T+1

        Returns:
            Map zone name -> number of inbound drones in transit.
        """
        incoming: dict[str, int] = {}
        for drone in self.drones:
            if drone.status != DroneStatus.IN_TRANSIT:
                continue
            target = drone.next_zone()
            if target is not None:
                incoming[target.name] = incoming.get(target.name, 0) + 1
        return incoming

    def _link_loads_at_start(self) -> dict[Connection, int]:
        """Per-turn count of drones using each connection.

          Seeded with drones still in transit from earlier turns,
          so a single-turn normal crossing shares the same link
          capacity budget as a multi-turn restricted transit.

          Returns:
              Map connection -> drones already using it this turn.
        """
        return {
            conn: len(conn.drones_in_transit)
            for conn in self.graph.connections
        }

    def _active_drones_ordered(self) -> list[Drone]:
        """Return not-yet-arrived drones, most advanced first"""
        active = [d for d in self.drones if not d.is_arrived()]
        return sorted(
            active, key=lambda d: d.path_index, reverse=True
        )

    def _move_one(
            self, drone: Drone,
            incoming: dict[str, int],
            link_loads: dict[Connection, int],
    ) -> Optional[Movement]:
        """Resolve one drone's action, dispatching on its state.

        Returns:
            The movement performed, or None if the drone waits
        """
        if drone.status == DroneStatus.IN_TRANSIT:
            return self._finish_transit(drone, incoming)
        target = drone.next_zone()
        if target is None:
            return None
        if target.zone_type == ZoneType.RESTRICTED:
            return self._try_enter_restricted(drone,
                                              target, incoming, link_loads)
        return self._try_normal_move(drone, target, link_loads)

    def _finish_transit(
            self, drone: Drone, incoming: dict[str, int]
    ) -> Optional[Movement]:
        """Land a drone that was crossing a connection.

        Transit always completes this turn (one tick),
        so the drone leaves the link and enters the
        restricted zone whose slot it reserved at
        departure.

        Returns:
            THe arrival Movement (D<ID>-<zone>)
        """
        drone.tick_transit()
        conn = drone.in_transit_connection
        target = drone.next_zone()
        if conn is None or target is None:
            return None
        conn.release(drone.id)
        target.add_drone(drone.id)
        incoming[target.name] -= 1
        self._advance(drone, target)
        return Movement(drone.id, target.name)

    def _try_enter_restricted(
            self, drone: Drone, target: Zone,
            incoming: dict[str, int],
            link_loads: dict[Connection, int],
    ) -> Optional[Movement]:
        """Start the 2-turn move onto the link toward a restricted.

        Engages only if the link is below max_link_capacity this
        turn AND the restricted zone will have a slot on arrival
        (occupancy + inbound < cap): a drone may never wait on the
        link.

        Returns:
            The transit Movement (D<ID>-<connection>), or None
        """
        conn = self.graph.get_connection(
            drone.current_zone.name, target.name
        )
        if conn is None:
            return None
        if link_loads.get(conn, 0) >= conn.max_link_capacity:
            return None
        reserved = target.occupancy() + incoming.get(target.name, 0)
        if reserved >= target.max_drones:
            return None
        label = f"{drone.current_zone.name}-{target.name}"
        drone.current_zone.remove_drone(drone.id)
        conn.occupy(drone.id)
        drone.start_transit(conn)
        incoming[target.name] = incoming.get(target.name, 0) + 1
        link_loads[conn] = link_loads.get(conn, 0) + 1
        return Movement(drone.id, label, is_transit=True)

    def _try_normal_move(
            self, drone: Drone, target: Zone,
            link_loads: dict[Connection, int],
    ) -> Optional[Movement]:
        """Move a drone one step into a normal/priority zone.

        Succeeds only if the destination can accept it now;
        with the most-advanced-first ordering, slot freed
        this turn already show up in can_accept().

        Returns:
            The Movement (D<ID>-<Zone>), Or None if it waits
        """
        if not target.can_accept():
            return None
        conn = self.graph.get_connection(
            drone.current_zone.name, target.name
        )
        if conn is not None:
            if link_loads.get(conn, 0) >= conn.max_link_capacity:
                return None
        drone.current_zone.remove_drone(drone.id)
        target.add_drone(drone.id)
        if conn is not None:
            link_loads[conn] = link_loads.get(conn, 0) + 1
        self._advance(drone, target)
        return Movement(drone.id, target.name)

    def _advance(self, drone: Drone, target: Zone) -> None:
        """Update a drone's bookkeeping after it entered a zone."""
        drone.current_zone = target
        drone.path_index += 1
        if target.is_end:
            drone.status = DroneStatus.ARRIVED
        else:
            drone.status = DroneStatus.MOVING

    def _snapshot(self) -> dict[int, str]:
        """Return every drone's current position as a zone/conn name"""
        state: dict[int, str] = {}
        for drone in self.drones:
            conn = drone.in_transit_connection
            if drone.status == DroneStatus.IN_TRANSIT and conn:
                state[drone.id] = f"{conn.zone_a}-{conn.zone_b}"
            else:
                state[drone.id] = drone.current_zone.name
        return state
