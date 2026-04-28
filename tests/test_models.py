from datetime import datetime

import pytest

from loto_bot.models import Draw, parse_archive_row


def test_parse_archive_row_returns_validated_draw() -> None:
    draw = parse_archive_row(
        {
            "date": "2026-04-28 15:00:00",
            "numbers": (
                "1, 8, 9, 10, 17, 18, 22, 23, 26, 27, 29, "
                "41, 53, 59, 60, 61, 62, 66, 69, 77"
            ),
        }
    )

    assert draw == Draw(
        drawn_at=datetime(2026, 4, 28, 15, 0, 0),
        numbers=frozenset(
            {1, 8, 9, 10, 17, 18, 22, 23, 26, 27, 29, 41, 53, 59, 60, 61, 62, 66, 69, 77}
        ),
    )


def test_parse_archive_row_rejects_duplicate_numbers() -> None:
    numbers = "1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19"

    with pytest.raises(ValueError, match="20 unique numbers"):
        parse_archive_row({"date": "2026-04-28 15:00:00", "numbers": numbers})


def test_parse_archive_row_rejects_out_of_range_numbers() -> None:
    numbers = "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 81"

    with pytest.raises(ValueError, match="1..80"):
        parse_archive_row({"date": "2026-04-28 15:00:00", "numbers": numbers})
