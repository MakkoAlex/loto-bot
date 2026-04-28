from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class PayoutProfile:
    name: str
    ticket_size: int
    cost: float
    returns_by_hits: Mapping[int, float]

    def __post_init__(self) -> None:
        if self.ticket_size < 1:
            raise ValueError("ticket size must be at least 1")
        if self.cost <= 0:
            raise ValueError("cost must be positive")
        if not self.returns_by_hits:
            raise ValueError("returns by hits cannot be empty")
        invalid_hits = [hits for hits in self.returns_by_hits if hits < 1 or hits > self.ticket_size]
        if invalid_hits:
            raise ValueError(f"return tiers must be within 1..{self.ticket_size}: {invalid_hits}")
        object.__setattr__(self, "returns_by_hits", MappingProxyType(dict(self.returns_by_hits)))

    def return_for_hits(self, hits: int) -> float:
        return float(self.returns_by_hits.get(hits, 0.0))

    def profit_for_hits(self, hits: int) -> float:
        return self.return_for_hits(hits) - self.cost


@dataclass(frozen=True)
class BettingSystem:
    required_hits: int
    picked_numbers: int

    def __post_init__(self) -> None:
        if self.required_hits < 1:
            raise ValueError("required hits must be at least 1")
        if self.picked_numbers < 1:
            raise ValueError("picked numbers must be at least 1")
        if self.required_hits > self.picked_numbers:
            raise ValueError("required hits cannot exceed picked numbers")

    @property
    def text(self) -> str:
        return f"{self.required_hits}/{self.picked_numbers}"


DEFAULT_PROFILES: Mapping[str, PayoutProfile] = MappingProxyType(
    {
        "system_2": PayoutProfile(
            name="system_2",
            ticket_size=2,
            cost=3.0,
            returns_by_hits={1: 3.77, 2: 22.54},
        ),
        "system_3": PayoutProfile(
            name="system_3",
            ticket_size=3,
            cost=7.0,
            returns_by_hits={1: 3.77, 2: 22.54, 3: 121.0},
        ),
        "straight_1": PayoutProfile(
            name="straight_1",
            ticket_size=1,
            cost=1.0,
            returns_by_hits={1: 3.77},
        ),
        "straight_2": PayoutProfile(
            name="straight_2",
            ticket_size=2,
            cost=1.0,
            returns_by_hits={2: 15.0},
        ),
        "straight_3": PayoutProfile(
            name="straight_3",
            ticket_size=3,
            cost=1.0,
            returns_by_hits={3: 65.0},
        ),
    }
)


def parse_system(text: str) -> BettingSystem:
    parts = text.strip().split("/")
    if len(parts) != 2:
        raise ValueError("System must use '<required_hits>/<picked_numbers>' format")

    try:
        required_hits = int(parts[0])
        picked_numbers = int(parts[1])
    except ValueError as exc:
        raise ValueError("System values must be integers") from exc

    return BettingSystem(required_hits=required_hits, picked_numbers=picked_numbers)
