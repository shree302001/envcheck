"""A small, forgiving parser for dotenv files."""

import re
from dataclasses import dataclass, field
from typing import List, Tuple

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_HINT_RE = re.compile(r"#\s*type:\s*([A-Za-z]+)\s*$", re.IGNORECASE)


@dataclass
class Entry:
    key: str
    value: str
    line: int
    raw: str = ""  # the KEY=VALUE text as written, without `export`
    type_hint: str = ""  # from a `# type: int` comment, lower-cased


@dataclass
class ParsedEnv:
    entries: List[Entry] = field(default_factory=list)
    errors: List[Tuple[int, str]] = field(default_factory=list)  # (line, message)

    def keys(self):
        return {e.key for e in self.entries}

    def first(self, key):
        for e in self.entries:
            if e.key == key:
                return e
        return None


def _parse_value(raw: str) -> Tuple[str, bool]:
    """Return (value, ok). ok is False for an unterminated quote."""
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        quote = raw[0]
        i = 1
        out = []
        while i < len(raw):
            c = raw[i]
            if quote == '"' and c == "\\" and i + 1 < len(raw):
                out.append(raw[i + 1])
                i += 2
                continue
            if c == quote:
                return "".join(out), True
            out.append(c)
            i += 1
        return "".join(out), False
    # Unquoted: an inline comment starts at " #".
    m = re.search(r"\s#", raw)
    if m:
        raw = raw[: m.start()]
    return raw.strip(), True


def parse(text: str) -> ParsedEnv:
    result = ParsedEnv()
    pending_hint = ""  # a `# type:` comment line applies to the next variable
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            pending_hint = ""
            continue
        if stripped.startswith("#"):
            m = _HINT_RE.match(stripped)
            if m:
                pending_hint = m.group(1).lower()
            continue
        hint, pending_hint = pending_hint, ""
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].lstrip()
        if "=" not in stripped:
            result.errors.append((lineno, "expected KEY=VALUE"))
            continue
        key, _, raw = stripped.partition("=")
        key = key.strip()
        if not _KEY_RE.match(key):
            result.errors.append((lineno, f"invalid variable name {key!r}"))
            continue
        value, ok = _parse_value(raw)
        if not ok:
            result.errors.append((lineno, f"unterminated quote for {key}"))
            continue
        inline = _HINT_RE.search(raw)
        if inline:
            hint = inline.group(1).lower()
        result.entries.append(Entry(key, value, lineno, stripped, hint))
    return result
