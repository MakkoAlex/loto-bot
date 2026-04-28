from datetime import datetime

import pytest

from loto_bot.models import Draw
from loto_bot.payouts import DEFAULT_PROFILES, parse_system
from loto_bot.validation import walk_forward_validate


def make_draw(day: int, numbers: set[int]) -> Draw:
    return Draw(drawn_at=datetime(2026, 1, day, 15, 0, 0), numbers=frozenset(numbers))


def test_walk_forward_validate_tests_training_winner_on_future_draws() -> None:
    draws = [
        make_draw(1, {1, 2, *range(10, 28)}),
        make_draw(2, {1, 2, *range(30, 48)}),
        make_draw(3, {1, *range(50, 69)}),
        make_draw(4, {1, 2, *range(10, 28)}),
        make_draw(5, set(range(30, 50))),
    ]

    results = walk_forward_validate(
        draws=draws,
        system=parse_system("2/2"),
        profile=DEFAULT_PROFILES["system_2"],
        train_window=3,
        test_window=2,
        candidates=1,
        max_combinations=10_000,
    )

    assert len(results) == 1
    result = results[0]
    assert result.window_index == 1
    assert result.combination == (1, 2)
    assert result.train_result.profit == pytest.approx(39.85)
    assert result.test_result.total_cost == pytest.approx(6.0)
    assert result.test_result.total_return == pytest.approx(22.54)
    assert result.test_result.profit == pytest.approx(16.54)
    assert result.test_result.hit_rate_at_least_2 == pytest.approx(0.5)
    assert result.search_mode == "exact"


def test_walk_forward_validate_uses_training_only_frequency_pool() -> None:
    draws = [
        make_draw(1, {1, 2, 3, *range(10, 27)}),
        make_draw(2, {1, 2, 3, *range(30, 47)}),
        make_draw(3, {70, 71, 72, *range(40, 57)}),
        make_draw(4, {70, 71, 72, *range(50, 67)}),
    ]

    results = walk_forward_validate(
        draws=draws,
        system=parse_system("3/3"),
        profile=DEFAULT_PROFILES["system_3"],
        train_window=2,
        test_window=2,
        candidates=1,
        pool_size=3,
        max_combinations=10_000,
    )

    assert results[0].combination == (1, 2, 3)
    assert results[0].search_mode == "top-3"
