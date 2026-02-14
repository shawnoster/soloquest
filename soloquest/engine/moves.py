"""Move resolution logic — outcome tiers, momentum burn."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OutcomeTier(StrEnum):
    STRONG_HIT = "strong_hit"
    WEAK_HIT = "weak_hit"
    MISS = "miss"


@dataclass(frozen=True)
class MoveResult:
    action_die: int
    stat: int
    adds: int
    action_score: int
    challenge_1: int
    challenge_2: int
    outcome: OutcomeTier
    match: bool
    burned_momentum: bool = False
    momentum_used: int = 0

    @property
    def beats_c1(self) -> bool:
        return self.action_score > self.challenge_1

    @property
    def beats_c2(self) -> bool:
        return self.action_score > self.challenge_2


def resolve_outcome(action_score: int, c1: int, c2: int) -> OutcomeTier:
    """Determine outcome tier from action score vs challenge dice."""
    beats = (action_score > c1) + (action_score > c2)
    match beats:
        case 2:
            return OutcomeTier.STRONG_HIT
        case 1:
            return OutcomeTier.WEAK_HIT
        case _:
            return OutcomeTier.MISS


def check_match(c1: int, c2: int) -> bool:
    return c1 == c2


def momentum_burn_outcome(momentum: int, c1: int, c2: int) -> OutcomeTier:
    """What outcome would result from burning momentum as action score."""
    return resolve_outcome(momentum, c1, c2)


def would_momentum_improve(
    current_outcome: OutcomeTier,
    momentum: int,
    c1: int,
    c2: int,
) -> bool:
    """Return True if burning momentum would improve the current outcome."""
    if momentum <= 0:
        return False
    burn_outcome = momentum_burn_outcome(momentum, c1, c2)
    tier_rank = {OutcomeTier.MISS: 0, OutcomeTier.WEAK_HIT: 1, OutcomeTier.STRONG_HIT: 2}
    return tier_rank[burn_outcome] > tier_rank[current_outcome]


def resolve_move(
    action_die: int,
    stat: int,
    adds: int,
    c1: int,
    c2: int,
    momentum: int = 0,
    burn: bool = False,
) -> MoveResult:
    """Full move resolution — optionally burn momentum."""
    action_score = min(action_die + stat + adds, 10)  # action score caps at 10
    match_flag = check_match(c1, c2)

    if burn and momentum > 0:
        outcome = momentum_burn_outcome(momentum, c1, c2)
        return MoveResult(
            action_die=action_die,
            stat=stat,
            adds=adds,
            action_score=action_score,
            challenge_1=c1,
            challenge_2=c2,
            outcome=outcome,
            match=match_flag,
            burned_momentum=True,
            momentum_used=momentum,
        )

    outcome = resolve_outcome(action_score, c1, c2)
    return MoveResult(
        action_die=action_die,
        stat=stat,
        adds=adds,
        action_score=action_score,
        challenge_1=c1,
        challenge_2=c2,
        outcome=outcome,
        match=match_flag,
    )
