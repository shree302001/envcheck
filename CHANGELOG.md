# Changelog

All notable changes are documented here.

## Unreleased

- `# type: int|float|bool|url` hints in the example validate values; mismatches are reported as `invalid`.
- `--fix` appends variables missing from the env file, using the example's lines.
- Several env files can be checked in one run (`envcheck a.env b.env`).
- `--ignore KEY` (repeatable) leaves a variable out of all findings and out of `--fix`.

## 0.1.0

- Initial release: compare `.env` to `.env.example`, reporting missing, empty, duplicate and extra variables and syntax errors.
- `--strict` and `--format json` options.
