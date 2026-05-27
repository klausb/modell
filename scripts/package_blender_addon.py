#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import zipfile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Package blender_addon as a Blender-installable ZIP archive."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root containing the blender_addon directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output archive path. Defaults to dist/blender_addon-<UTC_TIMESTAMP>.zip "
            "under the repository root."
        ),
    )
    return parser


def package_addon(repo_root: Path, output_path: Path | None) -> Path:
    addon_dir = repo_root / "blender_addon"
    if not addon_dir.is_dir():
        raise FileNotFoundError(f"Missing add-on directory: {addon_dir}")

    if output_path is None:
        timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
        output_path = repo_root / "dist" / f"blender_addon-{timestamp}.zip"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(addon_dir.rglob("*")):
            if path.is_dir():
                continue
            if path.name.endswith(".pyc"):
                continue
            if "__pycache__" in path.parts:
                continue

            arcname = path.relative_to(repo_root)
            zf.write(path, arcname.as_posix())

    return output_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output = args.output.resolve() if args.output is not None else None

    archive = package_addon(repo_root, output)
    print(f"Created: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
