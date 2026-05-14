"""
One-shot migration script: rewrite every hardcoded site-specific value across
the repo to point at the new Moodle instance.

Usage:
    python migrate_site.py

After it runs, all 24 files (6 Level-1 .py + 6 Level-2 .csv + 1 Level-2 .py +
6 NFR .py + cleanup + run_all.ps1 + README + report.tex + copilot-instructions)
are updated. Run pytest smoke test to verify.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# ─── Substitution table ───────────────────────────────────────────────────
SUBSTITUTIONS = [
    # 1. Base URL
    ("https://ihatetesting.moodlecloud.com", "https://xuansang1234.moodlecloud.com"),
    ("ihatetesting.moodlecloud.com",        "xuansang1234.moodlecloud.com"),

    # 2. Admin credentials
    ("phuc.nguyen0310@hcmut.edu.vn", "sang.truong2005@hcmut.edu.vn"),
    ("Huuphuc0310@",                  "Abcdxyz12@"),

    # 3. TC-003 assignment creation: course=425 sectionid=2116 -> course=10 sectionid=39
    ("course=425&sectionid=2116", "course=10&sectionid=39"),

    # 4. TC-006 quiz creation: course=426 sectionid=2121 -> course=12 sectionid=49 (NOTE: 49 is a guess)
    ("course=426&sectionid=2121", "course=12&sectionid=49"),

    # 5. TC-004 grader: cmid=1195 userid=2 -> cmid=41 userid=2 (userid unchanged from CSV)
    ("mod/assign/view.php?id=1195", "mod/assign/view.php?id=41"),
    # the standalone view URL used by TC-004 verification (Level 2 has it twice per row)
    ("/view.php?id=1195", "/view.php?id=41"),

    # 6. TC-006 view ("Announcements" verification) course id 2 -> 11
    #    (must be careful — `id=2` is also userid in TC-004; do that one first)
    ("course/view.php?id=2", "course/view.php?id=11"),

    # 7. Old TC-004 course view in test_grade_level1.py: id=140 -> id=10
    ("course/view.php?id=140", "course/view.php?id=10"),

    # 8. Quiz Level-1 hardcoded COURSE_ID/SECTION_ID
    ("COURSE_ID  = 426", "COURSE_ID  = 12"),
    ("SECTION_ID = 2121", "SECTION_ID = 49   # TODO verify section id of course 12"),
]

# Files we'll skip — binary, generated, or out-of-scope
SKIP_PATHS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv",
}
SKIP_EXTS = {".pyc", ".xlsx", ".pdf", ".png", ".jpg", ".jpeg", ".zip"}

# Only touch files of these types
INCLUDE_EXTS = {".py", ".csv", ".ps1", ".md", ".tex", ".sh"}

def should_visit(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    if any(p in SKIP_PATHS for p in parts):
        return False
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTS:
        return False
    return ext in INCLUDE_EXTS

def migrate_file(path: str) -> int:
    """Apply substitutions to one file. Returns number of replacements made."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return 0
    original = content
    total = 0
    for old, new in SUBSTITUTIONS:
        if old in content:
            n = content.count(old)
            content = content.replace(old, new)
            total += n
    if content != original:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
    return total

def main():
    by_file = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Prune skipped dirs in-place so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_PATHS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            # Don't migrate this script itself
            if rel == "migrate_site.py":
                continue
            if not should_visit(rel):
                continue
            n = migrate_file(full)
            if n:
                by_file[rel] = n

    if not by_file:
        print("No replacements made — already migrated?")
        return

    print(f"Migration complete — touched {len(by_file)} files:")
    print()
    for f in sorted(by_file):
        print(f"  {by_file[f]:>4}  {f}")
    print()
    print(f"Total replacements: {sum(by_file.values())}")

if __name__ == "__main__":
    main()
