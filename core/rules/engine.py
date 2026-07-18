"""Rules engine: facts -> rules (data) -> verdict with citations.

Design principles:
- Rules live in YAML with validity dates; the engine never contains a threshold.
- The regime is part of the facts and MUST be resolved before evaluation
  (the regime tree comes first — amounts never decide the regime).
- No eval(): conditions are structured {field, op, value} — safe and testable.
- Every hit carries a citation: a result without a citation is a bug.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

_OPS = {
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
    "eq": operator.eq,
}

DATA_DIR = Path(__file__).parent / "data"
PROFILES_DIR = DATA_DIR / "profiles"


@dataclass(frozen=True)
class Facts:
    """Input to an assessment. `regime` must be resolved by the caller first."""
    regime: str                 # "FOA" | "FOSA" | "ART123"
    estimated_value: Decimal    # NOK, excluding VAT
    assessment_date: date


@dataclass(frozen=True)
class RuleHit:
    rule_id: str
    regime: str
    consequence: str
    citation: str
    citation_url: str | None = None


class RulesEngine:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._rules: list[dict[str, Any]] = []
        for path in sorted(data_dir.glob("*.yaml")):
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                self._rules.extend(loaded)

    @staticmethod
    def _condition_holds(when: dict[str, Any], facts: Facts) -> bool:
        if "all" in when:
            return all(RulesEngine._condition_holds(c, facts) for c in when["all"])
        field, op, value = when["field"], when["op"], when["value"]
        actual = getattr(facts, field)
        return _OPS[op](Decimal(str(actual)), Decimal(str(value)))

    @staticmethod
    def _valid_on(rule: dict[str, Any], on: date) -> bool:
        valid_from: date = rule["valid_from"]
        valid_to: date | None = rule.get("valid_to")
        return valid_from <= on and (valid_to is None or on <= valid_to)

    def evaluate(self, facts: Facts) -> list[RuleHit]:
        hits: list[RuleHit] = []
        for rule in self._rules:
            if rule["regime"] != facts.regime:
                continue
            if not self._valid_on(rule, facts.assessment_date):
                continue
            if not self._condition_holds(rule["when"], facts):
                continue
            hits.append(RuleHit(
                rule_id=rule["id"],
                regime=rule["regime"],
                consequence=rule["consequence"],
                citation=rule["citation"],
                citation_url=rule.get("citation_url"),
            ))
        return hits


@dataclass(frozen=True)
class ReglementHit:
    """A hit from an organization's OWN internal reglement (the third control source)."""
    rule_id: str
    consequence: str
    message: str
    citation: str
    citation_url: str | None = None


def _dict_condition_holds(when: dict[str, Any], facts: dict[str, Any]) -> bool:
    if "all" in when:
        return all(_dict_condition_holds(c, facts) for c in when["all"])
    field, op, value = when["field"], when["op"], when["value"]
    actual = facts.get(field)
    if actual is None:
        return False
    return _OPS[op](Decimal(str(actual)), Decimal(str(value)))


class ReglementEngine:
    """Evaluates internal reglement rules (DATA in data/profiles/*.yaml) against a facts dict.

    Kept separate from RulesEngine so internal organization rules never mix with national law,
    and so these findings stay out of the core check_invoice pipeline (they are procedural,
    rendered at the UI level as a distinct third source).
    """
    def __init__(self, data_dir: Path = PROFILES_DIR) -> None:
        self._rules: list[dict[str, Any]] = []
        if data_dir.exists():
            for path in sorted(data_dir.glob("*.yaml")):
                loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    self._rules.extend(loaded)

    def evaluate(self, facts: dict[str, Any]) -> list[ReglementHit]:
        hits: list[ReglementHit] = []
        for rule in self._rules:
            if not _dict_condition_holds(rule["when"], facts):
                continue
            hits.append(ReglementHit(
                rule_id=rule["id"],
                consequence=rule["consequence"],
                message=rule.get("message", rule["consequence"]),
                citation=rule["citation"],
                citation_url=rule.get("citation_url"),
            ))
        return hits
