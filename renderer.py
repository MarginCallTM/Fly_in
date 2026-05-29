"""Renderers - turn a finished simulation into a visible output.

  Defines an abstract Renderer (the shared interface) and a concrete
  TerminalRenderer that prints the subject's turn-by-turn format with
  colorama. The matplotlib renderer lives in its own module so this
  one never has to import matplotlib.
  """

from __future__ import annotations
from abc import ABC, abstractmethod

from colorama import Style, init as colorama_init

from color_palette import ColorPalette
from simulator import Simulator, Movement


class Renderer(ABC):
    """Common interface for every simulation renderer.

    A renderer consumes a *finished* simulation (run()
    has already filled its history and snapshots) and
    presents it. Subclasses pick the medium: terminal
    text, matplotlib animation, etc.

    Args:
            simulator: A Simulator on wich run() has been called.
    """

    def __init__(self, simulator: Simulator) -> None:
        """Store the finished simulation to render."""
        self.simulator = simulator

    @abstractmethod
    def render(self) -> None:
        """Present the whole simulation (implemented by subclasses)."""


class TerminalRenderer(Renderer):
    """Print the simulation as the subject's turn-by-turn text.

    Each played turn becomes one line of 'D<ID>-<zone>' tokens,
    coloured per drone so a single drone is easy to follow across
    turns. Drones that do not move are omitted

    Args:
                simulator: A Simulator on which run() has been called
    """

    def __init__(self, simulator: Simulator) -> None:
        """Enable colorama, then store the simulation. """
        super().__init__(simulator)
        colorama_init(autoreset=True)
        self.palette = ColorPalette()

    def render(self) -> None:
        """Print a header, then one line per played turn"""
        self._print_header()
        self._print_legend()
        for moves in self.simulator.history:
            line = " ".join(self._format_move(m) for m in moves)
            print(line)

    def _print_header(self) -> None:
        """Print a one-line summary above the turn light"""
        turns = len(self.simulator.history)
        print(
            f"{Style.BRIGHT}Fly-in{Style.RESET_ALL} - "
            f"{self.simulator.nb_drones} drones, {turns} turns"
        )

    def _print_legend(self) -> None:
        """Print each colored zone once as a visual key.

        Proves the map colors are honored, even for a zone a
        drone only crosses for a single turn. Zones with no
        color are skipped to keep the legend short.
        """
        colored = [
            zone for zone in self.simulator.graph.zones.values()
            if zone.color is not None
        ]
        if not colored:
            return
        tokens = [self._color_zone(zone.name) for zone in colored]
        print("Zones: " + " ".join(tokens))

    def _color_zone(self, destination: str) -> str:
        """Wrap a destination token in its zone's declared color

        The token is a zone name, or an 'a-b' connection label
        while in transit; the arrival zone (after the dash) drves
        the color. An unknow/absent color leave the token plain

        Args:
            destination: Zone name or connection label.

        Returns: The token, ANSI-colored when the zone has a known
            color, otherzise unchanged
        """
        zone_name = destination.split("-")[-1]
        zone = self.simulator.graph.zones.get(zone_name)
        color = zone.color if zone is not None else None
        code = self.palette.terminal_code(color)
        if not code:
            return destination
        return f"{code}{destination}{self.palette.reset()}"

    def _format_move(self, move: Movement) -> str:
        """Color the whole token in its destination zone's color.

          The 'D<id>-' prefix and the zone name now share a single
          color: the one declared for the arrival zone in the map.
          A zone with no/unknown color leaves the token unstyled.

          Args:
              move: The move to render as 'D<id>-<zone>'.

          Returns: The styled token string.
        """
        token = f"D{move.drone_id}-{move.destination}"
        return self._color_zone(token)
