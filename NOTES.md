# Project notes

## Idea
`envcheck`: stdlib-only Python CLI that validates a `.env` against `.env.example`
(missing, empty, duplicate, extra variables, syntax errors) for local use and CI.

## Decisions
- Layout: `src/envcheck/{parser,checker,cli}.py`; tests use `unittest` (no deps).
- Blank value in the example = optional variable.
- `extra` is a warning unless `--strict`.
- Exit codes: 0 ok, 1 problems, 2 unreadable file.
- No `${VAR}` interpolation.

## Roadmap
1. (done) Core parser, comparison, CLI, JSON output, CI, docs.
2. (done) `--fix` to append missing keys from the example to the env file.
3. Check several env files at once; `--ignore KEY` option.
4. Optional type hints in the example (e.g. `# type: int`).
5. Publish to PyPI.

## Done log
- Iteration 1: project created, parser/checker/CLI, 13 tests, README, CI, templates.
- Iteration 2: `--fix` (appends missing keys using the example's raw lines, then re-checks); `Entry.raw`; 4 tests.
