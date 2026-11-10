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
    for k, typ, value in report.invalid:
        lines.append(f"invalid    {k} (expected {typ}, got {value!r})")
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
    p.add_argument("env", nargs="*", help="env file(s) to check (default: .env)")
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


def check_file(path: str, example: ParsedEnv, args: argparse.Namespace) -> dict:
    """Check one env file; return its report data plus ``added`` and ``failed``."""
    env = parse(_read(path))
    added: List[str] = []
    if args.fix:
        added = append_missing(path, env, example, args.ignore)
        if added:
            env = parse(_read(path))
    report = compare(env, example, args.ignore)
    return {"report": report, "added": added,
            "failed": report.problems(args.strict) > 0}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    paths = args.env or [".env"]
    try:
        example = parse(_read(args.example))
        results = [(p, check_file(p, example, args)) for p in paths]
    except OSError as exc:
        print(f"envcheck: {exc}", file=sys.stderr)
        return 2
    failed = any(r["failed"] for _, r in results)
    if args.format == "json":
        items = []
        for path, r in results:
            data = r["report"].to_dict()
            data["ok"] = not r["failed"]
            if args.fix:
                data["added"] = r["added"]
            items.append((path, data))
        if len(items) == 1:
            out = items[0][1]
        else:
            out = {"ok": not failed,
                   "files": [dict(file=path, **data) for path, data in items]}
        print(json.dumps(out, indent=2))
    else:
        for n, (path, r) in enumerate(results):
            if len(results) > 1:
                if n:
                    print()
                print(f"==> {path} <==")
            for k in r["added"]:
                print(f"added      {k}")
            print(format_text(r["report"], path, args.strict))
    return 1 if failed else 0
