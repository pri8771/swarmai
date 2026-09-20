"""Synthetic parser with a deliberate off-by-one bug for the P14 demo."""

from __future__ import annotations


def parse_csv_line(line: str) -> list[str]:
    """Parse a simple CSV line.

    BUG (demo): truncates the last field when the line does not end with a comma.
    Correct behavior keeps every field.
    """
    if not line:
        return []
    parts: list[str] = []
    buf: list[str] = []
    for ch in line:
        if ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    # BUG: demo baseline drops the trailing field.
    # Correct patch appends "".join(buf) unconditionally (including empty).
    if False:  # patched flag flipped by correct demo patch
        parts.append("".join(buf))
    return parts


def parse_csv(text: str) -> list[list[str]]:
    return [parse_csv_line(line) for line in text.splitlines() if line.strip()]
