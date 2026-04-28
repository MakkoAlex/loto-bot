# Loto Polonia Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that fetches Loto Polonia draw history and ranks direct or expanded betting systems by historical cost, return, profit, ROI, hit rate, and losing streaks.

**Architecture:** Use a small `src/loto_bot` package with immutable models, data-driven payout profiles, pure backtesting functions, and a thin `argparse` CLI. Tests use small deterministic fixtures and mock HTTP responses so automated verification never depends on the live website.

**Tech Stack:** Python 3.11+, stdlib `argparse`, `csv`, `json`, `urllib`; pytest for tests; setuptools build metadata in `pyproject.toml`.

---

## File Structure

- Create `pyproject.toml`: package metadata, CLI entry point, pytest/ruff config.
- Create `README.md`: install, fetch, analyze, and systems usage.
- Create `src/loto_bot/__init__.py`: package version.
- Create `src/loto_bot/models.py`: frozen dataclasses for `Draw`, `PayoutProfile`, `BacktestResult`, and archive parsing.
- Create `src/loto_bot/payouts.py`: default payout profiles and system parsing.
- Create `src/loto_bot/backtest.py`: pure hit counting, direct-ticket evaluation, expanded-ticket evaluation, metrics, and sorting.
- Create `src/loto_bot/fetcher.py`: archive pagination, validation, JSON cache read/write.
- Create `src/loto_bot/reporting.py`: terminal table plus CSV/JSON exports.
- Create `src/loto_bot/cli.py`: `fetch`, `analyze`, and `systems` commands.
- Create `data/.gitkeep` and `reports/.gitkeep`: local output directories.
- Create `tests/test_models.py`: draw parsing and validation tests.
- Create `tests/test_payouts.py`: payout profile and system parser tests.
- Create `tests/test_backtest.py`: direct and expanded ROI tests.
- Create `tests/test_fetcher.py`: mocked pagination and cache tests.
- Create `tests/test_reporting_cli.py`: report and CLI smoke tests.

## Task 1: Project Skeleton And Draw Models

**Files:**
- Create: `pyproject.toml`
- Create: `src/loto_bot/__init__.py`
- Create: `src/loto_bot/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

```python
from datetime import datetime

import pytest

from loto_bot.models import Draw, parse_archive_row


def test_parse_archive_row_returns_validated_draw():
    draw = parse_archive_row(
        {
            "date": "2026-04-28 15:00:00",
            "numbers": "1, 8, 9, 10, 17, 18, 22, 23, 26, 27, 29, 41, 53, 59, 60, 61, 62, 66, 69, 77",
        }
    )

    assert draw == Draw(
        drawn_at=datetime(2026, 4, 28, 15, 0, 0),
        numbers=frozenset({1, 8, 9, 10, 17, 18, 22, 23, 26, 27, 29, 41, 53, 59, 60, 61, 62, 66, 69, 77}),
    )


def test_parse_archive_row_rejects_duplicate_numbers():
    numbers = "1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19"

    with pytest.raises(ValueError, match="20 unique numbers"):
        parse_archive_row({"date": "2026-04-28 15:00:00", "numbers": numbers})


def test_parse_archive_row_rejects_out_of_range_numbers():
    numbers = "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 81"

    with pytest.raises(ValueError, match="1..80"):
        parse_archive_row({"date": "2026-04-28 15:00:00", "numbers": numbers})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`

Expected: FAIL because `loto_bot.models` does not exist.

- [ ] **Step 3: Implement package skeleton and model parsing**

Implement:

```python
@dataclass(frozen=True)
class Draw:
    drawn_at: datetime
    numbers: frozenset[int]


def parse_archive_row(row: Mapping[str, object]) -> Draw:
    ...
```

Validation:

- Date format is `%Y-%m-%d %H:%M:%S`
- Exactly 20 unique numbers
- Every number is from 1 through 80

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`

Expected: PASS.

## Task 2: Payout Profiles And System Parsing

**Files:**
- Create: `src/loto_bot/payouts.py`
- Modify: `src/loto_bot/models.py`
- Create: `tests/test_payouts.py`

- [ ] **Step 1: Write failing payout tests**

