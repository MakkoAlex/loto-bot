# Walk-Forward Validation Design

## Purpose

Add a validation mode that checks whether historical lottery patterns survive on future unseen draws. This prevents the analyzer from only reporting combinations that looked good in hindsight.

The new mode answers:

- Which combinations looked best in a training window?
- What happened when those exact combinations were tested in the next future window?
- Did any system keep a positive or less-negative ROI out of sample?

## Approach

The command will use rolling walk-forward windows over chronological draws:

```text
oldest draws -> train window -> next future test window -> step forward -> repeat
```

For each window:

1. Use only the training draws to choose candidate combinations.
2. Rank training candidates with the existing payout-aware backtest engine.
3. Backtest the selected training candidates on the next future test window.
4. Report both training and test money metrics side by side.

For systems with 3 or more picked numbers, candidate pools must be selected from the training window only. Using all draws to select the pool would leak future information into the validation result.

## CLI

Add:

```powershell
python -m loto_bot.cli validate --draws data/draws.json --system 3/3 --train-window 3000 --test-window 300 --candidates 5 --csv reports/validation_3_3.csv --json reports/validation_3_3.json
```

Options:

- `--system`: one system such as `2/2`, `3/3`, `3/5`
- `--train-window`: number of older draws used to find candidates
- `--test-window`: number of future draws used for out-of-sample scoring
- `--step`: draw count to move between windows; defaults to `test-window`
- `--candidates`: number of top training candidates to test per window
- `--pool-size`: top-frequency training-only pool for large searches
- `--max-combinations`: safety cap for candidate searches
- `--csv` / `--json`: optional exports

## Output

Each row represents one candidate in one validation window:

- window number
- system
- combination
- train date range
- test date range
- train profit and ROI
- test profit and ROI
- test hit rate for at least 2 numbers
- test longest losing streak
- search mode, such as `exact` or `top-14`

The default table should emphasize test ROI and test profit because those are out-of-sample results.

## Testing

Add tests for:

- A deterministic tiny walk-forward validation window.
- Validation using training-only candidate selection.
- CLI `validate` running against a local cache.
- CSV/JSON exports containing validation-specific metrics.

No live network access is needed for validation tests.
