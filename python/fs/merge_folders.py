#!/usr/bin/env python
import os
import shutil
import pathlib
from datetime import datetime
import sys

# uv run python merge_folders.py

# Configuration
src_pattern = r"D:\_images\Screenshots*"
dest_base = r"F:\_images\Screenshots"
dest_base_video = r"F:\_videos"

# Video file extensions (lowercase)
VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".3gp",
    ".3g2",
    ".asf",
    ".rm",
    ".swf",
    ".vob",
    ".ts",
    ".m2ts",
    ".mts",
    ".divx",
    ".xvid",
}


def is_video(filepath: pathlib.Path) -> bool:
    """Check if a file is a video based on its extension."""
    return filepath.suffix.lower() in VIDEO_EXTENSIONS


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
        candidate = dst_dir / f"{stem}_{idx}{suffix}"
        idx += 1
    shutil.copy2(src, candidate)
    if candidate.name == src.name:
        print(f"Copied {src.name} -> {dst_dir}")
    else:
        print(f"Copied as {candidate.name} (size differed) -> {dst_dir}")


def step1_copy_files():
    """Step 1: Copy files from source to destination, organizing by modified date."""
    src_roots = get_src_roots()
    if not src_roots:
        print("No source folders matched the pattern.")
        return

    ensure_dir(pathlib.Path(dest_base))
    ensure_dir(pathlib.Path(dest_base_video))

    for src_root in src_roots:
        print(f"Processing source: {src_root}")
        for src_file in src_root.rglob("*"):
            if src_file.is_file():
                if is_video(src_file):
                    ensure_dir(pathlib.Path(dest_base_video))
                    copy_file(src_file, pathlib.Path(dest_base_video))
                else:
                    yymm = get_modified_ym(src_file)
                    dst_subdir = pathlib.Path(dest_base) / yymm
                    ensure_dir(dst_subdir)
                    copy_file(src_file, dst_subdir)


def collect_folder_stats(base_path: pathlib.Path) -> list:
    """Collect folder statistics."""
    results = []
    if not base_path.exists():
        return results

    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            dir_size = 0
            file_count = 0
            for file in item.rglob("*"):
                if file.is_file():
                    dir_size += file.stat().st_size
                    file_count += 1
            results.append(
                {
                    "name": item.name,
                    "size_bytes": dir_size,
                    "file_count": file_count,
                }
            )
    return results


def step2_folder_sizes():
    """Step 2: Get size of every subfolder under dest_base and save to 3 analysis files."""
    base_path = pathlib.Path(dest_base)
    parent = pathlib.Path(dest_base).parent
    base_name = pathlib.Path(dest_base).name

    print(f"\nCalculating folder sizes under: {base_path}")

    results = collect_folder_stats(base_path)
    if not results:
        print(f"No subfolders found in {base_path}")
        return

    total_size = sum(r["size_bytes"] for r in results)
    total_files = sum(r["file_count"] for r in results)

    # Helper to format size
    def fmt_size(size_bytes):
        size_mb = size_bytes / (1024 * 1024)
        if size_mb >= 1024:
            return f"{size_mb / 1024:>8.2f} GB"
        else:
            return f"{size_mb:>8.2f} MB"

    # --- File 1: Sorted by folder name (default) ---
    file_by_name = parent / f"{base_name}_by_name.txt"
    _write_report(
        file_by_name, results, total_size, total_files, "Sorted by Folder Name (YYYYMM)"
    )

    # --- File 2: Sorted by file count (descending) ---
    results_by_count = sorted(results, key=lambda x: x["file_count"], reverse=True)
    file_by_count = parent / f"{base_name}_by_file_count.txt"
    _write_report(
        file_by_count,
        results_by_count,
        total_size,
        total_files,
        "Sorted by File Count (Descending)",
    )

    # --- File 3: Sorted by folder size (descending) ---
    results_by_size = sorted(results, key=lambda x: x["size_bytes"], reverse=True)
    file_by_size = parent / f"{base_name}_by_folder_size.txt"
    _write_report(
        file_by_size,
        results_by_size,
        total_size,
        total_files,
        "Sorted by Folder Size (Descending)",
    )

    # Print summary to console
    print("\n" + "=" * 70)
    print(f"{'Folder':20s} {'Size':>15s} {'Files':>8s}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['name']:20s} {fmt_size(r['size_bytes']):>15s}  {r['file_count']:>6d}"
        )
    print("-" * 70)
    print(f"{'TOTAL':20s} {fmt_size(total_size):>15s}  {total_files:>6d}")
    print("=" * 70)
    print(f"\nReports saved to:")
    print(f"  {file_by_name}")
    print(f"  {file_by_count}")
    print(f"  {file_by_size}")


