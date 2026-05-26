"""Renderers - turn a finished simulation into a visible output.

  Defines an abstract Renderer (the shared interface) and a concrete
  TerminalRenderer that prints the subject's turn-by-turn format with
  colorama. The matplotlib renderer lives in its own module so this
  one never has to import matplotlib.
  """

from __future__ import annotations
from abc import ABC, abstractmethod

from colorama import Fore, Style, init as colorama_init

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

    # Cycled through ny drone id so each drone keeps one colour.
    COLORS: list[str] = [
        Fore.GREEN, Fore.CYAN, Fore.YELLOW,
        Fore.MAGENTA, Fore.BLUE, Fore.RED,
    ]

    def __init__(self, simulator: Simulator) -> None:
        """Enable colorama, then store the simulation. """
        super().__init__(simulator)
        colorama_init(autoreset=True)

    def render(self) -> None:
        """Print a header, then one line per played turn"""
        self._print_header()
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

    def _color_for(self, drone_id: int) -> str:
        """Return the stable colour assigned to a drone id."""
        return self.COLORS[(drone_id - 1) % len(self.COLORS)]

    def _format_move(self, move: Movement) -> str:
        """Colour one move token, e.g. a green 'D1-roof1'"""
        color = self._color_for(move.drone_id)
        return f"{color}{move}{Style.RESET_ALL}"
