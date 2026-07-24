"""Strict RLE parsing and canonicalisation for cellular-automata patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence


_HEADER_RE = re.compile(
    r"^\s*x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)"
    r"(?:\s*,\s*rule\s*=\s*([^,\s]+))?\s*$",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"(\d*)([bo$!])", re.IGNORECASE)


class RLEError(ValueError):
    """Raised when an RLE document is malformed."""


@dataclass(frozen=True)
class RLEPattern:
    width: int
    height: int
    rule: str | None
    cells: tuple[tuple[int, ...], ...]
    comments: tuple[str, ...] = ()


def normalize_rule(rule: str | None) -> str | None:
    """Return a canonical ``B.../S...`` rulestring."""
    if rule is None:
        return None
    compact = rule.upper().replace(" ", "")
    match = re.fullmatch(r"B([0-8]*)/S([0-8]*)", compact)
    if not match:
        reverse = re.fullmatch(r"S([0-8]*)/B([0-8]*)", compact)
        if not reverse:
            raise RLEError(f"unsupported rulestring: {rule!r}")
        birth, survival = reverse.group(2), reverse.group(1)
    else:
        birth, survival = match.groups()
    if len(set(birth)) != len(birth) or len(set(survival)) != len(survival):
        raise RLEError(f"duplicate neighbor count in rulestring: {rule!r}")
    return f"B{''.join(sorted(birth))}/S{''.join(sorted(survival))}"


def trim_cells(cells: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    """Remove empty borders while preserving an empty pattern as ``()``."""
    if not cells:
        return ()
    width = len(cells[0])
    if any(len(row) != width for row in cells):
        raise RLEError("cell matrix is not rectangular")
    if any(cell not in (0, 1) for row in cells for cell in row):
        raise RLEError("cell matrix must contain only 0 and 1")
    live = [
        (row_index, column_index)
        for row_index, row in enumerate(cells)
        for column_index, cell in enumerate(row)
        if cell
    ]
    if not live:
        return ()
    top = min(row for row, _ in live)
    bottom = max(row for row, _ in live)
    left = min(column for _, column in live)
    right = max(column for _, column in live)
    return tuple(
        tuple(int(cell) for cell in row[left : right + 1])
        for row in cells[top : bottom + 1]
    )


def parse_rle(text: str, *, trim: bool = True) -> RLEPattern:
    """Parse a complete RLE document and reject unknown/trailing tokens."""
    comments: list[str] = []
    header: tuple[int, int, str | None] | None = None
    body_parts: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments.append(line)
            continue
        if header is None:
            match = _HEADER_RE.fullmatch(line)
            if not match:
                raise RLEError("missing or malformed RLE header")
            header = (
                int(match.group(1)),
                int(match.group(2)),
                normalize_rule(match.group(3)),
            )
        else:
            body_parts.append(re.sub(r"\s+", "", line))
    if header is None:
        raise RLEError("missing RLE header")
    declared_width, declared_height, rule = header
    if declared_width <= 0 or declared_height <= 0:
        raise RLEError("RLE dimensions must be positive")

    body = "".join(body_parts)
    if not body.endswith("!"):
        raise RLEError("RLE body must end with !")
    tokens = list(_TOKEN_RE.finditer(body))
    if not tokens or "".join(match.group(0) for match in tokens) != body:
        raise RLEError("RLE body contains an unsupported token")
    if any(match.group(2).lower() == "!" for match in tokens[:-1]):
        raise RLEError("RLE terminator must be the final token")

    rows = [[0] * declared_width for _ in range(declared_height)]
    row = column = 0
    terminated = False
    for match in tokens:
        count = int(match.group(1) or "1")
        token = match.group(2).lower()
        if count <= 0:
            raise RLEError("RLE run lengths must be positive")
        if token == "!":
            if count != 1:
                raise RLEError("RLE terminator cannot have a run length")
            terminated = True
            break
        if token == "$":
            row += count
            column = 0
            # A trailing row separator before ``!`` is legal; any later cell
            # token will still fail the bounds check below.
            if row > declared_height:
                raise RLEError("RLE body exceeds declared height")
            continue
        if row >= declared_height or column + count > declared_width:
            raise RLEError("RLE body exceeds declared dimensions")
        if token == "o":
            for offset in range(count):
                rows[row][column + offset] = 1
        column += count
    if not terminated:
        raise RLEError("RLE body is not terminated")

    cells = trim_cells(rows) if trim else tuple(tuple(item for item in row) for row in rows)
    if not cells:
        raise RLEError("empty patterns are not supported")
    height = len(cells)
    width = len(cells[0])
    return RLEPattern(width, height, rule, cells, tuple(comments))


def _encode_row(row: Sequence[int]) -> str:
    last_live = max((index for index, cell in enumerate(row) if cell), default=-1)
    if last_live < 0:
        return ""
    runs: list[str] = []
    value = row[0]
    length = 0
    for cell in row[: last_live + 1]:
        if cell == value:
            length += 1
            continue
        runs.append(("" if length == 1 else str(length)) + ("o" if value else "b"))
        value = cell
        length = 1
    runs.append(("" if length == 1 else str(length)) + ("o" if value else "b"))
    return "".join(runs)


def encode_rle(cells: Sequence[Sequence[int]], rule: str | None = None) -> str:
    """Encode a matrix as compact, border-trimmed RLE."""
    trimmed = trim_cells(cells)
    if not trimmed:
        raise RLEError("empty patterns are not supported")
    width = len(trimmed[0])
    height = len(trimmed)
    header = f"x = {width}, y = {height}"
    canonical_rule = normalize_rule(rule)
    if canonical_rule:
        header += f", rule = {canonical_rule}"
    encoded_rows = [_encode_row(row) for row in trimmed]
    while encoded_rows and not encoded_rows[-1]:
        encoded_rows.pop()
    body_parts: list[str] = []
    pending_empty = 0
    for index, encoded in enumerate(encoded_rows):
        if encoded:
            if pending_empty:
                body_parts.append(("" if pending_empty == 1 else str(pending_empty)) + "$")
                pending_empty = 0
            body_parts.append(encoded)
        if index < len(encoded_rows) - 1:
            pending_empty += 1
    return header + "\n" + "".join(body_parts) + "!"


def _coordinates(cells: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, column)
        for row, values in enumerate(trim_cells(cells))
        for column, cell in enumerate(values)
        if cell
    )


def _normalize_coordinates(
    points: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    materialized = tuple(points)
    min_row = min(row for row, _ in materialized)
    min_column = min(column for _, column in materialized)
    return tuple(
        sorted((row - min_row, column - min_column) for row, column in materialized)
    )


def geometric_signature(cells: Sequence[Sequence[int]]) -> str:
    """Return a rotation/reflection/translation-invariant signature."""
    points = _coordinates(cells)
    if not points:
        raise RLEError("empty patterns are not supported")
    variants = []
    for reflect in (False, True):
        transformed = tuple((row, -column if reflect else column) for row, column in points)
        for rotation in range(4):
            rotated = transformed
            for _ in range(rotation):
                rotated = tuple((column, -row) for row, column in rotated)
            variants.append(_normalize_coordinates(rotated))
    canonical = min(variants)
    return ";".join(f"{row},{column}" for row, column in canonical)