def _write_report(
    output_file: pathlib.Path,
    results: list,
    total_size: int,
    total_files: int,
    sort_desc: str,
):
    """Write a report file."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Folder size report for: {output_file.stem}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Sorting: {sort_desc}\n")
        f.write("=" * 70 + "\n\n")

        # Header
        f.write(f"{'Folder':20s} {'Size':>15s} {'Files':>8s} {'Avg Size/File':>15s}\n")
        f.write("-" * 70 + "\n")

        for r in results:
            size_mb = r["size_bytes"] / (1024 * 1024)
            if size_mb >= 1024:
                size_str = f"{size_mb / 1024:.2f} GB"
            else:
                size_str = f"{size_mb:.2f} MB"

            avg = r["size_bytes"] / r["file_count"] / 1024 if r["file_count"] > 0 else 0
            f.write(
                f"{r['name']:20s} {size_str:>15s}  {r['file_count']:>6d}  {avg:>12.1f} KB\n"
            )

        f.write("-" * 70 + "\n")
        total_mb = total_size / (1024 * 1024)
        if total_mb >= 1024:
            total_str = f"{total_mb / 1024:.2f} GB"
        else:
            total_str = f"{total_mb:.2f} MB"
        avg_total = total_size / total_files / 1024 if total_files > 0 else 0
        f.write(
            f"{'TOTAL':20s} {total_str:>15s}  {total_files:>6d}  {avg_total:>12.1f} KB\n"
        )
        f.write("=" * 70 + "\n")


def step3_move_videos():
    """Step 3: Move video files from dest_base/yyyymm to dest_base_video, overwrite if exists."""
    base_path = pathlib.Path(dest_base)
    video_path = pathlib.Path(dest_base_video)

    if not base_path.exists():
        print(f"Error: {base_path} does not exist.")
        return

    ensure_dir(video_path)

    moved = 0
    skipped = 0
    overwritten = 0

    print(f"\nMoving video files from {base_path} to {video_path}")

    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            for file in item.rglob("*"):
                if file.is_file() and is_video(file):
                    dst = video_path / file.name
                    if dst.exists():
                        if os.path.getsize(dst) == os.path.getsize(file):
                            print(
                                f"Skipping {file.name}: already exists with same size"
                            )
                            skipped += 1
                        else:
                            shutil.copy2(file, dst)
                            file.unlink()
                            print(f"Overwritten {file.name} (size differed)")
                            overwritten += 1
                    else:
                        shutil.copy2(file, dst)
                        file.unlink()
                        print(f"Moved {file.name}")
                        moved += 1

    print(f"\n--- Move Summary ---")
    print(f"Moved: {moved}")
    print(f"Skipped (same size): {skipped}")
    print(f"Overwritten (diff size): {overwritten}")
    print(f"Total: {moved + skipped + overwritten}")


def get_src_roots() -> list:
    """Get source root directories from src_pattern."""
    src_pattern_path = pathlib.Path(src_pattern)
    src_parent = src_pattern_path.parent
    src_glob = src_pattern_path.name
    return [pathlib.Path(p) for p in src_parent.glob(src_glob)]


def show_menu():
    """Display menu and get user choice."""
    src_roots = get_src_roots()
    print("=" * 60)
    print("File Copy and Folder Analysis Tool")
    print("=" * 60)
    print(f"Source pattern: {src_pattern}")
    print(f"Source roots ({len(src_roots)}):")
    for root in src_roots:
        print(f"  - {root}")
    print(f"Destination (images): {dest_base}")
    print(f"Destination (videos): {dest_base_video}")
    print("=" * 60)
    print("\nSelect operation:")
    print("1. Copy files (Step 1)")
    print("2. Analyze folders (Step 2) - 3 reports")
    print("3. Move videos from YYYYMM to video folder (tmp)")
    print("4. Run Step 1 + 2 (Copy + Analyze)")
    print("0. Exit")
    print()

    while True:
        choice = input("Enter your choice (0-4): ").strip()
        if choice in ["0", "1", "2", "3", "4"]:
            return choice
        print("Invalid choice. Please try again.")


def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = show_menu()

    if choice == "1":
        print("\n--- Step 1: Copying files ---")
        step1_copy_files()
        print("\nCopying completed!")
    elif choice == "2":
        print("\n--- Step 2: Analyzing folder sizes ---")
        step2_folder_sizes()
        print("\nAnalysis completed!")
    elif choice == "3":
        print("\n--- Step 3: Moving videos ---")
        step3_move_videos()
        print("\nMoving completed!")
    elif choice == "4":
        print("\n--- Step 1: Copying files ---")
        step1_copy_files()
        print("\n--- Step 2: Analyzing folder sizes ---")
        step2_folder_sizes()
        print("\nSteps completed!")
    elif choice == "0":
        print("Exiting...")
    else:
        print(f"Invalid choice: {choice}")
        print("Usage: uv run python merge_folders.py [choice]")
        print("  0 = Exit")
        print("  1 = Copy files")
        print("  2 = Analyze folders (3 reports)")
        print("  3 = Move videos")
        print("  4 = All steps")


if __name__ == "__main__":
    main()
