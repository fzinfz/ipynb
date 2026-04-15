"""
Docusaurus Slug Fixer
=====================
1. Scans docs directory for md/mdx files with non-ASCII characters in filenames
   and injects front matter with an ASCII-safe slug.
2. Fixes bare `<` and `>` characters in markdown tables that break MDX compilation.

Usage:
    uv run docusaurus_fix_slug.py [--site <site_root>] [--dry-run]
    uv run docusaurus_fix_slug.py          # interactive site selection
"""

import glob;
import os;
import platform;
import re;
import sys;
import argparse;

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CONFIG = {
    "windows_pattern": r"D:\sites\*",
    "linux_pattern": "/data/site-*",
    "docs_subdir": "docs",
    "extensions": {".md", ".mdx"},
    "frontmatter_sep": "---",
};

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def has_non_ascii(text):
    """Return True if text contains any non-ASCII character."""
    try:
        text.encode("ascii");
        return False;
    except UnicodeEncodeError:
        return True;


def extract_slug_stem(filename):
    """Extract a numeric prefix from filename to use as slug stem.

    Examples:
        '001_XXX.md' -> '001'
    """
    stem = os.path.splitext(filename)[0];
    match = re.match(r"^(\d+)", stem);
    if match:
        return match.group(1);
    # Fallback: use entire ASCII-safe portion
    ascii_part = re.sub(r"[^\x00-\x7F]+", "", stem).strip("_-");
    return ascii_part or "doc";


def read_file_head(filepath, max_lines=5):
    """Read first N lines of a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [];
        for i, line in enumerate(f):
            if i >= max_lines:
                break;
            lines.append(line);
    return lines;


def has_frontmatter(filepath):
    """Check if file already starts with front matter (--- ... ---)."""
    try:
        lines = read_file_head(filepath, max_lines=10);
    except Exception:
        return False;
    if not lines:
        return False;
    if lines[0].strip() != "---":
        return False;
    for line in lines[1:]:
        if line.strip() == "---":
            return True;
    return False;


def get_existing_slug(filepath):
    """If file has front matter with slug, return its value; else None."""
    try:
        lines = read_file_head(filepath, max_lines=10);
    except Exception:
        return None;
    in_frontmatter = False;
    for line in lines:
        stripped = line.strip();
        if stripped == "---":
            if in_frontmatter:
                break;
            in_frontmatter = True;
            continue;
        if in_frontmatter:
            match = re.match(r"^slug\s*:\s*(.+)$", stripped);
            if match:
                return match.group(1).strip().strip("\"'");
    return None;


def inject_frontmatter(filepath, slug):
    """Inject slug front matter at the top of a file that has no front matter."""
    with open(filepath, "r", encoding="utf-8") as f:
        original_content = f.read();

    frontmatter = f"---\nslug: {slug}\n---\n\n";
    new_content = frontmatter + original_content;

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content);


def _needs_mdx_escape(line):
    """Check if a table line contains bare `<` or `>` that need JSX escaping.

    Uses character-by-character analysis to avoid false positives on:
    - HTML entities: ``&lt;``, ``&gt;``
    - Already-escaped JSX: ``{'<'}``, ``{'>'}``
    - Inline code spans: `` `<...>` ``

    Returns True if the line needs processing.
    """
    i = 0;
    length = len(line);

    while i < length:
        char = line[i];

        # Skip inside inline code spans (backtick-delimited)
        if char == "`":
            # Skip to closing backtick
            i += 1;
            while i < length and line[i] != "`":
                i += 1;
            i += 1;
            continue;

        # HTML entities starting with &
        if char == "&" and i + 3 < length:
            entity = line[i:i + 4];
            if entity in {"&lt;", "&gt;", "&amp;", "&quot;"}:
                i += len(entity);
                continue;

        # Already-escaped JSX: {'<'} or {'>'}
        if (
            char == "{"
            and i + 4 < length
            and line[i + 1] == "'"
            and line[i + 2] in {"<", ">"}
            and line[i + 3] == "'"
            and line[i + 4] == "}"
        ):
            i += 5;
            continue;

        # Bare < or > found
        if char in {"<", ">"}:
            return True;

        i += 1;

    return False;


def _escape_mdx_angle_brackets(line):
    """Escape bare `<` and `>` in a line with JSX expressions.

    Character-by-character replacement to prevent nested escaping issues.
    """
    result = [];
    i = 0;
    length = len(line);

    while i < length:
        char = line[i];

        # Preserve inline code spans
        if char == "`":
            j = i + 1;
            while j < length and line[j] != "`":
                j += 1;
            result.append(line[i:j + 1]);
            i = j + 1;
            continue;

        # Preserve HTML entities
        if char == "&" and i + 3 < length:
            entity = line[i:i + 4];
            if entity in {"&lt;", "&gt;", "&amp;", "&quot;"}:
                result.append(entity);
                i += len(entity);
                continue;

        # Preserve already-escaped JSX: {'<'} or {'>'}
        if (
            char == "{"
            and i + 4 < length
            and line[i + 1] == "'"
            and line[i + 2] in {"<", ">"}
            and line[i + 3] == "'"
            and line[i + 4] == "}"
        ):
            result.append(line[i:i + 5]);
            i += 5;
            continue;

        # Escape bare <
        if char == "<":
            # Allow valid HTML/JSX tags: <tag, </tag, <Component
            next_valid = (
                i + 1 < length and line[i + 1] in "/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ$_"
            );
            if next_valid:
                result.append(char);
                i += 1;
                continue;
            result.append("{'<'}");
            i += 1;
            continue;

        # Escape bare > (but not inside a tag context)
        if char == ">":
            # Allow > if preceded by alphanumeric or / (closing a tag)
            prev_valid = i > 0 and line[i - 1] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$/";
            if prev_valid:
                result.append(char);
                i += 1;
                continue;
            result.append("{'>'}");
            i += 1;
            continue;

        result.append(char);
        i += 1;

    return "".join(result);


def fix_mdx_angle_brackets(filepath, dry_run=False):
    """Fix bare `<` and `>` in markdown tables that break MDX compilation.

    MDX interprets `<...>` as JSX tags. In markdown tables, bare angle brackets
    like `<10` or `>50%` cause parse errors. This replaces them with JSX
    expression escapes: `{'<'}10`, `{'>'}50%`.

    Only targets table rows (lines containing ``|``) to minimize false positives.
    Skips blockquote lines (start with ``>``) entirely.
    Uses character-by-character analysis to prevent nested escaping on re-runs.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().split("\n");

    original_joined = "\n".join(lines);
    fixed_lines = [];

    for line in lines:
        # Skip blockquote lines (start with >)
        if line.startswith(">"):
            fixed_lines.append(line);
            continue;

        # Only process table rows (contain |)
        if "|" in line and _needs_mdx_escape(line):
            line = _escape_mdx_angle_brackets(line);

        fixed_lines.append(line);

    content = "\n".join(fixed_lines);

    if content == original_joined:
        return False;

    if not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content);
    return True;


