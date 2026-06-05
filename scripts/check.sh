#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Fail before `uv run` can update a stale lockfile.
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run pytest

rm -rf .artifacts/ci-smoke
uv run driftlens detect \
  tests/fixtures/steam_appdetails_v1.json \
  tests/fixtures/steam_appdetails_nested_v1.json \
  --out-dir .artifacts/ci-smoke
test -f .artifacts/ci-smoke/summary.json
