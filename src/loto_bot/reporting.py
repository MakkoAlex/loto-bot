from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from loto_bot.backtest import BacktestResult
from loto_bot.validation import ValidationResult


def result_to_dict(
    result: BacktestResult,
    system_text: str | None = None,
    search_mode: str = "exact",
) -> dict[str, Any]:
    return {
        "combination": list(result.combination),
        "system": system_text or result.system.text,
        "profile": result.profile_name,
        "search_mode": search_mode,
        "ticket_count": result.ticket_count,
        "draw_count": result.draw_count,
        "total_cost": round(result.total_cost, 2),
        "total_return": round(result.total_return, 2),
        "profit": round(result.profit, 2),
        "roi": round(result.roi, 6),
        "hit_rate_at_least_2": round(result.hit_rate_at_least_2, 6),
        "longest_losing_streak": result.longest_losing_streak,
        "recent_cost": round(result.recent_cost, 2),
        "recent_return": round(result.recent_return, 2),
        "recent_profit": round(result.recent_profit, 2),
        "recent_roi": round(result.recent_roi, 6),
        "last_profitable_hit_date": result.last_profitable_hit_date.isoformat(sep=" ")
        if result.last_profitable_hit_date
        else "",
        "score": round(result.score, 6),
        "hit_counts": result.hit_counts,
    }


def validation_result_to_dict(result: ValidationResult) -> dict[str, Any]:
    return {
        "window": result.window_index,
        "combination": list(result.combination),
        "system": result.system.text,
        "profile": result.profile_name,
        "search_mode": result.search_mode,
        "train_start": result.train_start.drawn_at.isoformat(sep=" "),
        "train_end": result.train_end.drawn_at.isoformat(sep=" "),
        "test_start": result.test_start.drawn_at.isoformat(sep=" "),
        "test_end": result.test_end.drawn_at.isoformat(sep=" "),
        "train_profit": round(result.train_result.profit, 2),
        "train_roi": round(result.train_result.roi, 6),
        "test_profit": round(result.test_result.profit, 2),
        "test_roi": round(result.test_result.roi, 6),
        "test_hit_rate_at_least_2": round(result.test_result.hit_rate_at_least_2, 6),
        "test_longest_losing_streak": result.test_result.longest_losing_streak,
        "test_total_cost": round(result.test_result.total_cost, 2),
        "test_total_return": round(result.test_result.total_return, 2),
    }


def write_csv(rows: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    row_list = [_serialize_for_csv(row) for row in rows]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(row_list[0].keys()) if row_list else []
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row_list)


def write_json(rows: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(list(rows), file, indent=2)


def print_table(rows: list[Mapping[str, Any]], limit: int) -> None:
    if not rows:
        print("No results.")
        return

    print(
        f"{'rank':>4}  {'system':<6}  {'numbers':<20}  {'profit':>12}  "
        f"{'roi':>10}  {'2+ hit %':>9}  {'max miss':>8}  {'mode':<12}"
    )
    for index, row in enumerate(rows[:limit], start=1):
        numbers = " ".join(str(number) for number in row["combination"])
        roi_pct = float(row["roi"]) * 100
        hit_pct = float(row.get("hit_rate_at_least_2", 0.0)) * 100
        print(
            f"{index:>4}  {str(row['system']):<6}  {numbers:<20}  "
            f"{float(row['profit']):>12.2f}  {roi_pct:>9.2f}%  "
            f"{hit_pct:>8.2f}%  {int(row.get('longest_losing_streak', 0)):>8}  "
            f"{str(row.get('search_mode', 'exact')):<12}"
        )


def print_validation_table(rows: list[Mapping[str, Any]], limit: int) -> None:
    if not rows:
        print("No validation windows.")
        return

    print(
        f"{'rank':>4}  {'win':>3}  {'system':<6}  {'numbers':<20}  "
        f"{'test profit':>12}  {'test roi':>10}  {'2+ hit %':>9}  {'mode':<8}"
    )
    ordered = sorted(rows, key=lambda row: (-float(row["test_roi"]), -float(row["test_profit"])))
    for index, row in enumerate(ordered[:limit], start=1):
        numbers = " ".join(str(number) for number in row["combination"])
        test_roi_pct = float(row["test_roi"]) * 100
        hit_pct = float(row.get("test_hit_rate_at_least_2", 0.0)) * 100
        print(
            f"{index:>4}  {int(row['window']):>3}  {str(row['system']):<6}  {numbers:<20}  "
            f"{float(row['test_profit']):>12.2f}  {test_roi_pct:>9.2f}%  "
            f"{hit_pct:>8.2f}%  {str(row.get('search_mode', 'exact')):<8}"
        )


def _serialize_for_csv(row: Mapping[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in row.items():
        if key == "combination" and isinstance(value, list):
            serialized[key] = " ".join(str(number) for number in value)
        elif isinstance(value, dict):
            serialized[key] = json.dumps(value, sort_keys=True)
        else:
            serialized[key] = value
    return serialized
