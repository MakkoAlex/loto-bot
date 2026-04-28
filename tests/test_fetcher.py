from datetime import datetime

from loto_bot.fetcher import fetch_archive, load_draws, save_draws


def test_fetch_archive_pages_until_short_page() -> None:
    calls = []

    def fake_get_json(url: str, timeout: float) -> list[dict[str, str]]:
        calls.append(url)
        if "offset=0" in url:
            return [
                {
                    "date": "2026-04-28 15:00:00",
                    "numbers": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20",
                },
                {
                    "date": "2026-04-27 15:00:00",
                    "numbers": "2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21",
                },
            ]
        return [
            {
                "date": "2026-04-26 15:00:00",
                "numbers": "3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22",
            }
        ]

    draws = fetch_archive(limit=2, get_json=fake_get_json)

    assert len(draws) == 3
    assert calls == [
        "https://www.lotopolonia.com/fetch_arhiva.php?offset=0&limit=2",
        "https://www.lotopolonia.com/fetch_arhiva.php?offset=2&limit=2",
    ]


def test_save_and_load_draws_round_trip(tmp_path) -> None:
    draws = fetch_archive(
        limit=1,
        get_json=lambda url, timeout: [
            {
                "date": "2026-04-28 15:00:00",
                "numbers": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20",
            }
        ]
        if "offset=0" in url
        else [],
    )
    path = tmp_path / "draws.json"

    save_draws(draws, path)
    loaded = load_draws(path)

    assert loaded[0].drawn_at == datetime(2026, 4, 28, 15, 0, 0)
    assert loaded[0].numbers == frozenset(range(1, 21))
