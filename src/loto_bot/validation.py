from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import comb
from typing import Sequence

from loto_bot.backtest import BacktestResult, backtest_combination, rank_combinations
from loto_bot.models import MAX_NUMBER, MIN_NUMBER, Draw
from loto_bot.payouts import BettingSystem, PayoutProfile

EXACT_PICK_LIMIT = 2


@dataclass(frozen=True)
class ValidationResult:
    window_index: int
    combination: tuple[int, ...]
    system: BettingSystem
    profile_name: str
    search_mode: str
    train_start: Draw
    train_end: Draw
    test_start: Draw
    test_end: Draw
    train_result: BacktestResult
    test_result: BacktestResult


def walk_forward_validate(
    draws: Sequence[Draw],
    system: BettingSystem,
    profile: PayoutProfile,
    train_window: int,
    test_window: int,
    candidates: int = 5,
    step: int | None = None,
    recent_window: int = 100,
    max_combinations: int = 1_000_000,
    pool_size: int = 14,
) -> list[ValidationResult]:
    if train_window < 1:
        raise ValueError("train window must be at least 1")
    if test_window < 1:
        raise ValueError("test window must be at least 1")
    if candidates < 1:
        raise ValueError("candidates must be at least 1")
    step_size = step or test_window
    if step_size < 1:
        raise ValueError("step must be at least 1")

    chronological = sorted(draws, key=lambda draw: draw.drawn_at)
    results: list[ValidationResult] = []
    start = 0
    window_index = 1

    while start + train_window + test_window <= len(chronological):
        train_draws = chronological[start : start + train_window]
        test_draws = chronological[start + train_window : start + train_window + test_window]
        train_eval = tuple(reversed(train_draws))
        test_eval = tuple(reversed(test_draws))
        number_pool, search_mode = resolve_validation_pool(
            draws=train_eval,
            picked_numbers=system.picked_numbers,
            max_combinations=max_combinations,
            pool_size=pool_size,
        )
        training_results = rank_combinations(
            draws=train_eval,
            system=system,
            profile=profile,
            top=candidates,
            recent_window=recent_window,
            max_combinations=max_combinations,
            number_pool=number_pool,
        )

        for train_result in training_results:
            test_result = backtest_combination(
                combination=train_result.combination,
                draws=test_eval,
                system=system,
                profile=profile,
                recent_window=recent_window,
            )
            results.append(
                ValidationResult(
                    window_index=window_index,
                    combination=train_result.combination,
                    system=system,
                    profile_name=profile.name,
                    search_mode=search_mode,
                    train_start=train_draws[0],
                    train_end=train_draws[-1],
                    test_start=test_draws[0],
                    test_end=test_draws[-1],
                    train_result=train_result,
                    test_result=test_result,
                )
            )

        start += step_size
        window_index += 1

    return results


def resolve_validation_pool(
    draws: Sequence[Draw],
    picked_numbers: int,
    max_combinations: int,
    pool_size: int,
) -> tuple[tuple[int, ...] | None, str]:
    full_count = comb(MAX_NUMBER - MIN_NUMBER + 1, picked_numbers)
    if picked_numbers <= EXACT_PICK_LIMIT and full_count <= max_combinations:
        return None, "exact"
    if pool_size < picked_numbers:
        raise ValueError("pool size must be at least picked numbers")

    pool_count = comb(pool_size, picked_numbers)
    if pool_count > max_combinations:
        raise ValueError(
            f"Top-frequency pool would evaluate {pool_count:,} combinations; "
            "reduce pool size or raise max-combinations"
        )
    return top_frequency_pool(draws, pool_size), f"top-{pool_size}"


def top_frequency_pool(draws: Sequence[Draw], pool_size: int) -> tuple[int, ...]:
    counts: Counter[int] = Counter()
    for draw in draws:
        counts.update(draw.numbers)
    ranked = sorted(range(MIN_NUMBER, MAX_NUMBER + 1), key=lambda number: (-counts[number], number))
    return tuple(sorted(ranked[:pool_size]))
