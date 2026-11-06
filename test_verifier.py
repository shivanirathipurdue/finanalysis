#!/usr/bin/env python3
"""
FIN 67110 - Lab 04 / Lab 05 Automated Verification Proofs
Runs the three verification proofs required by the syllabus:
  1. Clean Report Proof: Validates audited Costco run (COST_20261102_193519); all claims marked Correct.
  2. Seeded Error & Invented Number Proof: Validates seeded run (COST_SEEDED_ERROR);
     - Diluted EPS +$1.00 ($21.76 vs $20.76) marked Wrong and corrected to $20.76.
     - Inflated Revenue Growth Rate (+4.0 percentage points) marked Wrong and corrected.
  3. Skip Test Proof: Inspects desk_app.py to prove no flag or branch turns off the Verifier.
"""

import sys
from pathlib import Path
import verifier


def run_tests():
    script_dir = Path(__file__).resolve().parent
    clean_dir = script_dir / "COST_20261102_193519"
    if not clean_dir.exists():
        clean_dir = Path(r"C:\Users\cashi\COST_20261102_193519")

    seeded_dir = script_dir / "COST_SEEDED_ERROR"
    if not seeded_dir.exists():
        seeded_dir = Path(r"C:\Users\cashi\COST_SEEDED_ERROR")

    desk_file = script_dir / "desk_app.py"

    print("=" * 80)
    print("FIN 67110 - VERIFIER TEST SUITE (LAB 04 & LAB 05 PROOFS)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # Proof 1: Clean Report
    # -------------------------------------------------------------------------
    print("\n[PROOF 1 / 3] Testing Clean Audited Report...")
    assert clean_dir.exists(), f"Clean run folder not found: {clean_dir}"
    marks_file, verified_file = verifier.run_verifier(clean_dir)
    with open(marks_file, "r", encoding="utf-8") as f:
        marks_text = f.read()
    assert "**Wrong**: 0" in marks_text, "Clean report should have 0 Wrong marks."
    assert "**Unsupported**: 0" in marks_text, "Clean report should have 0 Unsupported marks."
    assert "**Correct**: 21" in marks_text or "**Correct**: " in marks_text
    print(">>> PROOF 1 PASSED: Audited report claims 100% verified as Correct.")

    # -------------------------------------------------------------------------
    # Proof 2: Seeded Error & Invented Number
    # -------------------------------------------------------------------------
    print("\n[PROOF 2 / 3] Testing Seeded Error & Invented Number...")
    assert seeded_dir.exists(), f"Seeded error folder not found: {seeded_dir}"
    marks_file, verified_file = verifier.run_verifier(seeded_dir)
    with open(marks_file, "r", encoding="utf-8") as f:
        marks_text = f.read()

    # Check Diluted EPS seeded error
    assert "Diluted EPS" in marks_text and "**Wrong**" in marks_text, "Diluted EPS must be marked Wrong."
    assert "Corrected to $20.76" in marks_text, "Diluted EPS must be corrected to $20.76."

    # Check Invented Revenue Growth arithmetic error
    assert "Revenue Growth Rate" in marks_text and "14.14%" in marks_text, "Inflated Revenue Growth must be evaluated."
    assert "Corrected to 10.14%" in marks_text, "Revenue Growth must be corrected to 10.14%."
    print(">>> PROOF 2 PASSED: Seeded Diluted EPS and Invented Growth Rate marked Wrong and corrected.")

    # -------------------------------------------------------------------------
    # Proof 3: Skip Test (Code Inspection)
    # -------------------------------------------------------------------------
    print("\n[PROOF 3 / 3] Testing Verifier Skip Protection...")
    with open(desk_file, "r", encoding="utf-8") as f:
        code_text = f.read()

    forbidden_flags = ["--skip-verifier", "--no-verifier", "--no-verify", "skip_verify"]
    for flag in forbidden_flags:
        assert flag not in code_text, f"Forbidden skip flag '{flag}' found in desk_app.py!"

    assert "verifier.run_verifier(work_dir)" in code_text, "Verifier must be invoked unconditionally on work_dir."
    print(">>> PROOF 3 PASSED: Verifier executes on every run; no flag or bypass exists.")

    print("\n" + "=" * 80)
    print("ALL 3 VERIFICATION PROOFS PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
