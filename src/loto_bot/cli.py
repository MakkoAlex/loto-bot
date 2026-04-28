from __future__ import annotations

import argparse
from collections import Counter
from math import comb
from pathlib import Path
from typing import Sequence

from loto_bot.backtest import rank_combinations
from loto_bot.fetcher import fetch_archive, load_draws, save_draws
from loto_bot.models import MAX_NUMBER, MIN_NUMBER, Draw
from loto_bot.payouts import DEFAULT_PROFILES, BettingSystem, PayoutProfile, parse_system
from loto_bot.reporting import print_table, result_to_dict, write_csv, write_json

DEFAULT_SYSTEMS = ["2/2", "2/5", "3/3", "3/5", "3/6"]
EXACT_PICK_LIMIT = 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loto-bot")
    subparsers = parser.add_subparsers(required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Download the Loto Polonia archive")
    fetch_parser.add_argument("--output", default="data/draws.json")
    fetch_parser.add_argument("--limit", type=int, default=500, help="Archive page size")
    fetch_parser.add_argument("--timeout", type=float, default=30.0)
    fetch_parser.set_defaults(func=run_fetch)

    analyze_parser = subparsers.add_parser("analyze", help="Rank combinations for one system")
    add_analysis_arguments(analyze_parser)
    analyze_parser.add_argument("--system", required=True)
    analyze_parser.set_defaults(func=run_analyze)

    systems_parser = subparsers.add_parser("systems", help="Compare several systems")
    add_analysis_arguments(systems_parser)
    systems_parser.add_argument("--systems", nargs="+", default=DEFAULT_SYSTEMS)
    systems_parser.set_defaults(func=run_systems)

    return parser


def add_analysis_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--draws", default="data/draws.json")
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--recent-window", type=int, default=100)
    parser.add_argument("--max-combinations", type=int, default=1_000_000)
    parser.add_argument(
        "--pool-size",
        type=int,
        default=14,
        help="Use top-frequency pool when a full search is too large",
    )
    parser.add_argument("--csv")
    parser.add_argument("--json")


def run_fetch(args: argparse.Namespace) -> int:
    draws = fetch_archive(limit=args.limit, timeout=args.timeout)
    save_draws(draws, args.output)
    print(f"Saved {len(draws)} draws to {args.output}")
    return 0


def run_analyze(args: argparse.Namespace) -> int:
    draws = load_draws(args.draws)
    system = parse_system(args.system)
    rows = _rank_system(draws=draws, system=system, args=args)
    _write_outputs(rows, args)
    print_table(rows, args.top)
    return 0


def run_systems(args: argparse.Namespace) -> int:
    draws = load_draws(args.draws)
    rows: list[dict[str, object]] = []
    for system_text in args.systems:
        system = parse_system(system_text)
        rows.extend(_rank_system(draws=draws, system=system, args=args))
    rows.sort(key=lambda row: (-float(row["score"]), -float(row["roi"]), -float(row["profit"])))
    _write_outputs(rows, args)
    print_table(rows, args.top)
    return 0


def _rank_system(
    draws: Sequence[Draw],
    system: BettingSystem,
    args: argparse.Namespace,
) -> list[dict[str, object]]:
    profile = infer_profile(system)
    number_pool, search_mode = resolve_number_pool(
        draws=draws,
        picked_numbers=system.picked_numbers,
        max_combinations=args.max_combinations,
        pool_size=args.pool_size,
    )
    results = rank_combinations(
        draws=draws,
        system=system,
        profile=profile,
        top=args.top,
        recent_window=args.recent_window,
        max_combinations=args.max_combinations,
        number_pool=number_pool,
    )
    return [result_to_dict(result, system_text=system.text, search_mode=search_mode) for result in results]


def infer_profile(system: BettingSystem) -> PayoutProfile:
    if system.required_hits == 1 and system.picked_numbers == 1:
        return DEFAULT_PROFILES["straight_1"]
    if system.required_hits == 2:
        return DEFAULT_PROFILES["system_2"]
    if system.required_hits == 3:
        return DEFAULT_PROFILES["system_3"]
    raise ValueError(f"No default payout profile for system {system.text}")


def resolve_number_pool(
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


def _write_outputs(rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    if args.csv:
        write_csv(rows, Path(args.csv))
    if args.json:
        write_json(rows, Path(args.json))


if __name__ == "__main__":
    raise SystemExit(main())
