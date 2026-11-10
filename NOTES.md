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
3. (done) `--ignore KEY` option.
3b. (done) Check several env files at once.
4. (done) Optional type hints in the example (e.g. `# type: int`).
5. Publish to PyPI.

## Done log
- Iteration 1: project created, parser/checker/CLI, 13 tests, README, CI, templates.
- Iteration 2: `--fix` (appends missing keys using the example's raw lines, then re-checks); `Entry.raw`; 4 tests.
- Iteration 3 (log numbering below is historical): `--ignore KEY` (repeatable; applies to all findings and `--fix`); 2 tests. Multi-file checking, type hints and PyPI remain optional future work; the tool is otherwise complete.
- Iteration 4: multiple env files per run (`==> file <==` headers in text, `files` list in JSON when more than one); 3 tests.
- Iteration 5: type hints (`# type: int|float|bool|url`, line above or inline in the example); new `invalid` finding that fails the check; 5 tests. Remaining: PyPI publishing (needs maintainer account).
- Final polish: moved a stray `unittest.main()` guard to the end of `tests/test_checker.py`, added a PyPI topic classifier. The project is feature-complete; only publishing to PyPI (needs a maintainer account) remains.
