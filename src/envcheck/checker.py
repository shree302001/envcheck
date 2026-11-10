"""Compare an env file against an example template."""

from dataclasses import dataclass, field
from typing import List, Tuple

from .parser import ParsedEnv


@dataclass
class Report:
    missing: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)
    empty: List[str] = field(default_factory=list)
    duplicates: List[Tuple[str, List[int]]] = field(default_factory=list)
    syntax: List[Tuple[int, str]] = field(default_factory=list)

    def problems(self, strict: bool = False) -> int:
        """Number of findings that should fail the check."""
        n = len(self.missing) + len(self.empty) + len(self.duplicates) + len(self.syntax)
        if strict:
            n += len(self.extra)
        return n

    def to_dict(self) -> dict:
        return {
            "missing": self.missing,
            "extra": self.extra,
            "empty": self.empty,
            "duplicates": [{"key": k, "lines": lines} for k, lines in self.duplicates],
            "syntax": [{"line": n, "message": m} for n, m in self.syntax],
        }


def compare(env: ParsedEnv, example: ParsedEnv) -> Report:
    """Compare ``env`` to ``example``.

    A variable is "empty" when it is blank in the env file but the example
    does not itself leave it blank (so optional variables stay optional).
    """
    report = Report(syntax=list(env.errors))
    env_keys = env.keys()
    example_keys = example.keys()

    seen = {}
    for e in env.entries:
        seen.setdefault(e.key, []).append(e.line)
    report.duplicates = [(k, lines) for k, lines in seen.items() if len(lines) > 1]

    # Preserve the order of the example for readable output.
    ordered_example = list(dict.fromkeys(e.key for e in example.entries))
    report.missing = [k for k in ordered_example if k not in env_keys]
    report.extra = [k for k in seen if k not in example_keys]
    for k in ordered_example:
        if k in env_keys and env.first(k).value == "" and example.first(k).value != "":
            report.empty.append(k)
    return report
