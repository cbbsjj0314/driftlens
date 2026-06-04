#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv run pytest tests/test_llm_openai_compatible.py
