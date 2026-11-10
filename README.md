# envcheck

Catch missing, empty and duplicate variables by checking your `.env` against `.env.example`, locally or in CI. Zero dependencies.

```console
$ envcheck
missing    DATABASE_URL
empty      SECRET_KEY
duplicate  PORT (lines 3, 9)
extra      DEBUG_TOOLBAR (warning)
$ echo $?
1
```

## Install

```sh
pip install .          # from a clone; requires Python 3.9+
python -m envcheck     # or run without installing: PYTHONPATH=src
```

## Usage

```sh
envcheck                       # checks ./.env against ./.env.example
envcheck prod.env -e .env.example
envcheck --strict              # also fail on variables not in the example
envcheck --ignore PORT --ignore DEBUG   # skip variables you set elsewhere
envcheck --fix                 # append missing variables from the example to .env
envcheck --format json         # machine-readable output
```

| Finding     | Meaning                                                                 | Fails the check |
|-------------|-------------------------------------------------------------------------|-----------------|
| `missing`   | In the example, absent from the env file                                | yes             |
| `empty`     | Blank in the env file, but has a value in the example                   | yes             |
| `duplicate` | Defined more than once in the env file                                  | yes             |
| syntax      | Line is not `KEY=VALUE`, bad name, or unterminated quote                | yes             |
| `extra`     | In the env file, not in the example                                     | only `--strict` |

A variable left blank in `.env.example` (`OPTIONAL_THING=`) is treated as optional, so a blank value in `.env` is fine.

`--fix` copies the example's line for each missing variable (placeholder value included) to the end of the env file; existing lines are never modified. Findings are then re-checked, so remaining problems such as empty values still fail.

Exit codes: `0` ok, `1` problems found, `2` a file could not be read.

### Supported syntax

`KEY=value`, `export KEY=value`, single or double quotes (`"` supports `\"` escapes), full-line `#` comments and trailing ` # comments` on unquoted values. Variable interpolation (`${OTHER}`) is not expanded.

### In CI

```yaml
- run: pip install .
- run: envcheck .env.ci --strict
```

## Development

```sh
python -m unittest
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Released under the [MIT License](LICENSE).
