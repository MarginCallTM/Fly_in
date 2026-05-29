"""Color palette - map map-file color names to real output colors.

  The subject allows any single-word string as a zone color and fixes
  no list of allowed values, so this palette never rejects a name:
  an unknown color simply produces no styling instead of crashing.
  The table below is the sample of every color used across maps/.
  """

from __future__ import annotations

from typing import Optional


class ColorPalette:
    """Translate a map color name into a terminal (ANSI) color.

    An 8-color terminal cannot show orange, gold, crimson...
    the 256-color ANSI set can, so the table maps each sampled name to
    its 256-color code. A name absent from the table is not an
    error: terminal_code returns an emmpty string and the caller
    leaves that token unstyled
    """

    # 256-color ANSI codes for every color found in maps/
    _ANSI_CODES: dict[str, int] = {
        "black": 0,
        "red": 196,
        "green": 46,
        "yellow": 226,
        "blue": 39,
        "magenta": 201,
        "cyan": 51,
        "orange": 208,
        "purple": 129,
        "darkred": 88,
        "gold": 220,
        "brown": 130,
        "maroon": 124,
        "crimson": 197,
        "lime": 118,
        "violet": 177,
    }

    _RESET: str = "\033[0m"

    def terminal_code(self, color: Optional[str]) -> str:
        """Return the ANSI sequence that opens a color.

          Args:
              color: A color name from the map, or None.

          Returns: The '\\033[38;5;Nm' escape for a known color, or
              an empty string when color is None or unknown (so the
              caller prints the token without any styling).
          """
        if color is None:
            return ""
        code = self._ANSI_CODES.get(color.lower())
        if code is None:
            return ""
        return f"\033[38;5;{code}m"

    def reset(self) -> str:
        """Return the ANSI sequence that clears all styling"""
        return self._RESET
