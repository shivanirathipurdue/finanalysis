#!/usr/bin/env python3
"""
FIN 67110 - Spinoff Seeker Unit Test Suite (Lab 06 Contract Verification)
Verifies all seeker procedural rules on synthetic/made-up test data:
  1. Drop rule: Form 10 without info statement or fund/shell is dropped with reason & filing cited.
  2. Pricing rule: First price is after distribution date, NEVER a when-issued price.
  3. Registry rule: Confirmed facts recorded; missing facts stay blank and are never estimated.
  4. Ranking rule: Names in window scored by declared factors.
  5. Weight zeroing rule: Setting a factor weight to 0.0 zeroes its points without altering other factors.
  6. Ending rule: Last line must be 'screens, not recommendations'.
"""

import copy
import sys
from datetime import datetime, timedelta
from pathlib import Path

import seeker


def get_mock_candidates():
    """Synthetic/made-up test data (zero company names hardcoded)."""
    return [
        {
            "name": "Alpha SpinCo",
            "ticker": "ALPH",
            "cik": "0009990001",
            "form_10_accn": "0009990001-26-000001",
            "has_information_statement": True,
            "is_fund_or_shell": False,
            "parent_name": "Parent Omega Inc.",
            "parent_cik": "0009990000",
            "distribution_ratio": "1 per 4",
            "record_date": "2026-07-10",
            "distribution_date": "2026-07-20",
            "has_cert": True,
            "has_trading_proof": True,
            "first_price": 45.00,
            "first_price_date": "2026-07-21",
            "raw_factors": {
                "size_relative_to_parent": 0.08,
                "initial_weakness": -0.15,
                "insider_buying": 3,
                "analyst_neglect": 0,
                "absolute_market_cap": 0.60,
            },
        },
        {
            "name": "Beta Fund LLC",
            "ticker": "BETA",
            "form_10_accn": "0009990002-26-000002",
            "has_information_statement": False,
            "is_fund_or_shell": True,
            "parent_distributing": False,
        },
        {
            "name": "Gamma Registrant Existing Shares",
            "ticker": "GAMM",
            "form_10_accn": "0009990003-26-000003",
            "has_information_statement": False,
            "is_fund_or_shell": False,
            "parent_distributing": False,
        },
        {
            "name": "Delta SpinCo Missing Date",
            "ticker": "DELT",
            "form_10_accn": "0009990004-26-000004",
            "has_information_statement": True,
            "is_fund_or_shell": False,
            "parent_name": "Parent Epsilon Corp.",
            "distribution_ratio": "1 per 10",
            "record_date": "",
            "distribution_date": "",  # missing date
            "has_cert": True,
            "has_trading_proof": False,
        },
    ]


def run_tests():
    print("=" * 80)
    print("FIN 67110 - LAB 06 SPINOFF SEEKER TEST SUITE")
    print("=" * 80)

    # 1. Test Drop Rule
    print("\n[TEST 1 / 6] Verifying Drop Rule on Non-Spinoff Filings...")
    s1 = seeker.SpinoffSeeker("2025-11-01")
    s1.run_screen(get_mock_candidates())
    dropped_names = [d["name"] for d in s1.dropped]
    assert "Beta Fund LLC" in dropped_names, "Fund/shell must be dropped."
    assert "Gamma Registrant Existing Shares" in dropped_names, "Form 10 with no info stmt must be dropped."
    for d in s1.dropped:
        assert d["reason"], "Every dropped filing must carry a stated reason."
        assert d["filing"], "Every dropped filing must cite its Form 10 accession."
    print(">>> TEST 1 PASSED: Non-spinoffs dropped with explicit reasons and filing citations.")

    # 2. Test Pricing Rule (First close AFTER distribution, never when-issued)
    print("\n[TEST 2 / 6] Verifying Pricing Rule (Post-Distribution Close Only)...")
    assert len(s1.ranked) > 0, "Candidate Alpha SpinCo must be ranked."
    alpha = s1.ranked[0]
    dist_date = datetime.strptime(alpha["dist_date"], "%Y-%m-%d").date()
    price_date = datetime.strptime(alpha["price_date"], "%Y-%m-%d").date()
    assert price_date > dist_date, f"Price date ({price_date}) must be strictly after distribution date ({dist_date})."
    print(f">>> TEST 2 PASSED: Price date ({price_date}) is after distribution date ({dist_date}); when-issued avoided.")

    # 3. Test Fact Registry & Missing Facts Never Estimated
    print("\n[TEST 3 / 6] Verifying Fact Registry & Missing Fact Integrity...")
    reg_delta = [r for r in s1.registry if r["name"] == "Delta SpinCo Missing Date"]
    assert len(reg_delta) == 1
    d_entry = reg_delta[0]
    assert d_entry["distribution_date"] == "", "Missing distribution date must remain blank in registry."
    assert d_entry["record_date"] == "", "Missing record date must remain blank in registry."
    print(">>> TEST 3 PASSED: Missing facts remain blank in registry; never estimated.")

    # 4. Test Final Report Ending Line
    print("\n[TEST 4 / 6] Verifying Required Concluding Line...")
    report_text = s1.run_screen(get_mock_candidates())
    assert report_text.strip().endswith("screens, not recommendations"), "Report must end with 'screens, not recommendations'."
    print(">>> TEST 4 PASSED: Report concludes with 'screens, not recommendations'.")

    # 5. Test Factor Scoring Breakdown
    print("\n[TEST 5 / 6] Verifying Factor Scoring and Points Breakdown...")
    assert "scores" in alpha, "Candidate must output scores per factor."
    assert alpha["total_points"] > 0, "Candidate total points must be positive."
    recomputed_total = sum(alpha["scores"].values())
    assert abs(recomputed_total - alpha["total_points"]) < 0.15, "Total points must equal sum of factor points."
    print(f">>> TEST 5 PASSED: Factor points sum ({recomputed_total:.1f}) matches total points ({alpha['total_points']}).")

    # 6. Test Factor Weight Zeroing Rule
    print("\n[TEST 6 / 6] Verifying Weight Zeroing (Points become 0 without affecting other factors)...")
    # Clone factors config and set 'initial_weakness' weight to 0.0
    zero_factors_cfg = copy.deepcopy(s1.factors_cfg)
    for f in zero_factors_cfg["factors"]:
        if f["name"] == "initial_weakness":
            f["weight"] = 0.0

    s_zero = seeker.SpinoffSeeker("2025-11-01")
    s_zero.factors_cfg = zero_factors_cfg
    s_zero.factors = zero_factors_cfg["factors"]
    s_zero.run_screen(get_mock_candidates())

    alpha_zero = s_zero.ranked[0]
    assert alpha_zero["scores"]["initial_weakness"] == 0.0, "Zero-weighted factor points must become 0.0."
    assert alpha_zero["scores"]["insider_buying"] == alpha["scores"]["insider_buying"], "Unmodified factor points must remain identical."
    print(f">>> TEST 6 PASSED: Zeroing weight removed factor points ({alpha_zero['scores']['initial_weakness']}) while preserving other factors ({alpha_zero['scores']['insider_buying']}).")

    print("\n" + "=" * 80)
    print("ALL 6 UNIT TESTS PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
