from datetime import datetime

import pytest

from loto_bot.backtest import backtest_combination, rank_combinations
from loto_bot.models import Draw
from loto_bot.payouts import DEFAULT_PROFILES, parse_system


def make_draw(day: int, numbers: set[int]) -> Draw:
    return Draw(drawn_at=datetime(2026, 1, day, 15, 0, 0), numbers=frozenset(numbers))


def test_backtest_direct_system_calculates_money_metrics() -> None:
    draws = [
        make_draw(1, {1, 2, *range(10, 28)}),
        make_draw(2, {1, *range(30, 49)}),
        make_draw(3, set(range(50, 70))),
    ]

    result = backtest_combination(
        combination=(1, 2),
        draws=draws,
        system=parse_system("2/2"),
        profile=DEFAULT_PROFILES["system_2"],
        recent_window=2,
    )

    assert result.total_cost == pytest.approx(9.0)
    assert result.total_return == pytest.approx(26.31)
    assert result.profit == pytest.approx(17.31)
    assert result.roi == pytest.approx(1.9233333333)
    assert result.hit_counts == {0: 1, 1: 1, 2: 1}
    assert result.hit_rate_at_least_2 == pytest.approx(1 / 3)
    assert result.longest_losing_streak == 1


def test_backtest_expanded_system_sums_sub_ticket_costs_and_returns() -> None:
    draws = [make_draw(1, {1, 2, 3, *range(10, 27)})]

    result = backtest_combination(
        combination=(1, 2, 3, 4, 5),
        draws=draws,
        system=parse_system("3/5"),
        profile=DEFAULT_PROFILES["system_3"],
        recent_window=1,
    )

    assert result.total_cost == pytest.approx(70.0)
    assert result.total_return == pytest.approx(267.55)
    assert result.profit == pytest.approx(197.55)


def test_rank_combinations_sorts_by_roi_then_profit_then_numbers() -> None:
    draws = [
        make_draw(1, {1, 2, *range(10, 28)}),
        make_draw(2, set(range(30, 50))),
    ]

    results = rank_combinations(
        draws=draws,
        system=parse_system("2/2"),
        profile=DEFAULT_PROFILES["system_2"],
        max_combinations=10_000,
    )

    assert results[0].combination == (1, 2)
