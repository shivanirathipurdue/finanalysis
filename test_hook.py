#!/usr/bin/env python3
"""
FIN 67110 - Lab 07 Seeded Error Test for The Hook
Tests that:
1. Clean worksheet passes silently (exit code 0).
2. Seeded copy (+ $1 discrepancy) is caught, hook refuses 'done' (exit code 1) and names the failing line.
"""

import sys
import subprocess
from pathlib import Path


def run_seeded_error_test():
    base_dir = Path(__file__).resolve().parent
    run_dir = base_dir / "BHSL_20261110_160000"
    clean_worksheet = run_dir / "worksheet.md"
    seeded_worksheet = run_dir / "worksheet_seeded_error.md"

    if not clean_worksheet.exists():
        print(f"Error: Clean worksheet not found at {clean_worksheet}", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("FIN 67110 - LAB 07 HOOK SEEDED ERROR VERIFICATION SUITE")
    print("=" * 80)

    # 1. Test Clean Worksheet
    print("\n[TEST 1 / 2] Testing Clean Worksheet with Hook...")
    res_clean = subprocess.run(
        [sys.executable, str(base_dir / "hook.py"), str(clean_worksheet)],
        capture_output=True,
        text=True
    )
    assert res_clean.returncode == 0, f"Clean worksheet must pass hook silently. Stderr: {res_clean.stderr}"
    print(">>> TEST 1 PASSED: Clean worksheet verified silently (exit code 0).")

    # 2. Create Seeded Error Worksheet (+$1.00 tampering)
    print("\n[TEST 2 / 2] Testing Seeded Error Copy (+$1 discrepancy)...")
    with open(clean_worksheet, "r", encoding="utf-8") as f:
        content = f.read()

    # Tamper with $140,000,000.00 -> $140,000,001.00
    assert "$140,000,000.00" in content, "Target string $140,000,000.00 not found in worksheet."
    seeded_content = content.replace("$140,000,000.00", "$140,000,001.00", 1)

    with open(seeded_worksheet, "w", encoding="utf-8") as f:
        f.write(seeded_content)

    res_seeded = subprocess.run(
        [sys.executable, str(base_dir / "hook.py"), str(seeded_worksheet)],
        capture_output=True,
        text=True
    )

    assert res_seeded.returncode != 0, "Hook must REFUSE 'done' on seeded error (non-zero exit code)."
    assert "[HOOK REFUSAL]" in res_seeded.stderr or "[HOOK REFUSAL]" in res_seeded.stdout, "Hook output must declare refusal."
    assert "Line" in (res_seeded.stderr + res_seeded.stdout), "Hook must name the failing line number."

    print(">>> TEST 2 PASSED: Hook refused 'done' on seeded error copy!")
    print("Captured Refusal Output:")
    print(res_seeded.stderr.strip())

    print("\n" + "=" * 80)
    print("ALL HOOK TESTS PASSED: Clean worksheet silent; Seeded copy refused and named line!")
    print("=" * 80)


if __name__ == "__main__":
    run_seeded_error_test()
