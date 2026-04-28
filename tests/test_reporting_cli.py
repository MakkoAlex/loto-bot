import csv
import json
from datetime import datetime

from loto_bot.cli import main
from loto_bot.cli import resolve_number_pool
from loto_bot.fetcher import save_draws
from loto_bot.models import Draw
from loto_bot.reporting import write_csv, write_json


def test_analyze_command_runs_against_local_draw_cache(tmp_path) -> None:
    draws_path = tmp_path / "draws.json"
    save_draws([Draw(datetime(2026, 1, 1, 15, 0, 0), frozenset(range(1, 21)))], draws_path)

    assert main(["analyze", "--draws", str(draws_path), "--system", "2/2", "--top", "3"]) == 0


def test_csv_and_json_reports(tmp_path) -> None:
    result = {
        "combination": [1, 2],
        "system": "2/2",
        "total_cost": 3.0,
        "total_return": 22.54,
        "profit": 19.54,
        "roi": 6.5133333333,
    }
    csv_path = tmp_path / "report.csv"
    json_path = tmp_path / "report.json"

    write_csv([result], csv_path)
    write_json([result], json_path)

    with csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    with json_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    assert rows[0]["combination"] == "1 2"
    assert payload[0]["profit"] == 19.54


def test_resolve_number_pool_uses_frequency_pool_for_three_number_searches() -> None:
    draws = [Draw(datetime(2026, 1, 1, 15, 0, 0), frozenset(range(1, 21)))]

    pool, search_mode = resolve_number_pool(
        draws=draws,
        picked_numbers=3,
        max_combinations=1_000_000,
        pool_size=5,
    )

    assert pool == (1, 2, 3, 4, 5)
    assert search_mode == "top-5"
