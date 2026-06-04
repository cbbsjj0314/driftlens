import json
from pathlib import Path


def _resolve_artifact_path(base_dir: Path, relative_path: str) -> Path:
    artifact_path = Path(relative_path)

    if artifact_path.is_absolute():
        raise ValueError(f"Artifact path must be relative: {relative_path}")

    if ".." in artifact_path.parts:
        raise ValueError(
            f"Artifact path cannot traverse parent directories: {relative_path}"
        )

    resolved_base_dir = base_dir.resolve()
    resolved_artifact_path = (resolved_base_dir / artifact_path).resolve()

    if not resolved_artifact_path.is_relative_to(resolved_base_dir):
        raise ValueError(f"Artifact path must stay under base_dir: {relative_path}")

    return resolved_artifact_path


def write_json_artifact(base_dir: Path, relative_path: str, data: dict | list) -> Path:
    """Write a deterministic JSON artifact under base_dir and return its path."""
    artifact_path = _resolve_artifact_path(base_dir, relative_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_json = json.dumps(
        data,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )
    artifact_path.write_text(f"{artifact_json}\n", encoding="utf-8")

    return artifact_path


def write_text_artifact(base_dir: Path, relative_path: str, text: str) -> Path:
    """Write a UTF-8 text artifact under base_dir and return its path."""
    artifact_path = _resolve_artifact_path(base_dir, relative_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_text = text if text.endswith("\n") else f"{text}\n"
    artifact_path.write_text(artifact_text, encoding="utf-8")

    return artifact_path


def read_json_artifact(path: Path) -> dict | list:
    """Read a JSON artifact from a filesystem path."""
    return json.loads(path.read_text(encoding="utf-8"))
