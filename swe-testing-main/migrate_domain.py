"""
One-shot migration from the OLD Moodle domain to the NEW Moodle domain.
Run once, then delete this file (or keep it as a migration record).

Applies these substitutions across the entire repo:
  * Base URL
  * Admin credentials
  * Test-specific IDs (course / section / cmid / userid)

After running, every test file points at the NEW domain.
"""

import os
import re
import sys

ROOT = os.path.dirname(__file__)

# ---------------------------------------------------------------------------
# Substitutions (order matters: longest/most-specific first)
# ---------------------------------------------------------------------------
REPLACEMENTS = [
    # TC-003 (Teacher creates assignment) — course 425 → 10, section 2116 → 39
    ("course=425&sectionid=2116", "course=10&sectionid=39"),

    # TC-006 (Teacher creates quiz) — course 426 → 12, section 2121 → 39 *guess*
    ("course=426&sectionid=2121", "course=12&sectionid=39"),

    # TC-004 (Teacher grades student) — assignment cmid 1195 → 41 (userid stays 2)
    ("mod/assign/view.php?id=1195", "mod/assign/view.php?id=41"),
    # Level 1 grade test also navigates to a course view first (course 140 → 10)
    ("course/view.php?id=140", "course/view.php?id=10"),

    # TC-006 CSV: warm-up course view 2 → 11
    ("course/view.php?id=2,", "course/view.php?id=11,"),

    # Level 1 quiz Python — split COURSE_ID / SECTION_ID constants
    ("COURSE_ID  = 426", "COURSE_ID  = 12"),
    ("SECTION_ID = 2121", "SECTION_ID = 39"),   # *needs verification

    # Credentials — admin username + password
    ("phuc.nguyen0310@hcmut.edu.vn", "sang.truong2005@hcmut.edu.vn"),
    ("Huuphuc0310@", "Abcdxyz12@"),

    # Base URL — must be LAST so the above more-specific URLs win first
    ("https://ihatetesting.moodlecloud.com", "https://xuansang1234.moodlecloud.com"),
    ("ihatetesting.moodlecloud.com",         "xuansang1234.moodlecloud.com"),
]

# Files to patch
TARGETS = [
    # Level 1
    "level1/test_add_user_level1.py",
    "level1/test_course_level1.py",
    "level1/test_assign_level1.py",
    "level1/test_grade_level1.py",
    "level1/test_event_level1.py",
    "level1/test_quiz_level1.py",
    # Level 2
    "level2/test_level2.py",
    "level2/test_data_tc001_level2.csv",
    "level2/test_data_tc002_level2.csv",
    "level2/test_data_tc003_level2.csv",
    "level2/test_data_tc004_level2.csv",
    "level2/test_data_tc005_level2.csv",
    "level2/test_data_tc006_level2.csv",
    # NFR
    "non_functional/test_nfr_01_login_perf_sec.py",
    "non_functional/test_nfr_02_login_perf_a11y.py",
    "non_functional/test_nfr_03_login_sec_a11y.py",
    "non_functional/test_nfr_04_quiz_perf_sec.py",
    "non_functional/test_nfr_05_quiz_perf_a11y.py",
    "non_functional/test_nfr_06_quiz_sec_a11y.py",
    # Utilities
    "cleanup_moodle.py",
    "run_all.ps1",
]


def patch_file(rel_path: str) -> dict:
    full = os.path.join(ROOT, rel_path)
    if not os.path.exists(full):
        return {"path": rel_path, "status": "MISSING", "changes": 0}
    with open(full, "r", encoding="utf-8") as f:
        original = f.read()
    new = original
    changes = 0
    for old, repl in REPLACEMENTS:
        if old in new:
            count = new.count(old)
            new = new.replace(old, repl)
            changes += count
    if new == original:
        return {"path": rel_path, "status": "no-change", "changes": 0}
    with open(full, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    return {"path": rel_path, "status": "patched", "changes": changes}


def main():
    print(f"Migrating {len(TARGETS)} files from old -> new Moodle domain...")
    print("-" * 72)
    total = 0
    for t in TARGETS:
        r = patch_file(t)
        marker = {"patched": "OK ", "no-change": " . ", "MISSING": "!! "}[r["status"]]
        print(f"  {marker} {r['path']:55s}  {r['changes']:>4} change(s)")
        total += r["changes"]
    print("-" * 72)
    print(f"Total substitutions applied: {total}")
    print()
    print("VERIFY MANUALLY (best-guess values):")
    print("   * TC-006 SECTION_ID set to 39 (same as TC-003); your real value may differ.")
    print("     Files to check: level1/test_quiz_level1.py, level2/test_data_tc006_level2.csv")


if __name__ == "__main__":
    main()
