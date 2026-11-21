#!/usr/bin/env python3
"""
FIN 67110 - Lab 07 & Lab 08 Seeded Error Test Suite for The Hook
Tests that:
1. Clean worksheet passes silently (exit code 0).
2. Seeded worksheet (+ $1 discrepancy) is caught, hook refuses 'done' (exit code 1) and names the failing line.
3. Clean unified final report passes silently (exit code 0).
4. Seeded final report (+ $1 discrepancy) is caught, hook refuses 'done' (exit code 1) and names the failing line.
"""

import sys
import subprocess
from pathlib import Path


def run_seeded_error_test():
    base_dir = Path(__file__).resolve().parent
    run_dir = base_dir / "BHSL_20261110_160000"
    clean_worksheet = run_dir / "worksheet.md"
    seeded_worksheet = run_dir / "worksheet_seeded_error.md"
    clean_report = run_dir / "final_report.md"
    seeded_report = run_dir / "final_report_seeded_error.md"

    if not clean_worksheet.exists():
        print(f"Error: Clean worksheet not found at {clean_worksheet}", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("FIN 67110 - THE HOOK SEEDED ERROR VERIFICATION SUITE (LAB 07 & LAB 08)")
    print("=" * 80)

    # 1. Test Clean Worksheet
    print("\n[TEST 1 / 4] Testing Clean Worksheet with Hook...")
    res_clean = subprocess.run(
        [sys.executable, str(base_dir / "hook.py"), str(clean_worksheet)],
        capture_output=True,
        text=True
    )
    assert res_clean.returncode == 0, f"Clean worksheet must pass hook silently. Stderr: {res_clean.stderr}"
    print(">>> TEST 1 PASSED: Clean worksheet verified silently (exit code 0).")

    # 2. Create Seeded Error Worksheet (+$1.00 tampering)
    print("\n[TEST 2 / 4] Testing Seeded Error Worksheet (+$1 discrepancy)...")
    with open(clean_worksheet, "r", encoding="utf-8") as f:
        ws_content = f.read()

    assert "$140,000,000.00" in ws_content, "Target string $140,000,000.00 not found in worksheet."
    ws_seeded = ws_content.replace("$140,000,000.00", "$140,000,001.00", 1)

    with open(seeded_worksheet, "w", encoding="utf-8") as f:
        f.write(ws_seeded)

    res_ws_seeded = subprocess.run(
        [sys.executable, str(base_dir / "hook.py"), str(seeded_worksheet)],
        capture_output=True,
        text=True
    )

    assert res_ws_seeded.returncode != 0, "Hook must REFUSE 'done' on seeded error (non-zero exit code)."
    assert "[HOOK REFUSAL]" in res_ws_seeded.stderr or "[HOOK REFUSAL]" in res_ws_seeded.stdout, "Hook output must declare refusal."
    assert "Line" in (res_ws_seeded.stderr + res_ws_seeded.stdout), "Hook must name the failing line number."

    print(">>> TEST 2 PASSED: Hook refused 'done' on seeded worksheet copy!")
    print("Captured Refusal Output:")
    print(res_ws_seeded.stderr.strip())

    # 3. Test Clean Final Report
    print("\n[TEST 3 / 4] Testing Clean Final Report with Hook...")
    res_rep_clean = subprocess.run(
        [sys.executable, str(base_dir / "hook.py"), str(clean_report)],
        capture_output=True,
        text=True
    )
    assert res_rep_clean.returncode == 0, f"Clean final report must pass hook silently. Stderr: {res_rep_clean.stderr}"
    print(">>> TEST 3 PASSED: Clean final report verified silently (exit code 0).")

    # 4. Create Seeded Error Final Report (+$1.00 tampering)
    print("\n[TEST 4 / 4] Testing Seeded Error Final Report (+$1 discrepancy)...")
    with open(clean_report, "r", encoding="utf-8") as f:
        rep_content = f.read()

    assert "$140,000,000.00" in rep_content, "Target string $140,000,000.00 not found in final report."
    rep_seeded = rep_content.replace("$140,000,000.00", "$140,000,001.00", 1)

    with open(seeded_report, "w", encoding="utf-8") as f:
        f.write(rep_seeded)

    res_rep_seeded = subprocess.run(
        [sys.executable, str(base_dir / "hook.py"), str(seeded_report)],
        capture_output=True,
        text=True
    )

    assert res_rep_seeded.returncode != 0, "Hook must REFUSE 'done' on seeded report error (non-zero exit code)."
    assert "[HOOK REFUSAL]" in res_rep_seeded.stderr or "[HOOK REFUSAL]" in res_rep_seeded.stdout, "Hook output must declare refusal."
    assert "Line" in (res_rep_seeded.stderr + res_rep_seeded.stdout), "Hook must name the failing line number."

    print(">>> TEST 4 PASSED: Hook refused 'done' on seeded final report copy!")
    print("Captured Refusal Output:")
    print(res_rep_seeded.stderr.strip())

    print("\n" + "=" * 80)
    print("ALL HOOK TESTS PASSED: Clean outputs silent; Seeded copies refused with failing lines named!")
    print("=" * 80)


if __name__ == "__main__":
    run_seeded_error_test()
