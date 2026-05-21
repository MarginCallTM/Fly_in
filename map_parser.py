"""Map parser - turns a .txt map file into a Graph object."""

from __future__ import annotations

from graph import Graph


class MapParseError(Exception):
    """Raised when a map file cannot be parsed.

    Always carries the line number where the problem occured,
    so the top-level handler can print a clean diagnostic.

    Attributes:
        line_no: 1-based index of the offending line.
    """

    def __init__(self, line_no: int, message: str) -> None:
        """Build a MapParseError tagged with its source line."""
        super().__init__(f"Line {line_no}: {message}")
        self.line_no = line_no


class MapParser:
    """Read a map file and build the corresponding Graph.

    Usage:
        parser = MapParser()
        graph, nb_drones = parser.parse("maps/easy/01.txt")

    The parser is single-use: call parse() once per file. State
    accumulated during parsing (graph being built, nb_drones,
    seen flags) is reset at the start of each call.
    """

    def __init__(self) -> None:
        """Initialize an empty parser (state set up in parse)."""
        self._graph: Graph = Graph()
        self._nb_drones: int = 0
        self._nb_drones_seen: bool = False

    def parse(self, filepath: str) -> tuple[Graph, int]:
        """Parse a map file and return its Graph and drone count.

        Args:
            filepath: Path to the map file to read.

        Retruns: A (graph, nb_drones) tuple. The graph is
        already validated (start/ end hubs present).

        Raises:
            MapParseError: if any line is malformed, or if the
            file is missing required declarations.
        """
        self._graph = Graph()
        self._nb_drones = 0
        self._nb_drones_seen = False

        with open(filepath, "r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                self._route_line(line, line_no)

        if not self._nb_drones_seen:
            raise MapParseError(0, "missing 'nb_drones' declaration")
        self._graph.validate()
        return self._graph, self._nb_drones

    def _route_line(self, line: str, line_no: int) -> None:
        """Dispatch a stripped, non-comment line to its parser.

        Args:
            line: The cleaned line content (no trailing newline).
            line_no: 1-based source line number for error reporting.

        Raises:
            MapParseError: If then line does not start with any
                know keyword
        """
        prefix = line.split(":", 1)[0]
        match prefix:
            case "nb_drones":
                self._parse_nb_drones(line, line_no)
            case "start_hub" | "end_hub" | "hub":
                # Implemented in Session B
                raise MapParseError(line_no, "zone parser not ready")
            case "connection":
                # Implemented in Session C
                raise MapParseError(line_no, "connection parser not ready")
            case _:
                raise MapParseError(
                    line_no, f"unknow keyword '{prefix}'"
                )

    def _parse_nb_drones(self, line: str, line_no: int) -> None:
        """Parse a 'nb_drones: <int>' declaration

        Args:
            line: The full source line.
            line_no: 1-based source line number for error reporting.

        Raises:
            MapParseError: If nb_drones appears twice, if the value
                is missing, not an integer, or not strictly positive.
        """
        if self._nb_drones_seen:
            raise MapParseError(line_no, "duplicate 'nb_drones'")
        _, _, value = line.partition(":")
        value = value.strip()
        try:
            n = int(value)
        except ValueError:
            raise MapParseError(
                line_no, f"nb_drones value '{value}' is not an integer"
            )
        if n <= 0:
            raise MapParseError(
                line_no, f"nb_drones must be ? 0 (got {n})"
            )
        self._nb_drones = n
        self._nb_drones_seen = True
