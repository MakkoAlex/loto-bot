from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from loto_bot.models import DRAW_DATE_FORMAT, Draw, parse_archive_row

ARCHIVE_ENDPOINT = "https://www.lotopolonia.com/fetch_arhiva.php"
USER_AGENT = "loto-bot/0.1 (+https://github.com/MakkoAlex/loto-bot)"

GetJson = Callable[[str, float], object]


def fetch_archive(
    limit: int = 500,
    timeout: float = 30.0,
    get_json: GetJson | None = None,
) -> list[Draw]:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    json_loader = get_json or default_get_json
    offset = 0
    draws: list[Draw] = []

    while True:
        url = f"{ARCHIVE_ENDPOINT}?offset={offset}&limit={limit}"
        payload = json_loader(url, timeout)
        if not isinstance(payload, list):
            raise RuntimeError(f"Expected archive JSON list from {url}")

        rows = [_ensure_mapping(row, url) for row in payload]
        draws.extend(parse_archive_row(row) for row in rows)

        if len(rows) < limit:
            break
        offset += limit

    return draws


def default_get_json(url: str, timeout: float) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to fetch archive JSON from {url}: {exc}") from exc


def save_draws(draws: Iterable[Draw], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "date": draw.drawn_at.strftime(DRAW_DATE_FORMAT),
            "numbers": ", ".join(str(number) for number in sorted(draw.numbers)),
        }
        for draw in draws
    ]
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def load_draws(path: str | Path) -> list[Draw]:
    input_path = Path(path)
    with input_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"Draw cache must contain a list: {input_path}")
    return [parse_archive_row(_ensure_mapping(row, str(input_path))) for row in payload]


def _ensure_mapping(row: object, source: str) -> Mapping[str, object]:
    if not isinstance(row, Mapping):
        raise RuntimeError(f"Invalid archive row from {source}: expected object")
    return row
