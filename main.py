from __future__ import annotations
import sys

from map_parser import MapParser, MapParseError
from simulator import Simulator
from renderer import TerminalRenderer
from router import NoSolutionError


class Application:
    """Wire the whole pipeline: parse -> simulate -> render.

    Owns the high-level flow for one map file and turns any
    expected failure  (bad file, unsolvable map, deadlock)
    into a clean message plus a non-zero exit code.

    Args:
            map_path: Path to the .txt map file to play
    """

    def __init__(self, map_path: str) -> None:
        """Store the map path (work happens in run)"""
        self.map_path = map_path

    def run(self) -> int:
        """Run the pipeline, returning a shell exit code.

        Returns:
                0 on success, 1 if an expected error was handled.
        """
        try:
            graph, nb_drones = MapParser().parse(self.map_path)
            simulator = Simulator(graph, nb_drones)
            simulator.run()
            TerminalRenderer(simulator).render()
        except FileNotFoundError:
            return self._fail(f"map file not found: {self.map_path}")
        except MapParseError as err:
            return self._fail(f"invalid map - {err}")
        except NoSolutionError as err:
            return self._fail(f"no solution - {err}")
        except RuntimeError as err:
            return self._fail(f"simulation aborted - {err}")
        return 0

    def _fail(self, message: str) -> int:
        """Print an error on stderr and return the failure code."""
        print(f"Error: {message}", file=sys.stderr)
        return 1


def main() -> int:
    """Read the map path from argv and launch the application.

    Returns:
                Process exit code (0 = success, 2 = bad usage).
    """
    if len(sys.argv) != 2:
        print("Usage: python main.py <map_file>", file=sys.stderr)
        return 2
    return Application(sys.argv[1]).run()


if __name__ == "__main__":
    sys.exit(main())
