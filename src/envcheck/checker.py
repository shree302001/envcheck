"""Compare an env file against an example template."""

from dataclasses import dataclass, field
from typing import Iterable, List, Tuple
from urllib.parse import urlparse

from .parser import ParsedEnv


def _is_int(v: str) -> bool:
    try:
        int(v)
    except ValueError:
        return False
    return True


def _is_float(v: str) -> bool:
    try:
        float(v)
    except ValueError:
        return False
    return True


def _is_url(v: str) -> bool:
    parts = urlparse(v)
    return bool(parts.scheme and (parts.netloc or parts.scheme in ("mailto", "file")))


# Types accepted in `# type: NAME` hints. Unknown names are not checked.
VALIDATORS = {
    "int": _is_int,
    "float": _is_float,
    "bool": lambda v: v.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off"),
    "url": _is_url,
}


@dataclass
class Report:
    missing: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)
    empty: List[str] = field(default_factory=list)
    duplicates: List[Tuple[str, List[int]]] = field(default_factory=list)
    invalid: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, type, value)
    syntax: List[Tuple[int, str]] = field(default_factory=list)

    def problems(self, strict: bool = False) -> int:
        """Number of findings that should fail the check."""
        n = len(self.missing) + len(self.empty) + len(self.invalid) + len(self.duplicates) + len(self.syntax)
        if strict:
            n += len(self.extra)
        return n

    def to_dict(self) -> dict:
        return {
            "missing": self.missing,
            "extra": self.extra,
            "empty": self.empty,
            "invalid": [{"key": k, "type": t, "value": v} for k, t, v in self.invalid],
            "duplicates": [{"key": k, "lines": lines} for k, lines in self.duplicates],
            "syntax": [{"line": n, "message": m} for n, m in self.syntax],
        }


def compare(env: ParsedEnv, example: ParsedEnv, ignore: Iterable[str] = ()) -> Report:
    """Compare ``env`` to ``example``.

    A variable is "empty" when it is blank in the env file but the example
    does not itself leave it blank (so optional variables stay optional).
    Variables named in ``ignore`` are left out of every finding.
    """
    skip = set(ignore)
    report = Report(syntax=list(env.errors))
    env_keys = env.keys()
    example_keys = example.keys()

    seen = {}
    for e in env.entries:
        seen.setdefault(e.key, []).append(e.line)
    report.duplicates = [(k, lines) for k, lines in seen.items() if len(lines) > 1 and k not in skip]

    # Preserve the order of the example for readable output.
    ordered_example = list(dict.fromkeys(e.key for e in example.entries if e.key not in skip))
    report.missing = [k for k in ordered_example if k not in env_keys]
    report.extra = [k for k in seen if k not in example_keys and k not in skip]
    for k in ordered_example:
        if k in env_keys and env.first(k).value == "" and example.first(k).value != "":
            report.empty.append(k)
    for k in ordered_example:
        check = VALIDATORS.get(example.first(k).type_hint)
        for e in env.entries:
            if e.key == k and e.value != "" and check and not check(e.value):
                report.invalid.append((k, example.first(k).type_hint, e.value))
                break
    return report
