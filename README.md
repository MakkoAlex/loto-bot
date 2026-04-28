# Loto Bot

Loto Bot is a local Python analyzer for Loto Polonia Multi draw history. It fetches the public archive, backtests direct or expanded systems, and ranks number combinations by historical gross return, cost, profit, ROI, hit rate, and losing streaks.

This is a historical analyzer, not a guarantee of future results.

## Install

```powershell
python -m pip install -e .
```

## Fetch Draw History

```powershell
python -m loto_bot.cli fetch --output data/draws.json
```

## Analyze One System

```powershell
python -m loto_bot.cli analyze --draws data/draws.json --system 3/5 --top 20 --csv reports/best_3_5.csv --json reports/best_3_5.json
```

## Compare Systems

```powershell
python -m loto_bot.cli systems --draws data/draws.json --systems 2/2 2/5 3/3 3/5 3/6 --top 20 --csv reports/best_systems.csv --json reports/best_systems.json
```

## Validate A Pattern

```powershell
python -m loto_bot.cli validate --draws data/draws.json --system 3/3 --train-window 3000 --test-window 300 --candidates 3 --csv reports/validation_3_3.csv --json reports/validation_3_3.json
```

Validation trains on older draws, chooses the best historical candidates, then tests those exact combinations on the next future window. This is the main command for checking whether a pattern survives outside the period that found it.

Small searches run exactly across numbers `1..80`. Very large searches automatically use a top-frequency pool, `14` numbers by default, so systems like `3/6` can finish locally. Increase `--max-combinations` or adjust `--pool-size` to control that tradeoff.

## Payout Defaults

- `system_2`: cost `3.00 RON`, returns `3.77 RON` for `1/2`, `22.54 RON` for `2/2`
- `system_3`: cost `7.00 RON`, returns `3.77 RON` for `1/3`, `22.54 RON` for `2/3`, `121.00 RON` for `3/3`

For expanded systems, cost and return are summed across all sub-tickets. For example, `3/5` evaluates all ten 3-number sub-tickets inside the selected five numbers.
