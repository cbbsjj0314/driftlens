#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv lock --check

repo_root=$PWD
temp_root=$(mktemp -d)
trap 'rm -rf "$temp_root"' EXIT

build_dir="$temp_root/dist"
default_venv="$temp_root/default-venv"
llm_venv="$temp_root/llm-venv"
work_dir="$temp_root/work"
mkdir -p "$work_dir"

if ! uv build --out-dir "$build_dir" >"$temp_root/build.log" 2>&1; then
  echo "Package build failed." >&2
  cat "$temp_root/build.log" >&2
  exit 1
fi

shopt -s nullglob
wheels=("$build_dir"/driftlens-*.whl)
sdists=("$build_dir"/driftlens-*.tar.gz)
shopt -u nullglob

if [[ ${#wheels[@]} -ne 1 ]]; then
  echo "Expected exactly one DriftLens wheel; found ${#wheels[@]}." >&2
  exit 1
fi

if [[ ${#sdists[@]} -ne 1 ]]; then
  echo "Expected exactly one DriftLens source distribution; found ${#sdists[@]}." >&2
  exit 1
fi

wheel=${wheels[0]}
sdist=${sdists[0]}

if ! uv venv --python 3.12 "$default_venv" >"$temp_root/default-venv.log" 2>&1; then
  echo "Default Python environment creation failed." >&2
  cat "$temp_root/default-venv.log" >&2
  exit 1
fi

if ! uv venv --python 3.12 "$llm_venv" >"$temp_root/llm-venv.log" 2>&1; then
  echo "LLM Python environment creation failed." >&2
  cat "$temp_root/llm-venv.log" >&2
  exit 1
fi

"$default_venv/bin/python" - "$repo_root/pyproject.toml" "$wheel" "$sdist" <<'PY'
import configparser
import email.parser
import re
import sys
import tarfile
import tomllib
import zipfile
from pathlib import PurePosixPath


pyproject_path, wheel_path, sdist_path = sys.argv[1:]


def canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def requirement_name(value: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", value)
    if match is None:
        raise SystemExit("Wheel contains an unsupported Requires-Dist value.")
    return canonical_name(match.group(1))


def normalized_marker(value: str) -> str:
    value = value.strip().replace("'", '"')
    value = re.sub(r"\s+", " ", value)
    return value


def sanitized_member(value: str) -> str:
    return "".join(character if character.isprintable() else "?" for character in value)


def validate_archive_members(label: str, members: list[str]) -> None:
    forbidden_directories = {
        ".artifacts",
        ".git",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "artifacts",
    }

    for raw_member in members:
        archive_path = raw_member.replace("\\", "/")
        normalized = archive_path
        while normalized.startswith("./"):
            normalized = normalized[2:]
        path = PurePosixPath(normalized)
        parts = path.parts
        lowered_parts = tuple(part.lower() for part in parts)

        unsafe = (
            not normalized
            or PurePosixPath(archive_path).is_absolute()
            or ".." in parts
            or ".env" in lowered_parts
            or any(part in forbidden_directories for part in lowered_parts)
            or any(
                lowered_parts[index : index + 2] == ("docs", "local")
                for index in range(max(0, len(lowered_parts) - 1))
            )
            or any("dogfood" in part for part in lowered_parts)
            or path.suffix.lower() == ".log"
        )
        if unsafe:
            raise SystemExit(
                f"{label} contains forbidden content: {sanitized_member(normalized)}"
            )


with open(pyproject_path, "rb") as pyproject_file:
    project = tomllib.load(pyproject_file)["project"]

with zipfile.ZipFile(wheel_path) as wheel_archive:
    wheel_members = wheel_archive.namelist()
    validate_archive_members("Wheel", wheel_members)

    metadata_members = [
        member for member in wheel_members if member.endswith(".dist-info/METADATA")
    ]
    entry_point_members = [
        member
        for member in wheel_members
        if member.endswith(".dist-info/entry_points.txt")
    ]
    if len(metadata_members) != 1 or len(entry_point_members) != 1:
        raise SystemExit("Wheel must contain one METADATA and one entry_points.txt file.")

    metadata = email.parser.BytesParser().parsebytes(
        wheel_archive.read(metadata_members[0])
    )
    entry_points_text = wheel_archive.read(entry_point_members[0]).decode("utf-8")

with tarfile.open(sdist_path, mode="r:gz") as sdist_archive:
    validate_archive_members(
        "Source distribution", [member.name for member in sdist_archive.getmembers()]
    )

if canonical_name(metadata["Name"] or "") != canonical_name(project["name"]):
    raise SystemExit("Wheel package name does not match pyproject.toml.")
if metadata["Version"] != project["version"]:
    raise SystemExit("Wheel package version does not match pyproject.toml.")

requirements = metadata.get_all("Requires-Dist", failobj=[])
unconditional = set()
llm_extra = set()
for requirement in requirements:
    requirement_text, separator, marker = requirement.partition(";")
    name = requirement_name(requirement_text)
    if not separator:
        unconditional.add(name)
    elif normalized_marker(marker) == 'extra == "llm"':
        llm_extra.add(name)

if "click" not in unconditional:
    raise SystemExit("Wheel metadata is missing unconditional click.")
if "typer" not in unconditional:
    raise SystemExit("Wheel metadata is missing unconditional typer.")
if "openai" in unconditional:
    raise SystemExit("Wheel metadata declares openai as a default requirement.")
if "openai" not in llm_extra:
    raise SystemExit("Wheel metadata is missing openai for the llm extra.")

entry_points = configparser.ConfigParser(interpolation=None)
entry_points.optionxform = str
entry_points.read_string(entry_points_text)
if entry_points.get("console_scripts", "driftlens", fallback="").strip() != "driftlens.cli:app":
    raise SystemExit("Wheel metadata is missing the DriftLens console entrypoint.")
PY

if ! uv pip install \
  --python "$default_venv/bin/python" \
  "$wheel" \
  >"$temp_root/default-install.log" 2>&1; then
  echo "Default wheel installation failed." >&2
  cat "$temp_root/default-install.log" >&2
  exit 1
fi

if ! uv pip install \
  --python "$llm_venv/bin/python" \
  "${wheel}[llm]" \
  >"$temp_root/llm-install.log" 2>&1; then
  echo "LLM wheel installation failed." >&2
  cat "$temp_root/llm-install.log" >&2
  exit 1
fi

unset PYTHONPATH

(
  cd "$work_dir"

  "$default_venv/bin/python" - "$repo_root" "$default_venv" <<'PY'
import importlib.util
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
venv_root = Path(sys.argv[2]).resolve()

import click
import driftlens.cli

module_path = Path(driftlens.cli.__file__).resolve()
if not module_path.is_relative_to(venv_root) or module_path.is_relative_to(repo_root):
    raise SystemExit("Default installation imported DriftLens outside its environment.")
if importlib.util.find_spec("openai") is not None:
    raise SystemExit("Default installation unexpectedly contains openai.")
PY

  "$default_venv/bin/driftlens" --help >/dev/null
  "$default_venv/bin/driftlens" detect --help >/dev/null

  "$default_venv/bin/driftlens" detect \
    "$repo_root/tests/fixtures/steam_appdetails_v1.json" \
    "$repo_root/tests/fixtures/steam_appdetails_nested_v1.json" \
    --out-dir "$temp_root/default-output" \
    >"$temp_root/default-stdout.json"

  "$default_venv/bin/python" - "$temp_root/default-stdout.json" "$temp_root/default-output" <<'PY'
import json
import sys
from pathlib import Path

stdout_path = Path(sys.argv[1])
output_dir = Path(sys.argv[2])
summary = json.loads(stdout_path.read_text(encoding="utf-8"))
expected = {
    "samples/previous.json",
    "samples/current.json",
    "schemas/previous.json",
    "schemas/current.json",
    "diffs/schema_diff.json",
    "diffs/classified_diff.json",
    "summary.json",
}
if set(summary["artifacts"].values()) != expected:
    raise SystemExit("Default smoke returned unexpected artifact paths.")
if any(not (output_dir / relative_path).is_file() for relative_path in expected):
    raise SystemExit("Default smoke did not write all deterministic artifacts.")
PY

  "$default_venv/bin/driftlens" detect \
    "$repo_root/tests/fixtures/steam_appdetails_v1.json" \
    "$repo_root/tests/fixtures/steam_appdetails_nested_v1.json" \
    --out-dir "$temp_root/mock-output" \
    --report \
    --analysis-provider mock \
    >"$temp_root/mock-stdout.json"

  test -f "$temp_root/mock-output/summary.json"
  test -f "$temp_root/mock-output/llm/analysis.json"
  test -f "$temp_root/mock-output/reports/schema_drift.md"

  "$default_venv/bin/python" - "$temp_root/mock-stdout.json" <<'PY'
import importlib.util
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stdout_file:
    json.load(stdout_file)
if importlib.util.find_spec("openai") is not None:
    raise SystemExit("Mock report smoke unexpectedly required openai.")
PY
)

(
  cd "$work_dir"

  "$llm_venv/bin/python" - "$repo_root" "$llm_venv" <<'PY'
import importlib.util
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
venv_root = Path(sys.argv[2]).resolve()

if importlib.util.find_spec("openai") is None:
    raise SystemExit("The llm extra did not install openai.")

import driftlens.cli
import driftlens.llm.openai_compatible

for module in (driftlens.cli, driftlens.llm.openai_compatible):
    module_path = Path(module.__file__).resolve()
    if not module_path.is_relative_to(venv_root) or module_path.is_relative_to(repo_root):
        raise SystemExit("The llm installation imported DriftLens outside its environment.")
PY

  "$llm_venv/bin/driftlens" --help >/dev/null
  "$llm_venv/bin/driftlens" detect --help >/dev/null
)

echo "Package checks passed."