def collect_files(docs_root):
    """Walk docs_root and yield (relative_path, filename) for all md/mdx files."""
    for dirpath, _dirnames, filenames in os.walk(docs_root):
        for fname in sorted(filenames):
            ext = os.path.splitext(fname)[1].lower();
            if ext not in CONFIG["extensions"]:
                continue;
            rel_dir = os.path.relpath(dirpath, docs_root);
            yield rel_dir, fname;


def discover_sites():
    """Discover available Docusaurus sites based on the current OS.

    Returns:
        list[str]: List of site root directories.
    """
    if platform.system() == "Windows":
        pattern = CONFIG["windows_pattern"];
    else:
        pattern = CONFIG["linux_pattern"];

    # glob returns full paths for absolute patterns
    dirs = sorted(glob.glob(pattern));

    # Filter: only keep directories that contain a docs/ subdirectory
    sites = [];
    for d in dirs:
        if not os.path.isdir(d):
            continue;
        if os.path.isdir(os.path.join(d, CONFIG["docs_subdir"])):
            sites.append(os.path.abspath(d));

    return sites;


def select_site():
    """Interactive site selection. Returns the chosen site root path."""
    sites = discover_sites();

    if not sites:
        print("  ERROR: No Docusaurus sites found.");
        print(f"    Windows: looked for {CONFIG['windows_pattern']} with docs/ subdirectory");
        print(f"    Linux:   looked for {CONFIG['linux_pattern']} with docs/ subdirectory");
        sys.exit(1);

    if len(sites) == 1:
        return sites[0];

    print("  Available sites:\n");
    for i, site in enumerate(sites):
        name = os.path.basename(site);
        print(f"    [{i + 1}] {name}  ({site})");

    while True:
        print();
        try:
            choice = input("  Select site number: ").strip();
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.");
            sys.exit(0);

        if not choice:
            continue;

        try:
            index = int(choice) - 1;
        except ValueError:
            print("  Invalid input. Enter a number.");
            continue;

        if 0 <= index < len(sites):
            return sites[index];
        print(f"  Out of range. Enter 1-{len(sites)}.");


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def scan_and_fix(site_root, dry_run=False):
    """Scan docs directory, detect non-ASCII filenames, and inject slug front matter."""
    docs_root = os.path.join(site_root, CONFIG["docs_subdir"]);

    if not os.path.isdir(docs_root):
        print(f"  ERROR: docs directory not found: {docs_root}");
        sys.exit(1);

    print(f"  Scanning: {docs_root}\n");

    stats = {
        "total": 0,
        "needs_fix": 0,
        "skipped_has_slug": 0,
        "skipped_no_frontmatter": 0,
        "fixed": 0,
        "angle_brackets": 0,
    };

    for rel_dir, fname in collect_files(docs_root):
        stats["total"] += 1;
        filepath = os.path.join(docs_root, rel_dir, fname);
        ext = os.path.splitext(fname)[1].lower();

        # --- Phase 1: Fix bare angle brackets for MDX (md files only, not mdx) ---
        if ext == ".md" and fix_mdx_angle_brackets(filepath, dry_run=dry_run):
            stats["angle_brackets"] += 1;
            action = "DRY-RUN" if dry_run else "FIXED";
            print(f"  [{action}] {os.path.join(rel_dir, fname)}  ->  escaped angle brackets");

        # --- Phase 2: Fix non-ASCII slug (non-ASCII filenames only) ---
        if not has_non_ascii(fname):
            continue;

        stats["needs_fix"] += 1;

        # Build slug
        slug_stem = extract_slug_stem(fname);
        # Normalize rel_dir: replace backslashes, strip leading dot
        dir_part = rel_dir.replace("\\", "/");
        if dir_part == ".":
            slug = f"/{slug_stem}";
        else:
            slug = f"/{dir_part}/{slug_stem}";

        # Check if file already has a slug
        existing_slug = get_existing_slug(filepath);
        if existing_slug is not None:
            stats["skipped_has_slug"] += 1;
            print(f"  [skip] {os.path.join(rel_dir, fname)}  (slug: {existing_slug})");
            continue;

        # Check if file has front matter (without slug)
        if has_frontmatter(filepath):
            stats["skipped_no_frontmatter"] += 1;
            print(f"  [warn] {os.path.join(rel_dir, fname)}  (has front matter but no slug)");
            continue;

        # Inject front matter
        stats["fixed"] += 1;
        action = "DRY-RUN" if dry_run else "FIXED";
        print(f"  [{action}] {os.path.join(rel_dir, fname)}  ->  slug: {slug}");

        if not dry_run:
            inject_frontmatter(filepath, slug);

    # Summary
    print(f"\n  --- Summary ---");
    print(f"  Total files scanned:  {stats['total']}");
    print(f"  Angle brackets fixed: {stats['angle_brackets']}");
    print(f"  Non-ASCII filenames:  {stats['needs_fix']}");
    print(f"  Already has slug:     {stats['skipped_has_slug']}");
    print(f"  Has FM but no slug:   {stats['skipped_no_frontmatter']}");
    print(f"  Slugs fixed this run: {stats['fixed']}");


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Docusaurus Path Fixer ===\n");

    parser = argparse.ArgumentParser(
        description="Fix Docusaurus slug errors caused by non-ASCII filenames."
    );
    parser.add_argument(
        "--site",
        default=None,
        help="Path to Docusaurus site root. If omitted, interactive selection is shown.",
    );
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files.",
    );
    args = parser.parse_args();

    # Determine site root
    if args.site:
        site_root = os.path.abspath(args.site);
    else:
        site_root = select_site();

    print(f"  Site root: {site_root}");
    print(f"  Dry run:   {args.dry_run}\n");

    if not os.path.isdir(site_root):
        print(f"  ERROR: site root not found: {site_root}");
        sys.exit(1);

    scan_and_fix(site_root, dry_run=args.dry_run);

    print(f"\n=== Done ===");


if __name__ == "__main__":
    main();
