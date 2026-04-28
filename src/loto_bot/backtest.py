from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from math import comb
from typing import Iterable, Sequence

from loto_bot.models import MAX_NUMBER, MIN_NUMBER, Draw
from loto_bot.payouts import BettingSystem, PayoutProfile


@dataclass(frozen=True)
class BacktestResult:
    combination: tuple[int, ...]
    system: BettingSystem
    profile_name: str
    ticket_count: int
    draw_count: int
    total_cost: float
    total_return: float
    profit: float
    roi: float
    hit_counts: dict[int, int]
    hit_rate_at_least_2: float
    longest_losing_streak: int
    recent_cost: float
    recent_return: float
    recent_profit: float
    recent_roi: float
    last_profitable_hit_date: datetime | None
    score: float


def hit_count(combination: Sequence[int], draw: Draw) -> int:
    return len(set(combination) & draw.numbers)


def expanded_tickets(combination: Sequence[int], ticket_size: int) -> tuple[tuple[int, ...], ...]:
    if ticket_size > len(combination):
        raise ValueError("ticket size cannot exceed picked numbers")
    return tuple(combinations(tuple(sorted(combination)), ticket_size))


def backtest_combination(
    combination: Sequence[int],
    draws: Sequence[Draw],
    system: BettingSystem,
    profile: PayoutProfile,
    recent_window: int = 100,
) -> BacktestResult:
    selected = tuple(sorted(combination))
    if len(selected) != system.picked_numbers:
        raise ValueError("combination size must match picked numbers")
    if len(set(selected)) != len(selected):
        raise ValueError("combination numbers must be unique")
    if profile.ticket_size > system.picked_numbers:
        raise ValueError("profile ticket size cannot exceed picked numbers")

    selected_set = frozenset(selected)
    ticket_count = comb(system.picked_numbers, profile.ticket_size)
    per_draw_cost = ticket_count * profile.cost
    return_by_full_hits = {
        full_hits: _expanded_return(
            full_hits=full_hits,
            picked_numbers=system.picked_numbers,
            profile=profile,
        )
        for full_hits in range(system.picked_numbers + 1)
    }
    returns: list[float] = []
    hit_counts: Counter[int] = Counter()
    longest_losing_streak = 0
    current_losing_streak = 0
    last_profitable_hit_date: datetime | None = None

    for draw in draws:
        full_hits = len(selected_set & draw.numbers)
        hit_counts[full_hits] += 1
        draw_return = return_by_full_hits[full_hits]
        returns.append(draw_return)

        if draw_return > per_draw_cost:
            current_losing_streak = 0
            if last_profitable_hit_date is None or draw.drawn_at > last_profitable_hit_date:
                last_profitable_hit_date = draw.drawn_at
        else:
            current_losing_streak += 1
            longest_losing_streak = max(longest_losing_streak, current_losing_streak)

    draw_count = len(draws)
    total_cost = per_draw_cost * draw_count
    total_return = sum(returns)
    profit = total_return - total_cost
    roi = profit / total_cost if total_cost else 0.0

    recent_returns = returns[:recent_window] if recent_window > 0 else []
    recent_cost = per_draw_cost * len(recent_returns)
    recent_return = sum(recent_returns)
    recent_profit = recent_return - recent_cost
    recent_roi = recent_profit / recent_cost if recent_cost else 0.0
    at_least_2_hits = sum(count for hits, count in hit_counts.items() if hits >= 2)
    hit_rate_at_least_2 = at_least_2_hits / draw_count if draw_count else 0.0
    streak_penalty = longest_losing_streak / draw_count if draw_count else 0.0
    score = roi + (recent_roi * 0.25) - streak_penalty

    return BacktestResult(
        combination=selected,
        system=system,
        profile_name=profile.name,
        ticket_count=ticket_count,
        draw_count=draw_count,
        total_cost=round(total_cost, 10),
        total_return=round(total_return, 10),
        profit=round(profit, 10),
        roi=roi,
        hit_counts=dict(sorted(hit_counts.items())),
        hit_rate_at_least_2=hit_rate_at_least_2,
        longest_losing_streak=longest_losing_streak,
        recent_cost=round(recent_cost, 10),
        recent_return=round(recent_return, 10),
        recent_profit=round(recent_profit, 10),
        recent_roi=recent_roi,
        last_profitable_hit_date=last_profitable_hit_date,
        score=score,
    )


def _expanded_return(full_hits: int, picked_numbers: int, profile: PayoutProfile) -> float:
    total_return = 0.0
    missed_numbers = picked_numbers - full_hits
    for tier_hits, gross_return in profile.returns_by_hits.items():
        if tier_hits > full_hits:
            continue
        misses_needed = profile.ticket_size - tier_hits
        if misses_needed > missed_numbers:
            continue
        total_return += comb(full_hits, tier_hits) * comb(missed_numbers, misses_needed) * gross_return
    return total_return


def rank_combinations(
    draws: Sequence[Draw],
    system: BettingSystem,
    profile: PayoutProfile,
    top: int = 50,
    recent_window: int = 100,
    max_combinations: int = 1_000_000,
    number_pool: Iterable[int] | None = None,
) -> list[BacktestResult]:
    pool = tuple(sorted(number_pool if number_pool is not None else range(MIN_NUMBER, MAX_NUMBER + 1)))
    combination_count = comb(len(pool), system.picked_numbers)
    if combination_count > max_combinations:
        raise ValueError(
            f"Search would evaluate {combination_count:,} combinations; "
            f"raise max_combinations or use a smaller number pool"
        )

    results = [
        backtest_combination(
            combination=candidate,
            draws=draws,
            system=system,
            profile=profile,
            recent_window=recent_window,
        )
        for candidate in combinations(pool, system.picked_numbers)
    ]
    results.sort(key=lambda item: (-item.score, -item.roi, -item.profit, item.combination))
    return results[:top]