```python
import pytest

from loto_bot.payouts import DEFAULT_PROFILES, parse_system


def test_system_3_returns_gross_values_by_hit_count():
    profile = DEFAULT_PROFILES["system_3"]

    assert profile.return_for_hits(0) == 0.0
    assert profile.return_for_hits(1) == 3.77
    assert profile.return_for_hits(2) == 22.54
    assert profile.return_for_hits(3) == 121.0


def test_system_3_profit_subtracts_cost():
    profile = DEFAULT_PROFILES["system_3"]

    assert profile.profit_for_hits(2) == pytest.approx(15.54)


def test_parse_system_accepts_valid_text():
    system = parse_system("3/5")

    assert system.required_hits == 3
    assert system.picked_numbers == 5


def test_parse_system_rejects_impossible_text():
    with pytest.raises(ValueError, match="required hits"):
        parse_system("6/5")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_payouts.py -v`

Expected: FAIL because payout code does not exist.

- [ ] **Step 3: Implement payout profiles**

Implement frozen dataclasses:

```python
@dataclass(frozen=True)
class PayoutProfile:
    name: str
    ticket_size: int
    cost: float
    returns_by_hits: Mapping[int, float]


@dataclass(frozen=True)
class BettingSystem:
    required_hits: int
    picked_numbers: int
```

Defaults:

- `system_2`: cost `3.0`, returns `{1: 3.77, 2: 22.54}`
- `system_3`: cost `7.0`, returns `{1: 3.77, 2: 22.54, 3: 121.0}`
- `straight_1`: cost `1.0`, returns `{1: 3.77}`
- `straight_2`: cost `1.0`, returns `{2: 15.0}`
- `straight_3`: cost `1.0`, returns `{3: 65.0}`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_payouts.py -v`

Expected: PASS.

## Task 3: Backtesting Direct And Expanded Systems

**Files:**
- Create: `src/loto_bot/backtest.py`
- Create: `tests/test_backtest.py`

- [ ] **Step 1: Write failing backtest tests**

```python
from datetime import datetime

import pytest

from loto_bot.backtest import backtest_combination, rank_combinations
from loto_bot.models import Draw
from loto_bot.payouts import DEFAULT_PROFILES, parse_system


def make_draw(day: int, numbers: set[int]) -> Draw:
    return Draw(drawn_at=datetime(2026, 1, day, 15, 0, 0), numbers=frozenset(numbers))


