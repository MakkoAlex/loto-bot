from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

DRAW_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DRAW_SIZE = 20
MIN_NUMBER = 1
MAX_NUMBER = 80


@dataclass(frozen=True)
class Draw:
    drawn_at: datetime
    numbers: frozenset[int]


def parse_archive_row(row: Mapping[str, object]) -> Draw:
    try:
        raw_date = row["date"]
        raw_numbers = row["numbers"]
    except KeyError as exc:
        raise ValueError(f"Archive row is missing required field: {exc.args[0]}") from exc

    if not isinstance(raw_date, str):
        raise ValueError("Archive row date must be text")
    if not isinstance(raw_numbers, str):
        raise ValueError("Archive row numbers must be text")

    try:
        drawn_at = datetime.strptime(raw_date, DRAW_DATE_FORMAT)
    except ValueError as exc:
        raise ValueError(f"Invalid draw date {raw_date!r}; expected {DRAW_DATE_FORMAT}") from exc

    try:
        numbers = frozenset(int(part.strip()) for part in raw_numbers.split(","))
    except ValueError as exc:
        raise ValueError(f"Invalid draw numbers {raw_numbers!r}; all values must be integers") from exc

    if len(numbers) != DRAW_SIZE:
        raise ValueError(f"Draw must contain exactly {DRAW_SIZE} unique numbers")

    out_of_range = sorted(number for number in numbers if number < MIN_NUMBER or number > MAX_NUMBER)
    if out_of_range:
        raise ValueError(f"Draw numbers must be in range {MIN_NUMBER}..{MAX_NUMBER}: {out_of_range}")

    return Draw(drawn_at=drawn_at, numbers=numbers)
