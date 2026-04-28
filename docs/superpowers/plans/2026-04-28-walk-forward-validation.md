# Walk-Forward Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `validate` command that trains on older draw windows and tests selected combinations on future unseen windows.

**Architecture:** Create a pure `validation.py` module that depends on existing backtest and payout logic. Extend the CLI and reporting module with validation-specific rows and a compact terminal table.

**Tech Stack:** Python stdlib, existing `loto_bot` package modules, pytest.

---

## Task 1: Validation Engine

**Files:**
- Create: `src/loto_bot/validation.py`
- Create: `tests/test_validation.py`

- [ ] Write a failing test for one walk-forward window where `2/2` training selects `(1, 2)` and future test metrics are calculated on unseen draws.
- [ ] Run `python -m pytest tests/test_validation.py -v` and confirm it fails because `loto_bot.validation` is missing.
- [ ] Implement `ValidationResult` and `walk_forward_validate`.
- [ ] Run `python -m pytest tests/test_validation.py -v` and confirm it passes.

## Task 2: CLI And Reports

**Files:**
- Modify: `src/loto_bot/cli.py`
- Modify: `src/loto_bot/reporting.py`
- Modify: `tests/test_reporting_cli.py`
- Modify: `README.md`

- [ ] Write a failing CLI test for `main(["validate", ...])` against a local draw cache.
- [ ] Run the focused CLI test and confirm it fails because `validate` is not registered.
- [ ] Add the `validate` subcommand, validation rows, CSV/JSON exports, and terminal table.
- [ ] Run the focused CLI test and confirm it passes.

## Task 3: Verification And Report

**Files:**
- Modify only if verification finds issues.

- [ ] Run `python -m pytest -v`.
- [ ] Run `python -m compileall src tests`.
- [ ] Run `python -m loto_bot.cli validate --draws data/draws.json --system 3/3 --train-window 3000 --test-window 300 --candidates 3 --csv reports/validation_3_3.csv --json reports/validation_3_3.json`.
- [ ] Commit and push the feature.
