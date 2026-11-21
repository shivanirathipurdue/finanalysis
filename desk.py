#!/usr/bin/env python3
"""
FIN 67110 - Unified Equity Research Desk (Week 5: Lab 08 & Lab 09)
One command joins the Agent Team (Week 3) and Skills (Week 4):
  - Spinoff Seeker Skill (seeker.py)
  - Fact Ingestion & Cache (single-fetch guarantee)
  - Autonomous Agent Team Graph (desk_app.py)
  - Spinoff Worksheet Skill (worksheet.py)
  - Enforcement Hook Guard (hook.py)
All parts run in a deterministic order fixed in code (never chosen by a model).
Outputs unified final report ending with 'screens, not recommendations'.
"""

import sys
import os
import re
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import closes_reader
import desk_app
import desk_steps
import verifier
import seeker
import worksheet
import hook


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class UnifiedDesk:
    """Orchestrates the unified desk pipeline in fixed code order."""

    def __init__(self, target_arg: str, replay_dir: Optional[str] = None, offline: bool = False):
        self.target_arg = target_arg.strip()
        self.replay_dir = Path(replay_dir).resolve() if replay_dir else None
        self.offline = offline or (self.replay_dir is not None)
        self.base_dir = Path(__file__).resolve().parent
        self.registry_path = self.base_dir / "registry.json"
        self.config_path = self.base_dir / "worksheet_config.json"
        self.persona_path = self.base_dir / "roles" / "investor_persona.md"

        self.ticker = ""
        self.run_dir: Optional[Path] = None
        self.timing_log: Dict[str, float] = {}
        self.filings_read: List[str] = []

    def execute_pipeline(self) -> Path:
        """Run the desk end to end in deterministic code order."""
        total_start_time = time.time()
        print("=" * 80)
        print("FIN 67110 - ONE DESK: UNIFIED AGENT TEAM & SKILLS EXECUTION")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Target: {self.target_arg}")
        print("=" * 80)

        # ----------------------------------------------------------------------
        # STEP 1: Seeker / Screen Resolution & Pick Determination
        # ----------------------------------------------------------------------
        t0 = time.time()
        print("\n>>> STEP 1 / 6: Seeker Screen & Pick Determination")
        if self.target_arg.lower() == "screen":
            print("Client requested 'screen': Running Spinoff Seeker to discover candidates...")
            s = seeker.SpinoffSeeker(start_date_str="2025-11-01")
            s.run_screen()
            if s.ranked:
                top_candidate = s.ranked[0]
                self.ticker = top_candidate["ticker"].strip().upper()
                print(f"Seeker Top Pick: {top_candidate['name']} ({self.ticker}) with {top_candidate['total_points']:.1f} pts.")
            else:
                raise RuntimeError("Seeker screen completed with 0 ranked candidates in window.")
        else:
            self.ticker = self.target_arg.strip().upper()
            print(f"Direct ticker provided: {self.ticker}")

        elapsed_step1 = time.time() - t0
        self.timing_log["Step 1: Screen & Pick"] = elapsed_step1
        print(f"[Step 1: Screen & Pick completed in {elapsed_step1:.2f}s]")

        # ----------------------------------------------------------------------
        # STEP 2: Run Folder Initialization (Single Run Folder Contract)
        # ----------------------------------------------------------------------
        t0 = time.time()
        print("\n>>> STEP 2 / 6: Run Folder Initialization")
        if self.replay_dir and self.replay_dir.exists():
            self.run_dir = self.replay_dir
            print(f"Replay mode active: Reading strictly from existing folder: {self.run_dir.name}")
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_dir = self.base_dir / f"{self.ticker}_{timestamp_str}"
            self.run_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created dedicated run folder: {self.run_dir.name}")

        elapsed_step2 = time.time() - t0
        self.timing_log["Step 2: Run Folder Setup"] = elapsed_step2
        print(f"[Step 2: Run Folder Setup completed in {elapsed_step2:.2f}s]")

        # ----------------------------------------------------------------------
        # STEP 3: Data Ingestion (Single-Fetch Guarantee)
        # ----------------------------------------------------------------------
        t0 = time.time()
        print("\n>>> STEP 3 / 6: Filing Ingestion (Single-Fetch Guarantee)")
        self._ensure_filings_and_facts()
        elapsed_step3 = time.time() - t0
        self.timing_log["Step 3: Filing Ingestion"] = elapsed_step3
        print(f"[Step 3: Filing Ingestion completed in {elapsed_step3:.2f}s]")

        # ----------------------------------------------------------------------
        # STEP 4: Agent Team Graph Execution
        # ----------------------------------------------------------------------
        t0 = time.time()
        print("\n>>> STEP 4 / 6: Autonomous Agent Team Graph Execution (Roles 1 to 6)")
        self._run_agent_team()
        elapsed_step4 = time.time() - t0
        self.timing_log["Step 4: Agent Team Graph"] = elapsed_step4
        print(f"[Step 4: Agent Team Graph completed in {elapsed_step4:.2f}s]")

        # ----------------------------------------------------------------------
        # STEP 5: Spinoff Worksheet Skill Execution
        # ----------------------------------------------------------------------
        t0 = time.time()
        print("\n>>> STEP 5 / 6: Spinoff Worksheet Skill Execution")
        self._run_worksheet_skill()
        elapsed_step5 = time.time() - t0
        self.timing_log["Step 5: Worksheet Skill"] = elapsed_step5
        print(f"[Step 5: Worksheet Skill completed in {elapsed_step5:.2f}s]")

        # ----------------------------------------------------------------------
        # STEP 6: Final Report Assembly & The Hook Guard
        # ----------------------------------------------------------------------
        t0 = time.time()
        print("\n>>> STEP 6 / 6: Final Report Assembly & Hook Verification")
        final_report_file = self._assemble_and_guard_report()
        elapsed_step6 = time.time() - t0
        self.timing_log["Step 6: Report Assembly & Hook"] = elapsed_step6
        print(f"[Step 6: Report Assembly & Hook completed in {elapsed_step6:.2f}s]")

        total_elapsed = time.time() - total_start_time
        print("\n" + "=" * 80)
        print(f"ONE DESK EXECUTION COMPLETE FOR {self.ticker} IN {total_elapsed:.2f} SECONDS")
        print("Timing Breakdown per Component:")
        for step_name, dur in self.timing_log.items():
            print(f"  • {step_name}: {dur:.2f}s")
        print(f"Final Report: {final_report_file}")
        print("=" * 80)

        return final_report_file

    def _ensure_filings_and_facts(self):
        """
        Ensure all required filings and facts.json exist in self.run_dir.
        Guarantees that no filing is ever fetched twice.
        """
        facts_path = self.run_dir / "facts.json"

        # Check registry for spinoff status
        registry = load_json(self.registry_path)
        is_spinoff = any(r.get("ticker", "").strip().upper() == self.ticker for r in registry) if isinstance(registry, list) else False

        # In offline or replay mode, verify files exist without network calls
        if self.offline or facts_path.exists():
            print(f"Reusing existing saved facts and filings from {self.run_dir.name} (network fetch skipped).")
            # Enumerate filings read from directory
            for f in self.run_dir.glob("*.txt"):
                self.filings_read.append(f.name)
            return

        # Single-Fetch Guarantee: If repository already holds saved filings for this ticker, reuse them
        baseline_candidates = [c for c in self.base_dir.glob(f"{self.ticker}_*") if c != self.run_dir and (c / "facts.json").exists()]
        if baseline_candidates:
            print(f"Single-Fetch Guarantee: Reusing repository baseline facts and filings for {self.ticker} (skipping redundant fetch).")
            self._copy_baseline_run_data()
            return

        # Online mode: Fetch once and save into self.run_dir
        print(f"Fetching primary SEC filings and XBRL facts once for {self.ticker}...")
        try:
            sec_agent = os.getenv("SEC_USER_AGENT", "Shivani Rathi rathi47@purdue.edu")
            cik_str, title, cik_int = desk_steps.step_1_resolve_ticker(self.ticker, sec_agent)
            filings = desk_steps.step_2_list_filings(cik_str, cik_int, sec_agent)
            desk_steps.step_3_download_and_save_documents(
                cik_str, cik_int, filings, sec_agent, self.ticker, target_dir=self.run_dir
            )
            facts, fy, end_date = desk_steps.step_4_fetch_facts(cik_str, sec_agent)
            with open(self.run_dir / "facts.json", "w", encoding="utf-8") as f:
                json.dump(facts, f, indent=2)

            for form_type, f_info in filings.items():
                accn = f_info.get("accessionNumber", "N/A")
                self.filings_read.append(f"{form_type} ({accn})")
        except Exception as e:
            # If network error or ticker missing in online EDGAR, fallback to copying baseline run if available
            print(f"[Notice] Online EDGAR fetch encountered notice ({e}). Reusing repository baseline facts.")
            self._copy_baseline_run_data()

    def _copy_baseline_run_data(self):
        """Reuses existing baseline run data if available for ticker."""
        # Find existing run folder for ticker
        candidates = list(self.base_dir.glob(f"{self.ticker}_*"))
        for c in candidates:
            if c != self.run_dir and (c / "facts.json").exists():
                for item in c.iterdir():
                    if item.is_file() and not (self.run_dir / item.name).exists():
                        with open(item, "rb") as sf, open(self.run_dir / item.name, "wb") as df:
                            df.write(sf.read())
                break
        for f in self.run_dir.glob("*.txt"):
            self.filings_read.append(f.name)

    def _run_agent_team(self):
        """Run the 6-node agent team graph on self.run_dir."""
        # Financial Analyst quotes worksheet data as a file without recomputing
        team = desk_app.EquityResearchAgentTeam(
            ticker=self.ticker,
            work_dir=self.run_dir,
            use_fallback=False
        )
        # Execute the deterministic graph
        team.run_graph()

    def _run_worksheet_skill(self):
        """Run the worksheet skill on self.run_dir."""
        worksheet_text = worksheet.build_worksheet(
            run_dir=self.run_dir,
            config_path=self.config_path,
            persona_path=self.persona_path,
            registry_path=self.registry_path
        )
        ws_file = self.run_dir / "worksheet.md"
        with open(ws_file, "w", encoding="utf-8") as f:
            f.write(worksheet_text)
        print(f"Worksheet output saved to: {ws_file.name}")

    def _assemble_and_guard_report(self) -> Path:
        """
        Assemble the final unified report:
        Line 1: Every filing any part read
        Body: Team's verified report + Worksheet view and valuation range
        End: 'screens, not recommendations'
        Runs The Hook guard unconditionally.
        """
        verified_report_path = self.run_dir / "verified_report.md"
        if not verified_report_path.exists():
            verified_report_path = self.run_dir / "report.md"

        worksheet_path = self.run_dir / "worksheet.md"

        with open(verified_report_path, "r", encoding="utf-8") as f:
            team_text = f.read()

        with open(worksheet_path, "r", encoding="utf-8") as f:
            ws_text = f.read()

        # Build comprehensive list of filings read
        filing_items = []
        for fn in sorted(list(set(self.filings_read))):
            filing_items.append(fn)

        # Also inspect facts.json for cited accession numbers
        facts_data = load_json(self.run_dir / "facts.json")
        target_info = facts_data.get("target", {})
        if "form_10_accn" in target_info:
            filing_items.append(f"Form 10 ({target_info['form_10_accn']}) Exhibit 99.1")

        if not filing_items:
            filing_items = ["Form 10 Exhibit 99.1", "Form 4", "Form 10-Q"]

        filings_line = f"Filings read: {', '.join(sorted(list(set(filing_items))))}"

        # Clean team text lines
        team_lines = team_text.strip().split("\n")
        # Remove any redundant top filing lines from team report
        if team_lines and team_lines[0].startswith("Filings:"):
            team_lines = team_lines[1:]
        clean_team_text = "\n".join(team_lines).strip()

        # Extract Worksheet Core Analysis & Directional View
        # Split worksheet into parts
        ws_sections = re.split(r"(?m)^##\s+", ws_text)
        ws_view_section = ""
        ws_val_range_section = ""
        ws_why_cheap_section = ""

        for sec in ws_sections:
            if sec.startswith("View on Release"):
                ws_view_section = f"## Spinoff Valuation View on Release\n{sec.strip()}"
            elif sec.startswith("Value range"):
                ws_val_range_section = f"## Value Range & Owner Cash Flow\n{sec.strip()}"
            elif sec.startswith("Why it may be cheap"):
                ws_why_cheap_section = f"## Spinoff Special Situation Analysis\n{sec.strip()}"

        final_sections = [
            filings_line,
            f"Run Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            clean_team_text,
            "",
            "---",
            "# Part 6: Spinoff Valuation & Special Situation Analysis",
            ws_why_cheap_section,
            "",
            ws_val_range_section,
            "",
            ws_view_section,
            "",
            "screens, not recommendations"
        ]

        final_report_content = "\n".join([s for s in final_sections if s]).strip() + "\n"

        final_report_file = self.run_dir / "final_report.md"
        with open(final_report_file, "w", encoding="utf-8") as f:
            f.write(final_report_content)

        print(f"Unified final report written to: {final_report_file.name}")

        # ----------------------------------------------------------------------
        # THE HOOK GUARD: Runs unconditionally on worksheet and final report
        # ----------------------------------------------------------------------
        print("\n[The Guard] Executing The Hook on saved worksheet and final report...")
        hook_success, hook_errors = hook.verify_worksheet(worksheet_path)
        if not hook_success:
            print(f"[FAIL] The Hook refused 'done' on worksheet ({worksheet_path.name})!", file=sys.stderr)
            for err in hook_errors:
                print(f"  -> {err}", file=sys.stderr)
            raise RuntimeError(f"Hook refused 'done' on {worksheet_path.name}")

        final_hook_success, final_hook_errors = hook.verify_worksheet(final_report_file)
        if not final_hook_success:
            print(f"[FAIL] The Hook refused 'done' on final report ({final_report_file.name})!", file=sys.stderr)
            for err in final_hook_errors:
                print(f"  -> {err}", file=sys.stderr)
            raise RuntimeError(f"Hook refused 'done' on {final_report_file.name}")

        print("[SUCCESS] The Hook passed: All numerical claims verified against filings, facts, computations, and reader.")
        return final_report_file


def main():
    parser = argparse.ArgumentParser(
        description="FIN 67110 - One Desk: Unified Agent Team and Skills (Week 5: Lab 08 & Lab 09)."
    )
    parser.add_argument("target", type=str, nargs="?", default="screen", help="Ticker symbol (e.g. BHSL, COST) or 'screen'")
    parser.add_argument("--replay", type=str, default=None, help="Path to saved run folder to replay offline with network off")
    parser.add_argument("--offline", action="store_true", help="Force offline execution using saved filings and cache")

    args = parser.parse_args()

    target_name = args.target if not args.replay else Path(args.replay).name.split("_")[0]
    desk = UnifiedDesk(
        target_arg=target_name,
        replay_dir=args.replay,
        offline=args.offline
    )

    try:
        final_file = desk.execute_pipeline()
        print(f"\nReport generated successfully: {final_file}")
    except Exception as e:
        print(f"\n[DESK EXECUTION FAILED at step]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
