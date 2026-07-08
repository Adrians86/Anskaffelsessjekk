"""Rules engine — rules live in data/ as versioned YAML, never in code."""
from core.rules.engine import Facts, RuleHit, RulesEngine

__all__ = ["Facts", "RuleHit", "RulesEngine"]
