"""
Map Level 1 expected_result wordings to Level 2 CSV files by test_case_id.
Both level 1 and level 2 share the same TC numbering and same input parameters,
so the expected error wording is identical — only the framework differs.
"""
import csv
import os

L1_DIR = os.path.join(os.path.dirname(__file__), "level1")
L2_DIR = os.path.join(os.path.dirname(__file__), "level2")

# (l1_name, l2_name) pairs
PAIRS = [
    ("test_data_tc001.csv",       "test_data_tc001_level2.csv"),
    ("test_data_tc002.csv",       "test_data_tc002_level2.csv"),
    ("test_data_tc003.csv",       "test_data_tc003_level2.csv"),
    ("test_data_tc004.csv",       "test_data_tc004_level2.csv"),
    ("test_data_tc005.csv",       "test_data_tc005_level2.csv"),
    ("test_data_tc006.csv",       "test_data_tc006_level2.csv"),
]

def load_l1_map(path):
    """Return {test_case_id: expected_result} from a Level-1 CSV."""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tc = row["test_case_id"].strip()
            out[tc] = row["expected_result"]
    return out

def patch_l2(l2_path, mapping):
    """Rewrite the L2 CSV replacing expected_result via mapping."""
    with open(l2_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    changed = 0
    for row in rows:
        tc = row["test_case_id"].strip()
        if tc in mapping and row.get("expected_result", "") != mapping[tc]:
            row["expected_result"] = mapping[tc]
            changed += 1
    with open(l2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return changed, len(rows)

if __name__ == "__main__":
    for l1_name, l2_name in PAIRS:
        l1_path = os.path.join(L1_DIR, l1_name)
        l2_path = os.path.join(L2_DIR, l2_name)
        if not os.path.exists(l1_path) or not os.path.exists(l2_path):
            print(f"SKIP {l1_name} <-> {l2_name} (missing)")
            continue
        mapping = load_l1_map(l1_path)
        changed, total = patch_l2(l2_path, mapping)
        print(f"{l2_name}: updated {changed}/{total} rows")