def test_backtest_direct_system_calculates_money_metrics():
    draws = [
        make_draw(1, {1, 2, *range(10, 28)}),
        make_draw(2, {1, *range(10, 29)}),
        make_draw(3, set(range(10, 30))),
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


def test_backtest_expanded_system_sums_sub_ticket_costs_and_returns():
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


def test_rank_combinations_sorts_by_roi_then_profit_then_numbers():
    draws = [
        make_draw(1, {1, 2, *range(10, 28)}),
        make_draw(2, {3, 4, *range(10, 28)}),
    ]

    results = rank_combinations(
        draws=draws,
        system=parse_system("2/2"),
        profile=DEFAULT_PROFILES["system_2"],
        max_combinations=10_000,
    )

    assert results[0].combination == (1, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backtest.py -v`

Expected: FAIL because `loto_bot.backtest` does not exist.

- [ ] **Step 3: Implement backtest logic**

Implement:

- `hit_count(combination, draw)`
- `expanded_tickets(combination, ticket_size)`
- `backtest_combination(combination, draws, system, profile, recent_window=100)`
- `rank_combinations(draws, system, profile, top=50, recent_window=100, max_combinations=1_000_000)`

Expanded model:

- If `picked_numbers == profile.ticket_size`, evaluate one ticket.
- If `picked_numbers > profile.ticket_size`, evaluate every `itertools.combinations(combination, profile.ticket_size)`.
- Per draw cost is `len(sub_tickets) * profile.cost`.
- Per draw return is the sum of `profile.return_for_hits(hit_count(sub_ticket, draw))`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backtest.py -v`

Expected: PASS.

## Task 4: Archive Fetching And Cache

**Files:**
- Create: `src/loto_bot/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write failing fetcher tests**

```python
from datetime import datetime

from loto_bot.fetcher import fetch_archive, load_draws, save_draws


def test_fetch_archive_pages_until_short_page():
    calls = []

    def fake_get_json(url: str, timeout: float):
        calls.append(url)
        if "offset=0" in url:
            return [
                {"date": "2026-04-28 15:00:00", "numbers": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20"},
                {"date": "2026-04-27 15:00:00", "numbers": "2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21"},
            ]
        return [
            {"date": "2026-04-26 15:00:00", "numbers": "3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22"}
        ]

    draws = fetch_archive(limit=2, get_json=fake_get_json)

    assert len(draws) == 3
    assert calls == [
        "https://www.lotopolonia.com/fetch_arhiva.php?offset=0&limit=2",
        "https://www.lotopolonia.com/fetch_arhiva.php?offset=2&limit=2",
    ]


def test_save_and_load_draws_round_trip(tmp_path):
    draws = fetch_archive(
        limit=1,
        get_json=lambda url, timeout: [
            {"date": "2026-04-28 15:00:00", "numbers": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20"}
        ]
        if "offset=0" in url
        else [],
    )
    path = tmp_path / "draws.json"

    save_draws(draws, path)
    loaded = load_draws(path)

    assert loaded[0].drawn_at == datetime(2026, 4, 28, 15, 0, 0)
    assert loaded[0].numbers == frozenset(range(1, 21))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fetcher.py -v`

Expected: FAIL because `loto_bot.fetcher` does not exist.

- [ ] **Step 3: Implement fetcher and cache helpers**

Implement:

- `fetch_archive(limit=500, timeout=30.0, get_json=None)`
- `default_get_json(url, timeout)`
- `save_draws(draws, path)`
- `load_draws(path)`

Use `urllib.request` with a user agent. Raise `RuntimeError` with URL context on network or JSON errors.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_fetcher.py -v`

Expected: PASS.

## Task 5: Reporting And CLI

**Files:**
- Create: `src/loto_bot/reporting.py`
- Create: `src/loto_bot/cli.py`
- Create: `tests/test_reporting_cli.py`
- Create: `README.md`
- Create: `data/.gitkeep`
- Create: `reports/.gitkeep`

- [ ] **Step 1: Write failing reporting and CLI tests**

```python
import csv
import json
from datetime import datetime

from loto_bot.cli import main
from loto_bot.fetcher import save_draws
from loto_bot.models import Draw
from loto_bot.reporting import write_csv, write_json


def test_write_reports_include_money_metrics(tmp_path):
    draws_path = tmp_path / "draws.json"
    save_draws([Draw(datetime(2026, 1, 1, 15, 0, 0), frozenset(range(1, 21)))], draws_path)

    assert main(["analyze", "--draws", str(draws_path), "--system", "2/2", "--top", "3"]) == 0


def test_csv_and_json_reports(tmp_path):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reporting_cli.py -v`

Expected: FAIL because reporting and CLI code does not exist.

- [ ] **Step 3: Implement reporting and CLI**

Implement:

- `result_to_dict(result, system_text)`
- `write_csv(rows, path)`
- `write_json(rows, path)`
- `print_table(rows, limit)`
- `main(argv=None)`

CLI commands:

- `fetch --output data/draws.json --limit 500`
- `analyze --draws data/draws.json --system 3/5 --top 50 --recent-window 100 --csv reports/best.csv --json reports/best.json`
- `systems --draws data/draws.json --systems 2/2 2/5 3/3 3/5 3/6 --top 20`

For `analyze`, infer the payout profile from the required hits in the system: `2/x` uses `system_2`, `3/x` uses `system_3`, `1/1` uses `straight_1`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reporting_cli.py -v`

Expected: PASS.

## Task 6: Full Verification And First Real Report

**Files:**
- Modify: files from earlier tasks only if verification finds issues.

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Run CLI help**

Run: `python -m loto_bot.cli --help`

Expected: CLI prints commands `fetch`, `analyze`, and `systems`.

- [ ] **Step 3: Run live fetch smoke test**

Run: `python -m loto_bot.cli fetch --output data/draws.json --limit 1000`

Expected: writes current archive cache and prints draw count.

- [ ] **Step 4: Run first analyzer report**

Run: `python -m loto_bot.cli systems --draws data/draws.json --systems 2/2 2/5 3/3 3/5 3/6 --top 10 --csv reports/best_systems.csv --json reports/best_systems.json`

Expected: writes reports and prints ranked money metrics.

- [ ] **Step 5: Run lint-style checks**

Run: `python -m compileall src tests`

Expected: exit code 0.

- [ ] **Step 6: Commit implementation**

```bash
git add pyproject.toml README.md src tests data/.gitkeep reports/.gitkeep docs/superpowers/plans/2026-04-28-loto-polonia-analyzer.md
git commit -m "feat: add loto polonia analyzer"
```
