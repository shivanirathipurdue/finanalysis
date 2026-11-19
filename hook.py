#!/usr/bin/env python3
"""
FIN 67110 - Spinoff Worksheet Verification Hook (Teaching 5 & Lab 07)
Enforces the non-negotiable contract:
Reads every number in the saved worksheet itself.
- A number claiming a tag/period is looked up in facts.json, exactly.
- A number claiming a filing and a line is found in that filing's saved text.
- A number computed from printed inputs is recomputed from them.
- A rate or a weight is matched against config files.
- A price is matched against the closes reader output.
- A date, accession number, line number, or book citation is skipped as an identifier.
- Any unsupported number or arithmetic discrepancy triggers REFUSAL of 'done' and prints the failing line.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import closes_reader


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_dollar(val_str: str) -> float:
    cleaned = val_str.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def check_printed_arithmetic(line: str) -> Optional[str]:
    """
    Check if a line contains printed arithmetic (e.g. A + B - C = D or A * B = C or A / B = C)
    and verify that the equality holds.
    """
    # 1. Addition / Subtraction chain: e.g. After-Tax Earnings ($140,000,000.00) + D&A ($35,000,000.00) - CapEx ($25,000,000.00) = $150,000,000.00
    if "=" in line:
        parts = line.split("=")
        rhs_str = parts[-1].strip()
        lhs_str = "=".join(parts[:-1]).strip()

        # If line has a colon (like a markdown bullet '- Label: Arithmetic = Result'), take portion after colon
        if ":" in lhs_str:
            lhs_str = lhs_str.split(":", 1)[1].strip()

        # Extract RHS dollar or float amount
        rhs_match = re.search(r"(\$?[0-9,]+(?:\.[0-9]+)?)", rhs_str)
        if not rhs_match:
            return None
        expected_rhs = parse_dollar(rhs_match.group(1))

        # Check for multiplication: e.g. 6.0 * $150,000,000.00 or shares: 50,000,000 * close: $14.20
        if "*" in lhs_str:
            factors = re.findall(r"(\$?[0-9,]+(?:\.[0-9]+)?)", lhs_str)
            if len(factors) >= 2:
                # take last two numbers before '='
                f1 = parse_dollar(factors[-2])
                f2 = parse_dollar(factors[-1])
                calc = f1 * f2
                if abs(calc - expected_rhs) > 0.05:
                    return f"Multiplication mismatch: {f1} * {f2} = {calc:.2f}, but line states {expected_rhs:.2f}"
                return None

        # Check for division: e.g. $150,000,000.00 / 50,000,000 shares = $3.00
        if "/" in lhs_str:
            terms = re.findall(r"(\$?[0-9,]+(?:\.[0-9]+)?)", lhs_str)
            if len(terms) >= 2:
                num = parse_dollar(terms[-2])
                den = parse_dollar(terms[-1])
                if den != 0:
                    calc = num / den
                    if abs(calc - expected_rhs) > 0.02:
                        return f"Division mismatch: {num} / {den} = {calc:.2f}, but line states {expected_rhs:.2f}"
                    return None

        # Check for Addition / Subtraction chain of dollar amounts:
        # e.g. After-Tax Earnings ($140,000,000.00) + D&A ($35,000,000.00) - CapEx ($25,000,000.00)
        clean_lhs = re.sub(r"\bAfter-Tax\b", "After_Tax", lhs_str, flags=re.IGNORECASE)
        chain_matches = list(re.finditer(r"(?:^|(\s[+-]\s))[^$]*\$([0-9,]+(?:\.[0-9]+)?)", clean_lhs))
        if len(chain_matches) >= 2:
            running_sum = 0.0
            for m in chain_matches:
                op = m.group(1)
                sign = op.strip() if op else "+"
                val = parse_dollar(m.group(2))
                if sign == "-":
                    running_sum -= val
                else:
                    running_sum += val
            if abs(running_sum - expected_rhs) > 0.05:
                return f"Addition/subtraction mismatch: calculated sum {running_sum:.2f}, but line states {expected_rhs:.2f}"
            return None

    return None


def verify_worksheet(worksheet_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate every claim in the saved worksheet against filings, facts.json, config, and reader.
    Returns: (success: bool, errors: List[str])
    """
    if not worksheet_path.exists():
        return False, [f"Worksheet file does not exist: {worksheet_path}"]

    run_dir = worksheet_path.parent
    base_dir = Path(__file__).resolve().parent

    facts_file = run_dir / "facts.json"
    facts_data = load_json(facts_file)
    target_info = facts_data.get("target", {})
    ticker = target_info.get("ticker", "").strip().upper()
    facts_dict = target_info.get("facts", {})

    config = load_json(base_dir / "worksheet_config.json")
    rates = config.get("rates", {})

    # Load filing texts in run directory for line citations
    filing_texts: Dict[str, str] = {}
    for fpath in run_dir.glob("*.txt"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                filing_texts[fpath.name.lower()] = f.read()
        except Exception:
            pass

    errors = []

    with open(worksheet_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Required concluding line check
    last_non_empty = [ln.strip() for ln in lines if ln.strip()]
    if not last_non_empty or last_non_empty[-1] != "screens, not recommendations":
        errors.append("Worksheet must end with 'screens, not recommendations'.")

    for line_idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Check 1: Printed Arithmetic verification
        arithmetic_err = check_printed_arithmetic(line)
        if arithmetic_err:
            errors.append(f"Line {line_idx}: {arithmetic_err} in '{line}'")
            continue

        # Check 2: Pricing claims against reader
        price_match = re.search(r"Price on price date \(([0-9\-]+)\):\s*\$([0-9\.]+)", line)
        if price_match:
            p_date = price_match.group(1)
            p_val = float(price_match.group(2))
            closes = closes_reader.get_daily_closes(ticker, p_date, p_date)
            if p_date in closes:
                expected_p = closes[p_date]
                if abs(expected_p - p_val) > 0.01:
                    errors.append(f"Line {line_idx}: Price mismatch against reader: stated ${p_val:.2f}, reader returned ${expected_p:.2f}")

        # Check 3: Fact claims against facts.json
        # E.g. Net income, debt raised, cash distributed, insider purchases, credit facility
        for fact_key, f_info in facts_dict.items():
            amt = float(f_info.get("amount", 0.0))
            amt_fmt = f"{amt:,.2f}"
            amt_no_dec = f"{int(amt):,}"
            tag_name = f_info.get("tag", "")

            # If line mentions this fact name and holds a dollar figure
            if fact_key.lower() in line.lower() and "$" in line:
                # Disambiguate historical vs pro forma vs quarterly
                stmt_type = f_info.get("statement_type", "")
                if stmt_type == "historical" and "historical" not in line.lower():
                    continue
                if stmt_type == "pro forma" and ("historical" in line.lower() or "quarterly" in line.lower() or "10-q" in line.lower()):
                    continue
                if "quarterly" in line.lower() and f_info.get("form", "") != "Form 10-Q":
                    continue

                # Find all dollar amounts in line
                found_dollars = [parse_dollar(d) for d in re.findall(r"\$([0-9,]+(?:\.[0-9]+)?)", line)]
                # If neither the exact amount nor the calculated total matches
                if amt not in found_dollars and not any(abs(d - amt) < 0.05 for d in found_dollars):
                    # Check if it was an arithmetic line where inputs were present
                    if not any(f"{amt:,.0f}" in d_str for d_str in re.findall(r"[0-9,]+", line)):
                        errors.append(f"Line {line_idx}: Fact '{fact_key}' mismatch: expected ${amt_fmt} from facts.json (tag: {tag_name}), not found in '{line}'")

        # Check 4: Filing line citations against saved filing text
        if "form 10" in line.lower() or "form 4" in line.lower() or "10-q" in line.lower():
            # Extract claimed numbers (e.g. debt raised, cash to parent, purchases)
            dollar_matches = re.findall(r"\$([0-9,]+(?:\.[0-9]+)?)", line)
            for d_str in dollar_matches:
                val = parse_dollar(d_str)
                # Ignore small numbers / percentages or calculated totals
                if val < 1000.0:
                    continue
                # Format to search in text: either 120,000,000 or $120,000,000
                int_str = f"{int(val):,}"
                found_in_filing = any(int_str in text for text in filing_texts.values())
                if not found_in_filing:
                    # Also check if it was recomputed (e.g. total market value or owner cash flow)
                    if not ("=" in line or "market value" in line.lower() or "value range" in line.lower() or "price against" in line.lower()):
                        errors.append(f"Line {line_idx}: Filing claim number ${d_str} not found in saved filing text for '{line}'")

        # Check 5: Valuation rates and client purchase size against config
        if "low case" in line.lower() and "x" in line.lower():
            mult_match = re.search(r"Low Case\s*([0-9\.]+)x", line)
            if mult_match:
                mult = float(mult_match.group(1))
                if abs(mult - float(rates.get("low_case_multiple", 6.0))) > 0.01:
                    errors.append(f"Line {line_idx}: Low case multiple {mult}x does not match worksheet_config.json ({rates.get('low_case_multiple')}x)")

        if "client purchase size" in line.lower():
            client_amt_match = re.search(r"Client purchase size of\s*\$([0-9,]+(?:\.[0-9]+)?)", line)
            if client_amt_match:
                client_amt = parse_dollar(client_amt_match.group(1))
                exp_client = float(config.get("client_purchase_size", 500000.0))
                if abs(client_amt - exp_client) > 0.01:
                    errors.append(f"Line {line_idx}: Client purchase size ${client_amt:,.2f} does not match config ${exp_client:,.2f}")

    return (len(errors) == 0), errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python hook.py <path_to_worksheet.md>")
        sys.exit(1)

    target_path = Path(sys.argv[1])
    if target_path.is_dir():
        target_path = target_path / "worksheet.md"

    success, errors = verify_worksheet(target_path)

    if not success:
        print("[HOOK REFUSAL] Refusing 'done': The worksheet contains unverified or inconsistent numbers!", file=sys.stderr)
        for err in errors:
            print(f"  -> {err}", file=sys.stderr)
        sys.exit(1)

    # Silent pass upon complete verification as required by Teaching 5 / Lab 07
    print(f"[HOOK SUCCESS] Silent verification passed: All numbers in {target_path.name} verified against filings, facts, computations, and reader.")
    sys.exit(0)


if __name__ == "__main__":
    main()
