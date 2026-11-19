#!/usr/bin/env python3
"""
FIN 67110 - Hit-Rate Table and Price Reaction Scorer (Teaching 6 & Lab 07)
Scans run folders, pulls pre-filing close and post-filing close using closes_reader,
computes the market reaction return, evaluates directional agreement, and prints
the hit-rate table. Practice runs are marked 'after'.
Ends with 'screens, not recommendations'.
"""

import sys
import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import closes_reader


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_run_reaction(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Score one run's directional view against price reaction."""
    facts_path = run_dir / "facts.json"
    worksheet_path = run_dir / "worksheet.md"
    report_path = run_dir / "report.md"

    if not facts_path.exists():
        return None

    facts_data = load_json(facts_path)
    target = facts_data.get("target", {})
    ticker = target.get("ticker", "").strip().upper()
    if not ticker:
        return None

    is_live = "live" in str(run_dir).lower()
    run_type = "live" if is_live else "practice (after)"

    # Determine filing timestamp
    folder_match = re.search(r"_(\d{4})(\d{2})(\d{2})_", run_dir.name)
    if "distribution_date" in target:
        filing_str = target["distribution_date"]
    elif folder_match:
        filing_str = f"{folder_match.group(1)}-{folder_match.group(2)}-{folder_match.group(3)}"
    else:
        filing_str = target.get("period_end", "2026-11-02")

    try:
        filing_dt = datetime.fromisoformat(f"{filing_str}T16:00:00")
    except ValueError:
        filing_dt = datetime(2026, 11, 2, 16, 0, 0)

    # Determine desk view
    desk_view = "More than price"
    if worksheet_path.exists():
        with open(worksheet_path, "r", encoding="utf-8") as f:
            ws_text = f.read()
            m = re.search(r"Directional view:\s*(More than price|Less than price)", ws_text, re.IGNORECASE)
            if m:
                desk_view = m.group(1).capitalize()
    elif report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            rep_text = f.read()
            if "Recommendation: Sell" in rep_text or "**Sell**" in rep_text:
                desk_view = "Less than price"
            else:
                desk_view = "More than price"

    # Pre-close (last close at or before filing time)
    pre_close, pre_date = closes_reader.get_last_close_before(ticker, filing_dt)

    # Post-close (first close after filing date)
    post_date_dt = filing_dt + timedelta(days=1)
    daily = closes_reader.get_daily_closes(
        ticker,
        post_date_dt.strftime("%Y-%m-%d"),
        (post_date_dt + timedelta(days=7)).strftime("%Y-%m-%d")
    )

    post_close = None
    post_date = "not available"
    if daily:
        first_post_d = sorted(daily.keys())[0]
        post_close = daily[first_post_d]
        post_date = first_post_d

    # Calculate reaction return
    if pre_close and post_close and pre_close > 0:
        ret_pct = ((post_close - pre_close) / pre_close) * 100.0
        reaction_dir = "Up" if ret_pct > 0 else ("Down" if ret_pct < 0 else "Flat")
        view_dir = "Up" if "More" in desk_view else "Down"
        agreed = (reaction_dir == view_dir)
        agree_str = "AGREE" if agreed else "DISAGREE"
    else:
        ret_pct = 0.0
        agree_str = "N/A"

    return {
        "ticker": ticker,
        "run_dir": run_dir.name,
        "run_type": run_type,
        "filing_date": filing_str,
        "pre_close": pre_close,
        "post_close": post_close,
        "ret_pct": ret_pct,
        "desk_view": desk_view,
        "agreement": agree_str
    }


def generate_hit_rate_table(base_dir: Path) -> str:
    """Scan all run folders and assemble the hit-rate report."""
    candidates_dirs = []
    # Search root and runs/practice / runs/live
    for d in base_dir.iterdir():
        if d.is_dir() and (d / "facts.json").exists():
            if "seeded_error" in d.name.lower():
                continue
            candidates_dirs.append(d)

    runs_folder = base_dir / "runs"
    if runs_folder.exists():
        for sub in runs_folder.rglob("*"):
            if sub.is_dir() and (sub / "facts.json").exists():
                if "seeded_error" in sub.name.lower():
                    continue
                if sub not in candidates_dirs:
                    candidates_dirs.append(sub)

    results = []
    # De-duplicate by ticker
    seen_tickers = set()
    for c in sorted(candidates_dirs, key=lambda x: x.name, reverse=True):
        row = evaluate_run_reaction(c)
        if row and row["ticker"] not in seen_tickers:
            seen_tickers.add(row["ticker"])
            results.append(row)

    lines = [
        "# Desk Hit-Rate Table (Pre-Filing vs. Post-Filing Reaction Scorecard)",
        "Framework: Teaching 6 — Scoring Directional Views Against Initial Market Reaction",
        "",
        "| Ticker | Run Type | Filing Date | Pre Close | Post Close | Reaction Return | Desk View | Score |",
        "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    scored_count = 0
    agree_count = 0

    for r in results:
        pre_str = f"${r['pre_close']:.2f}" if r["pre_close"] else "N/A"
        post_str = f"${r['post_close']:.2f}" if r["post_close"] else "N/A"
        ret_str = f"{r['ret_pct']:+.2f}%" if r["agreement"] != "N/A" else "N/A"

        if r["agreement"] in ["AGREE", "DISAGREE"]:
            scored_count += 1
            if r["agreement"] == "AGREE":
                agree_count += 1

        lines.append(
            f"| **{r['ticker']}** | {r['run_type']} | {r['filing_date']} | {pre_str} | {post_str} | {ret_str} | {r['desk_view']} | **{r['agreement']}** |"
        )

    hit_rate_pct = (agree_count / scored_count * 100.0) if scored_count > 0 else 50.0

    lines.extend([
        "",
        "## Summary Scorecard",
        f"- **Total Scored Runs**: {scored_count}",
        f"- **Agreed Directions**: {agree_count}",
        f"- **Desk Hit Rate**: **{hit_rate_pct:.1f}%**",
        "- **Base Rate Reference**: A pure coin-flip scores ~50.0% by chance.",
        "- **Horizon Note**: A one-day price reaction scores the initial market surprise, not the long-term value range.",
        "",
        "screens, not recommendations"
    ])

    return "\n".join(lines)


def main():
    base_dir = Path(__file__).resolve().parent
    table_md = generate_hit_rate_table(base_dir)
    print(table_md)

    output_file = base_dir / "hit_rate_table.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(table_md)
    print(f"\nHit rate table written to: {output_file}")


if __name__ == "__main__":
    main()
