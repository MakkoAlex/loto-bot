# Loto Polonia Analyzer Design

## Purpose

Build a local Python analyzer for Loto Polonia Multi draws that downloads the full public archive, evaluates historical betting systems, and ranks combinations by money outcome. The first version is a command-line tool focused on expected historical value: gross returns, cost, profit, ROI, hit rate, losing streaks, and recent form.

The tool does not claim to predict guaranteed future lottery results. It uses historical backtesting to find combinations and systems that would have performed best under the payout rules provided by the user.

## Source Data

The archive page is `https://www.lotopolonia.com/arhiva-rezultate.php`.

The page loads draw data through the public JSON endpoint:

```text
https://www.lotopolonia.com/fetch_arhiva.php?offset=<offset>&limit=<limit>
```

Each row contains:

- `date`: draw timestamp as text, for example `2026-04-28 15:00:00`
- `numbers`: comma-separated list of 20 drawn numbers from `1` through `80`

Observed archive coverage during discovery:

- Latest observed draw: `2026-04-28 15:00:00`
- Oldest observed draw: `1996-03-18 01:00:00`
- Observed total rows: `16746`

The fetcher should page until the endpoint returns an empty result or fewer results than the requested page size.

## Betting Systems

A system is represented as:

```text
<required_hits>/<picked_numbers>
```

Examples:

- `2/5`: choose 5 numbers, count the bet as successful when at least 2 are drawn
- `3/5`: choose 5 numbers, count the bet as successful when at least 3 are drawn
- `3/6`: choose 6 numbers, count the bet as successful when at least 3 are drawn

The analyzer should also support payout tables where every hit tier can have a separate return amount. This matters because a system may return something even below the headline threshold, such as a 3-number system returning money for `1/3`.

For expanded systems such as `3/5` and `3/6`, the first version will use an expanded-ticket model:

- `3/5` means choose 5 numbers and evaluate every 3-number sub-combination inside those 5 numbers using the `system_3` payout profile.
- `3/6` means choose 6 numbers and evaluate every 3-number sub-combination inside those 6 numbers using the `system_3` payout profile.
- `2/5` means choose 5 numbers and evaluate every 2-number sub-combination inside those 5 numbers using the `system_2` payout profile.

Cost and return are summed across all expanded sub-tickets. For example, with the provided `system_3` cost of `7.00 RON`, a `3/5` expanded system contains `10` three-number sub-tickets, so one draw costs `70.00 RON` unless the user later provides a different official cost table.

## Provided Payout Rules

The first version will include these payout profiles as defaults. Returns are gross returns, not profit.

### Straight Bets

| Profile | Cost | Hit tier | Gross return |
| --- | ---: | ---: | ---: |
| `straight_1` | configurable | 1/1 | stake x 3.77 |
| `straight_2` | configurable | 2/2 | stake x 15 |
| `straight_3` | configurable | 3/3 | stake x 65 |

### System Bets

| Profile | Cost | Hit tier | Gross return |
| --- | ---: | ---: | ---: |
| `system_2` | 3.00 RON | 1/2 | 3.77 RON |
| `system_2` | 3.00 RON | 2/2 | 22.54 RON |
| `system_3` | 7.00 RON | 1/3 | 3.77 RON |
| `system_3` | 7.00 RON | 2/3 | 22.54 RON |
| `system_3` | 7.00 RON | 3/3 | 121.00 RON |

The payout model should be data-driven so more systems can be added later without rewriting analyzer logic.

Expanded systems derive their cost from the underlying payout profile and the number of generated sub-tickets. This keeps the first version usable with the payout data currently available while allowing official expanded-system costs to replace this derived model later.

## Ranking Goal

The default goal is to maximize historical money outcome while keeping the user's practical target in mind: hitting at least 2 numbers.

Primary metrics:

- `total_cost`: number of evaluated draws multiplied by bet cost
- `total_return`: sum of gross returns across all evaluated draws
- `profit`: `total_return - total_cost`
- `roi`: `profit / total_cost`
- `hit_counts`: number of draws with exactly 0, 1, 2, 3, etc. hits
- `hit_rate_at_least_2`: percentage of draws with at least 2 hits
- `longest_losing_streak`: longest run of draws with no profitable return
- `recent_profit`: profit over the newest configurable draw window
- `last_profitable_hit_date`: most recent draw where return exceeded cost

