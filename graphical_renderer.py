"""Graphical renderer - animate the simulation with matplotlib.

  Draws the zone graph at the zones' (x, y) coordinates, then (step B)
  moves one coloured dot per drone over it, turn by turn, reading the
  frames stored in Simulator.snapshots. Kept apart from renderer.py so
  the terminal renderer never has to import matplotlib.
  """

from __future__ import annotations
import math
from typing import Any


from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.artist import Artist

from renderer import Renderer
from simulator import Simulator
from zone import Zone, ZoneType


class GraphicalRenderer(Renderer):
    """Animate the finished simulation as a moving graph.

    Zone form a static, colour-coded background; drones (step B)
    are dots refreshed every frame from Simulator.snapshots.

    Args:
            simulator: A Simulator on which run() has been called.
    """

    # Background colour of a zone, keyed by its type.
    ZONE_COLORS: dict[ZoneType, str] = {
        ZoneType.NORMAL: "#b0bec5",
        ZoneType.PRIORITY: "#66bb6a",
        ZoneType.RESTRICTED: "#ffa726",
        ZoneType.BLOCKED: "#ef5350",
    }

    # Cycled through by drone id (same idea as TerminalRenderer)
    DRONE_SPREAD: float = 0.18
    DRONE_COLORS: list[str] = [
        "#1e88e5", "#d81b60", "#8e24aa",
        "#00897b", "#f4511e", "#3949ab",
    ]

    def __init__(self, simulator: Simulator) -> None:
        """Store the simulation; the figure is built in render()"""
        super().__init__(simulator)
        # built in render(); kept as attributes so the animation
        # callback (_update, step B) can reach them.
        self.fig: Any = None
        self.ax: Any = None
        self.dots: Any = None
        self.anim: Any = None

    def render(self) -> None:
        """Draw the static graph (drone animation comes in step B)"""
        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self._draw_connections()
        self._draw_zones()
        self._init_drones()
        self.ax.set_aspect("equal")
        self.ax.margins(0.15)
        self.anim = FuncAnimation(
            self.fig, self._update,
            frames=len(self.simulator.snapshots),
            interval=1200, repeat=True,
        )
        plt.tight_layout()
        plt.show()

    def _draw_connections(self) -> None:
        """Draw every connection as a thin line between two zones."""
        for conn in self.simulator.graph.connections:
            xa, ya = self._zone_xy(conn.zone_a)
            xb, yb = self._zone_xy(conn.zone_b)
            self.ax.plot(
                [xa, xb], [ya, yb],
                color="#cfd8dc", linewidth=1.5, zorder=1,
            )

    def _draw_zones(self) -> None:
        """Draw each zone as a coloured marker with its name."""
        for zone in self.simulator.graph.zones.values():
            self.ax.scatter(
                zone.x, zone.y,
                c=self.ZONE_COLORS[zone.zone_type],
                marker=self._zone_marker(zone),
                s=420, edgecolors="black", zorder=2,
            )
            self.ax.annotate(
                zone.name, (zone.x, zone.y),
                xytext=(0, 12), textcoords="offset points",
                ha="center", va="center", fontsize=8,
            )

    def _zone_marker(self, zone: Zone) -> str:
        """Marker shape: square = start, start = end, dot otherwise."""
        if zone.is_start:
            return "s"
        if zone.is_end:
            return "*"
        return "o"

    def _zone_xy(self, name: str) -> tuple[float, float]:
        """Return the (x, y) coordinates of a zone, as floats"""
        zone = self.simulator.graph.zones[name]
        return float(zone.x), float(zone.y)

    def _init_drones(self) -> None:
        """Create the drone scatter at their turn-0 positions"""
        colors = [self._drone_color(d) for d in self._drone_ids()]
        positions = self._positions_at(0)
        self.dots = self.ax.scatter(
            [xy[0] for xy in positions],
            [xy[1] for xy in positions],
            c=colors, s=140, zorder=3, edgecolors="black",
        )

    def _update(self, frame: int) -> list[Artist]:
        """Animation callback: move drones to their frame positions."""
        self.dots.set_offsets(self._positions_at(frame))
        self.ax.set_title(f"Fly-in - turn {frame}")
        return [self.dots]

    def _positions_at(self, frame: int) -> list[tuple[float, float]]:
        """Return every drone's (x, y) at a frame, sorted by id.

          Drones sharing the same zone (or connection midpoint) are
          fanned out around it, so overlapping drones never collapse
          into a single dot.
          """
        state = self.simulator.snapshots[frame]
        bases = [self._drone_xy(state[d]) for d in sorted(state)]
        return self._spread_overlaps(bases)

    def _spread_overlaps(
            self, bases: list[tuple[float, float]]
    ) -> list[tuple[float, float]]:
        """Fan out drones that share an identical base position

        Groups positions by exact (x, y); any group of 2+
        is spread on a small circle. Order is preserved so
        each drone keeps its colour slot.
        """
        groups: dict[tuple[float, float], list[int]] = {}
        for index, xy in enumerate(bases):
            groups.setdefault(xy, []).append(index)
        result = list(bases)
        for members in groups.values():
            if len(members) > 1:
                self._fan_out(result, members)
        return result

    def _fan_out(
            self,
            positions: list[tuple[float, float]],
            members: list[int],
    ) -> None:
        """Spread members evenly on a small circle around center"""
        count = len(members)
        center_x, center_y = positions[members[0]]
        for rank, index in enumerate(members):
            angle = 2.0 * math.pi * rank / count
            positions[index] = (
                center_x + self.DRONE_SPREAD * math.cos(angle),
                center_y + self.DRONE_SPREAD * math.sin(angle),
            )

    def _drone_xy(self, token: str) -> tuple[float, float]:
        """Locate a drone from its snapshot token

        A token is a zone name ('roof1') or a connection label
        ('roof1-roof2'). On a connection the drone sits at the
        midpoint of the segment between the two zones.
        """
        parts = token.split("-")
        if len(parts) == 1:
            return self._zone_xy(parts[0])
        xa, ya = self._zone_xy(parts[0])
        xb, yb = self._zone_xy(parts[1])
        return (xa + xb) / 2, (ya + yb) / 2

    def _drone_ids(self) -> list[int]:
        """Return all drone ids, sorted (stable scatter order)."""
        return sorted(self.simulator.snapshots[0])

    def _drone_color(self, drone_id: int) -> str:
        """Return the stable colour assigned to a drone id."""
        index = (drone_id - 1) % len(self.DRONE_COLORS)
        return self.DRONE_COLORS[index]
