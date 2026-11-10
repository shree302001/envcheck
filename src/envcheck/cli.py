"""Command line interface."""

import argparse
import json
import sys
from typing import Iterable, List, Optional

from . import __version__
from .checker import Report, compare
from .parser import ParsedEnv, parse


def _read(path: str) -> str:
    with open(path, encoding="utf-8-sig") as fh:
        return fh.read()


def append_missing(path: str, env: ParsedEnv, example: ParsedEnv,
                   ignore: Iterable[str] = ()) -> List[str]:
    """Append example lines for keys absent from ``path``; return the keys added."""
    keys = env.keys() | set(ignore)
    added = {}
    for e in example.entries:
        if e.key not in keys and e.key not in added:
            added[e.key] = e.raw
    if not added:
        return []
    with open(path, "rb") as fh:
        content = fh.read()
    prefix = "" if not content or content.endswith(b"\n") else "\n"
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(prefix + "".join(line + "\n" for line in added.values()))
    return list(added)


def format_text(report: Report, env_path: str, strict: bool) -> str:
    lines = []
    for n, msg in report.syntax:
        lines.append(f"{env_path}:{n}: syntax error: {msg}")
    for k in report.missing:
        lines.append(f"missing    {k}")
    for k in report.empty:
        lines.append(f"empty      {k}")
    for k, nums in report.duplicates:
        lines.append(f"duplicate  {k} (lines {', '.join(map(str, nums))})")
    for k in report.extra:
        lines.append(f"extra      {k}" + ("" if strict else " (warning)"))
    if not lines:
        return f"{env_path}: OK"
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envcheck",
        description="Check a .env file against a .env.example template.",
    )
    p.add_argument("env", nargs="?", default=".env", help="env file (default: .env)")
    p.add_argument("-e", "--example", default=".env.example",
                   help="template file (default: .env.example)")
    p.add_argument("--strict", action="store_true",
                   help="treat variables missing from the example as errors")
    p.add_argument("--fix", action="store_true",
                   help="append variables missing from the env file, using the example's lines")
    p.add_argument("--ignore", action="append", default=[], metavar="KEY",
                   help="leave KEY out of all findings (repeatable)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        env = parse(_read(args.env))
        example = parse(_read(args.example))
    except OSError as exc:
        print(f"envcheck: {exc}", file=sys.stderr)
        return 2
    added: List[str] = []
    if args.fix:
        try:
            added = append_missing(args.env, env, example, args.ignore)
            if added:
                env = parse(_read(args.env))
        except OSError as exc:
            print(f"envcheck: {exc}", file=sys.stderr)
            return 2
    report = compare(env, example, args.ignore)
    failed = report.problems(args.strict) > 0
    if args.format == "json":
        data = report.to_dict()
        data["ok"] = not failed
        if args.fix:
            data["added"] = added
        print(json.dumps(data, indent=2))
    else:
        for k in added:
            print(f"added      {k}")
        print(format_text(report, args.env, args.strict))
    return 1 if failed else 0
