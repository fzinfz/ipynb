#!/usr/bin/env python
import os
import shutil
import pathlib
from datetime import datetime
import sys

# uv run python merge_folders.py

# Source pattern: multiple folders matching D:\_images\iPad Mini 5*
src_pattern = r"D:\_images\iPad Mini 5*"
dest_base = r"F:\_images\iPad Mini 5"


def get_modified_ym(filepath: pathlib.Path) -> str:
    """Return last modified year and month as YYYYMM string."""
    ts = os.path.getmtime(filepath)
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y%m")


def ensure_dir(p: pathlib.Path):
    """Create directory if it doesn't exist."""
    p.mkdir(parents=True, exist_ok=True)


def copy_file(src: pathlib.Path, dst_dir: pathlib.Path):
    """
    Copy src file to dst_dir.
    If file with same name exists:
      - if sizes equal: skip and print message
      - if sizes differ: save as <stem>_<index><suffix> with incrementing index
    """
    stem = src.stem
    suffix = src.suffix
    candidate = dst_dir / src.name
    idx = 1
    while candidate.exists():
        if os.path.getsize(candidate) == os.path.getsize(src):
            print(f"Skipping {src.name}: identical size in {dst_dir}")
            return
        # size differs -> try indexed name
        candidate = dst_dir / f"{stem}_{idx}{suffix}"
        idx += 1
    shutil.copy2(src, candidate)
    if candidate.name == src.name:
        print(f"Copied {src.name} → {dst_dir}")
    else:
        print(f"Copied as {candidate.name} (size differed) → {dst_dir}")


def main():
    # Find all matching source directories
    src_roots = [
        pathlib.Path(p) for p in pathlib.Path(r"D:\_images").glob("iPad Mini 5*")
    ]
    if not src_roots:
        print("No source folders matched the pattern.")
        return

    # Ensure base destination exists
    ensure_dir(pathlib.Path(dest_base))

    # Process each source root
    for src_root in src_roots:
        print(f"Processing source: {src_root}")
        for src_file in src_root.rglob("*"):
            if src_file.is_file():
                yymm = get_modified_ym(src_file)
                dst_subdir = pathlib.Path(dest_base) / yymm
                ensure_dir(dst_subdir)
                copy_file(src_file, dst_subdir)


if __name__ == "__main__":
    main()
