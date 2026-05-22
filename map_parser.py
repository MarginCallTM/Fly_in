"""Map parser - turns a .txt map file into a Graph object."""

from __future__ import annotations

from graph import Graph
from zone import Zone, ZoneType
from connection import Connection


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

        Returns: A (graph, nb_drones) tuple. The graph is
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
        try:
            self._graph.validate()
        except ValueError as err:
            raise MapParseError(0, str(err))
        return self._graph, self._nb_drones

    def _route_line(self, line: str, line_no: int) -> None:
        """Dispatch a stripped, non-comment line to its parser.

        Args:
            line: The cleaned line content (no trailing newline).
            line_no: 1-based source line number for error reporting.

        Raises:
            MapParseError: If the line does not start with any
                known keyword.
        """
        prefix = line.split(":", 1)[0]
        match prefix:
            case "nb_drones":
                self._parse_nb_drones(line, line_no)
            case "start_hub" | "end_hub" | "hub":
                self._parse_zone(line, line_no, prefix)
            case "connection":
                self._parse_connection(line, line_no)
            case _:
                raise MapParseError(
                    line_no, f"unknown keyword '{prefix}'"
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
                line_no, f"nb_drones must be > 0 (got {n})"
            )
        self._nb_drones = n
        self._nb_drones_seen = True

    def _parse_zone(
            self, line: str, line_no: int, prefix: str
    ) -> None:
        """Parse a 'start_hub/end_hub/hub: ...' declaration.

        Args:
            line: The full source line.
            line_no: 1-based source line number.
            prefix: Which keyword matched ('start_hub',
                'end_hub' or 'hub').

        Raises:
            MapParseError: If the body is malformed, the name
                contains '-', or coordinates are not integers.
        """
        # Strip 'start_hub:' off the front, keep the rest.
        _, _, rest = line.partition(":")
        rest = rest.strip()
        if not rest:
            raise MapParseError(
                line_no, f"empty body after '{prefix}'"
            )
        # Split 'name x y' from the optional '[meta]' block.
        main_part, metadata = self._extract_metadata(
            rest, line_no
        )
        tokens = main_part.split()
        if len(tokens) != 3:
            raise MapParseError(
                line_no,
                f"expected 'name x y', got '{main_part}'",
            )
        name, x_str, y_str = tokens
        if "-" in name:
            raise MapParseError(
                line_no,
                f"zone name '{name}' must not contain '-'",
            )
        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise MapParseError(
                line_no,
                f"coordinates must be integers "
                f"(got '{x_str}', '{y_str}')"
            )
        zone = self._build_zone(
            name, x, y, prefix, metadata, line_no
        )
        # Graph.add_zone enforces unique name + unique start/end
        try:
            self._graph.add_zone(zone)
        except ValueError as err:
            raise MapParseError(line_no, str(err))

    def _extract_metadata(
            self, rest: str, line_no: int
    ) -> tuple[str, dict[str, str]]:
        """Split the body into 'main' part and metadata dict.

        Args:
            rest: Everything after the ":" of the line.
            line_no: 1-based source line number.

        Returns: Tuple (main_part, metadata). main_part is the
        'name x y' text; metadata is empty if no brackets.

        Raises:
            MapParseError: If a '[' is opened but never closed
            at the end of the line
        """

        if "[" not in rest:
            return rest, {}
        main, _, after = rest.partition("[")
        if not after.endswith("]"):
            raise MapParseError(
                line_no, "metadata must end with ']'"
            )
        inner = after[:-1]  # drop the trailing ']'
        return main.strip(), self._parse_metadata(
            inner, line_no
        )

    def _parse_metadata(
            self, meta_str: str, line_no: int
    ) -> dict[str, str]:
        """Parse 'key=val, key=val' into a dict.

        Args:
            meta_str: Content between '[' and ']'.
            line_no: 1-based source line number.

        Returns: A dict[str, str]. Empty if meta_str is blank.

        Raises:
            MapParseError: On missing '=', empty key/value,
                or duplicate key inside the same bracket block.
        """
        result: dict[str, str] = {}
        if not meta_str.strip():
            return result
        for chunk in meta_str.replace(",", " ").split():
            chunk = chunk.strip()
            if "=" not in chunk:
                raise MapParseError(
                    line_no,
                    f"metadata entry '{chunk}' missing '='"
                )
            key, _, value = chunk.partition("=")
            key = key.strip()
            value = value.strip()
            if not key or not value:
                raise MapParseError(
                    line_no,
                    f"empty key or value in '{chunk}'"
                )
            if key in result:
                raise MapParseError(
                    line_no,
                    f"duplicate metadata key '{key}'"
                )
            result[key] = value
        return result

    def _build_zone(
            self,
            name: str,
            x: int,
            y: int,
            prefix: str,
            metadata: dict[str, str],
            line_no: int,
    ) -> Zone:
        """Construct a Zone from parsed fields and metadata.

        Args:
            name: Zone identifier (no dashes).
            x, y: integer coordinates.
            prefix: 'start_hub', 'end_hub' or 'hub'.
            metadata: Dict from _parse_metadata.
            line_no: 1-based source line number.

        Returns: A fully initialized Zone object.

        Raises:
            MapParseError: If metadata contains unknown keys.
        """
        allowed = {"zone", "color", "max_drones"}
        unknown = set(metadata) - allowed
        if unknown:
            raise MapParseError(
                line_no,
                f"unknown metadata key(s): {sorted(unknown)}",
            )
        zone_type = self._resolve_zone_type(
            metadata.get("zone", "normal"), line_no
        )
        color = metadata.get("color")
        max_drones = self._resolve_max_drones(
            metadata.get("max_drones", "1"), line_no
        )
        return Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
            is_start=(prefix == "start_hub"),
            is_end=(prefix == "end_hub"),
        )

    def _resolve_zone_type(
            self, value: str, line_no: int
    ) -> ZoneType:
        """Map a string ('normal', 'restricted'...) to ZoneType.

        Args:
            value: Raw string from metadata (e.g. 'priority').
            line_no: 1-based source line number.

        Returns: The matching ZoneType member.

        Raises:
            MapParseError: If the string is not a valid type.
        """
        try:
            # ZoneType('normal') works because we set string
            # values when declaring the enum in zone.py.
            return ZoneType(value)
        except ValueError:
            valid = [t.value for t in ZoneType]
            raise MapParseError(
                line_no,
                f"invalid zone type '{value}' "
                f"(valid: {valid})"
            )

    def _resolve_max_drones(
            self, value: str, line_no: int
    ) -> int:
        """Parse and validate the max_drones metadata value.

        Args:
            value: Raw string (e.g. '3').
            line_no: 1-based source line number.

        Returns: The integer value, guaranteed > 0.

        Raises:
            MapParseError: If not an integer or not strictly
                positive.
        """
        try:
            n = int(value)
        except ValueError:
            raise MapParseError(
                line_no,
                f"max_drones value '{value}' is not an integer"
            )
        if n <= 0:
            raise MapParseError(
                line_no, f"max_drones must be > 0 (got {n})"
            )
        return n

    def _parse_connection(
            self, line: str, line_no: int
    ) -> None:
        """Parse a 'connection: a-b [max_link_capacity]' line

        Args:
            line: The full source line.
            line_no: 1-based source line number.

        Raises:
            MapParseError: If the body is empty, the 'a-b' format
            is wrong, the metadata is malformed, or the capacity is
            not a stricly possitive integer. Graph.add_connection
            raises ValueError (caught upstream) if an endpoint zone
            is unknown or the connection (a-b or b-a) is already declared.
        """
        _, _, rest = line.partition(":")
        rest = rest.strip()
        if not rest:
            raise MapParseError(
                line_no, "empty body after 'connection'"
            )
        main_part, metadata = self._extract_metadata(
            rest, line_no
        )
        zone_a, zone_b = self._split_endpoints(
            main_part, line_no
        )
        capacity = self._resolve_link_capacity(
            metadata, line_no
        )
        conn = Connection(zone_a, zone_b, capacity)
        # Graph rejects unknow zone + dupes (a-b / b-a)
        try:
            self._graph.add_connection(conn)
        except ValueError as err:
            raise MapParseError(line_no, str(err))

    def _split_endpoints(
            self, main_part: str, line_no: int
    ) -> tuple[str, str]:
        """Split 'a-b' into a clean (zone_a, zone_b) tuple.
        Zone names cannot contain '-' (enforced by _parse_zone),
        so exactly one dash is expected.

        Args:
            main_part: Text before the optional '[meta]' block.
            line_no: 1-based source line number.

        Returns: Tuple of two non-empty endpoint names.

        Raises:
            MapParseError: If the format is not 'a-b', if either
            endpoint is empty, or if both endpoints are equal
            (self-loop is rejected as degenerate).
        """
        parts = main_part.split("-")
        if len(parts) != 2:
            raise MapParseError(
                line_no,
                f"expected 'a-b' format, got '{main_part}'"
            )
        zone_a = parts[0].strip()
        zone_b = parts[1].strip()
        if not zone_a or not zone_b:
            raise MapParseError(
                line_no,
                f"endpoint name is empty in '{main_part}'"
            )
        if zone_a == zone_b:
            raise MapParseError(
                line_no,
                f"self-loop forbidden ('{zone_a}' to itself)"
            )
        return zone_a, zone_b

    def _resolve_link_capacity(
            self, metadata: dict[str, str], line_no: int
    ) -> int:
        """Validate metadata keys and return max_link_capacity.

        Args:
            metadata: Dict produced by _parse_metadata.
            line_no: 1-based source line number.

        Returns: The capacity as a strictly positive int
            (defaults to 1 if absent).

        Raises:
            MapParseError: If a metadata key other than
                'max_link_capacity' is present, or if the value
                is not an integer > 0.
        """
        allowed = {"max_link_capacity"}
        unknown = set(metadata) - allowed
        if unknown:
            raise MapParseError(
                line_no,
                f"unknown metadata key(s): {sorted(unknown)}"
            )
        value = metadata.get("max_link_capacity", "1")
        try:
            n = int(value)
        except ValueError:
            raise MapParseError(
                line_no,
                f"max_link_capacity '{value}' "
                f"is not an integer"
            )
        if n <= 0:
            raise MapParseError(
                line_no,
                f"max_link_capacity must be > 0 (got {n})"
            )
        return n
