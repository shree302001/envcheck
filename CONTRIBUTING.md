# Contributing

Thanks for helping out! Bug reports and small, focused pull requests are welcome.

## Setup

```sh
git clone <your fork>
cd envcheck
python -m unittest        # no dependencies needed
```

## Guidelines

- Keep it standard-library only.
- Add a test for every behaviour change (`tests/`).
- Update `CHANGELOG.md` under "Unreleased".
- Use short, imperative commit messages ("Add JSON output").
- One logical change per pull request.

## Reporting bugs

Open an issue with the smallest `.env` / `.env.example` pair that reproduces the problem, the output you got and what you expected.