Default ranking score:

```text
score = roi + recent_roi_weight - losing_streak_penalty
```

The report must still show raw ROI and profit so the user can sort by pure money outcome instead of the blended score.

## Architecture

The project will be a small Python package with a CLI. Data fetching, parsing, analysis, payout rules, and reporting will be separated so each part is testable.

Planned package layout:

```text
pyproject.toml
README.md
src/loto_bot/
  __init__.py
  analyzer.py
  backtest.py
  cli.py
  fetcher.py
  models.py
  payouts.py
  reporting.py
data/
  .gitkeep
reports/
  .gitkeep
tests/
  test_analyzer.py
  test_backtest.py
  test_fetcher.py
  test_payouts.py
```

## Components

### Fetcher

Responsibilities:

- Download archive rows from `fetch_arhiva.php`
- Page through the archive using `offset` and `limit`
- Parse draw dates and drawn numbers
- Validate that each draw has 20 unique numbers in range `1..80`
- Save local cache as JSON
- Avoid silently swallowing network or parsing errors

The fetcher should use a polite default page size, configurable timeout, and a user agent string that identifies the local tool.

### Models

Responsibilities:

- Represent immutable draw data
- Represent payout profiles
- Represent backtest results
- Keep validation close to data boundaries

Data containers should use `@dataclass(frozen=True)`.

### Payouts

Responsibilities:

- Define default payout profiles
- Calculate gross return for a given hit count
- Calculate profit for one draw as `gross_return - cost`
- Allow future custom payout profiles loaded from config

### Analyzer

Responsibilities:

- Generate number combinations for a requested pick size
- Generate expanded sub-ticket combinations for systems such as `3/5`
- Count hits against every historical draw
- Aggregate hit distribution and performance metrics
- Support ranking by ROI, profit, at-least-2 hit rate, recent ROI, and blended score

Because combinations can explode quickly, the first version should support pick sizes from 1 to 6 by default and expose a clear error when the requested search is too large.

### Backtest

Responsibilities:

- Run a payout profile over historical draws for each candidate combination
- Run expanded systems by summing the cost and return of all underlying sub-tickets
- Calculate total cost, return, profit, ROI, losing streaks, and recent-window stats
- Produce deterministic results sorted by requested metric

### Reporting

Responsibilities:

- Print human-readable top results in the terminal
- Export CSV and JSON reports
- Include enough detail to understand why a combination ranked highly

### CLI

Initial commands:

```text
loto-bot fetch --output data/draws.json
loto-bot analyze --draws data/draws.json --profile system_3 --picks 3 --top 50
loto-bot analyze --draws data/draws.json --system 3/5 --top 50
loto-bot systems --draws data/draws.json --systems 2/2 2/5 3/3 3/5 3/6 --top 50
```

The `analyze` command should default to a money-aware ranking and show combinations that historically produced the best ROI/profit. The `systems` command should compare several direct or expanded systems.

## Error Handling

- Network failures should include URL, offset, and timeout context in logs or exception messages.
- Invalid archive rows should fail loudly with row details.
- Invalid systems, such as required hits greater than picked numbers, should return a clear CLI error.
- Oversized brute-force searches should return a clear message explaining the combination count and suggested smaller pick size.

## Testing

Testing follows TDD.

Unit tests:

- Parse valid archive rows into immutable draw objects
- Reject invalid draw rows with duplicate, missing, or out-of-range numbers
- Calculate payout returns and profits for every provided payout tier
- Calculate expanded-system cost and return for `2/5`, `3/5`, and `3/6`
- Count hits for known candidate combinations
- Calculate ROI, profit, hit distribution, and losing streaks from tiny hand-built draw sets
- Sort rankings deterministically

Integration-style tests:

- Mock the archive endpoint and verify pagination stops correctly
- Verify CSV/JSON report shape for a small known result set
- Verify CLI commands run against local fixture data

Live network access should not be required for automated tests.

## Non-Goals For First Version

- No guaranteed predictions
- No web dashboard
- No paid betting automation
- No account login or scraping behind authentication
- No uncontrolled exhaustive searches for very large pick sizes

## Approval Notes

The user confirmed that provided payout values are gross returns. Profit is therefore calculated by subtracting the stake or system cost from the gross return.
