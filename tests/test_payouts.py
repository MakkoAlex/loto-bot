import pytest

from loto_bot.payouts import DEFAULT_PROFILES, parse_system


def test_system_3_returns_gross_values_by_hit_count() -> None:
    profile = DEFAULT_PROFILES["system_3"]

    assert profile.return_for_hits(0) == 0.0
    assert profile.return_for_hits(1) == 3.77
    assert profile.return_for_hits(2) == 22.54
    assert profile.return_for_hits(3) == 121.0


def test_system_3_profit_subtracts_cost() -> None:
    profile = DEFAULT_PROFILES["system_3"]

    assert profile.profit_for_hits(2) == pytest.approx(15.54)


def test_parse_system_accepts_valid_text() -> None:
    system = parse_system("3/5")

    assert system.required_hits == 3
    assert system.picked_numbers == 5


def test_parse_system_rejects_impossible_text() -> None:
    with pytest.raises(ValueError, match="required hits"):
        parse_system("6/5")
