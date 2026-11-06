# FIN 67110 — Autonomous Equity Research Agent Team (Checkpoint 2)

**Purdue University · Daniels School of Business · Fall 2026**  
**Course**: FIN 67110 Mastering AI for Finance  
**Lab 04 & Lab 05**: The Agent Team & Verifier Node Architecture  

---

## 1. Executive Summary

This repository rebuilds the equity research desk as an autonomous agent team governed by a deterministic state graph in code. In contrast to paper implementations where a manager LLM dynamically decides orchestration paths, our architecture enforces process determinism: the sequence of execution, node visibility, single-retry bounds, and verifier execution are strictly fixed in code. Dynamic model reasoning occurs strictly inside each role node.

Every report undergoes an unconditional verification pass by the **Verifier Node** (`verifier.py`), generating an audited table of marks embedded beneath the title.

---

## 2. Process Architecture: Deterministic Graph in Code

The execution pipeline consists of six sequential nodes executed in fixed order:

```
[Node 1: steps] ──► [Node 2: research_analyst] ──► [Node 3: financial_analyst] ──► [Node 4: investment_advisor] ──► [Node 5: strategy_manager] ──► [Node 6: verifier]
```

### Deterministic Code vs. Dynamic Model Responsibilities

| Decision Category | Code Decides (Deterministic) | Model Decides (Dynamic) |
| :--- | :--- | :--- |
| **Orchestration** | Which node runs next, and when execution terminates. | What the business is and where it stands qualitatively. |
| **Context & Visibility** | Exact JSON payload passed to each node (`task`, `context`, `expected_output`). | Which qualitative development constitutes the primary catalyst. |
| **Retry Bounds** | Enforces that failing parts return to their role exactly once (max 2 runs). | The investment thesis and the rating (**Buy**, **Hold**, or **Sell**). |
| **Verification Gate** | The Verifier runs unconditionally after the Manager on every run. | Whether a filing line states that number, for that period, in that definition. |
| **Persistence** | What is saved and where (`node_io.json`, `facts.json`, `marks.md`, `verified_report.md`). | The one unique insight that the release headline does not state. |

---

## 3. Four Role Personas (`roles/`)

Each role is defined in an isolated persona instruction file under `roles/` following the 6-part specification:
1. **Identity**: Role specialization and analytical purpose.
2. **How It Reads a Company**: Primary metrics inspected and noise filtered out.
3. **What It Is Given**: Minimalist, step-isolated context payloads.
4. **The Criteria It Scores**: Sourced quantitative or qualitative rubrics.
5. **What Would Change Its View**: Falsification triggers in subsequent filings.
6. **The Output & Insight Requirement**: Predefined report section ending with a mandatory `Insight:` line citing filings beyond release paragraph 1.

- **`roles/research_analyst.md`**: Owns Part 1 (Overview) and Part 2 (Market Positioning). Quotes verbatim lines.
- **`roles/financial_analyst.md`**: Owns Part 3 (Valuation Insights). Maps audited XBRL facts, executes calculator arithmetic, declares definitions, and evaluates peer operating margins.
- **`roles/investment_advisor.md`**: Owns Part 4 (Future Outlook) and Part 5 (Recommendation). Synthesizes research and financial outputs into a rating and states **The Decisive Metric** in bold.
- **`roles/strategy_manager.md`**: Verifies 5-part completeness, audits insight non-duplication against release paragraph 1, enforces the single-retry limit, and compiles `report.md`.

---

## 4. The Verifier Node (`verifier.py`)

The Verifier executes unconditionally on every run. No flag, argument, or code branch can bypass it.

### Verifier Dual-Check Mechanism
1. **In Code**:
   - Compares XBRL tag values and period ends exactly against `facts.json`.
   - Normalizes whitespace and verifies that quoted lines appear verbatim in the saved filing texts (`10-K.txt`, `10-Q.txt`, `8-K_Ex99-1.txt`).
   - Recomputes all ratio arithmetic from stated inputs.
2. **With Model**:
   - Audits whether the quoted line supports that specific number for that period under that definition.
   - Audits role insight lines to ensure they do not merely duplicate paragraph 1 of the earnings release.

### Table of Marks & Allowed Classifications
- **`Correct`**: Verified factually and arithmetically against regulatory filings.
- **`Wrong`**: Factual or arithmetic discrepancy; corrected in the marks table with the real figure and filing tag/accession number beside it.
- **`Unsupported`**: Missing citation or unconfirmed filing line.
- **`Missing`**: Required statement metric omitted from report.

### Two Things the Verifier Cannot Catch by Design
When presenting the agent desk, remember:
1. **Right Number, Wrong Claim**: If an analyst sources a true number from a filing line to support an unrelated claim that the client did not ask about, the verifier confirms the number is true, but cannot judge whether the claim is relevant. This is an analytical judgment call.
2. **The Investment Advisor's Thesis**: The forward-looking recommendation and strategic narrative cannot be confirmed in historical filings because future outcomes have not occurred.

---

## 5. Verification Proofs & Seeded-Error Suite (`test_verifier.py`)

The automated test suite (`test_verifier.py`) provides empirical proof across three distinct test conditions:

```bash
python test_verifier.py
```

### Proof 1: Clean Report (`COST_20261102_193519`)
- Verified against audited Costco run.
- **Result**: All claims marked **`Correct`**; 0 Wrong, 0 Unsupported, 0 Missing.

### Proof 2: Seeded Error & Invented Number (`COST_SEEDED_ERROR`)
- **Seeded Error**: Diluted EPS stated at **$21.76** (+$1.00 above 10-K's per-share line of $20.76).
  - **Verifier Mark**: **`Wrong`**.
  - **Correction**: `Corrected to $20.76 (Source: 10-K Item 8 EarningsPerShareDiluted, accn: 0000909832-26-000093)`.
- **Invented Number**: Revenue growth rate stated at **14.14%** (inflated by 4.0 percentage points above calculated 10.14%).
  - **Verifier Mark**: **`Wrong`**.
  - **Correction**: `Arithmetic error in report. Corrected to 10.14% from inputs.`

### Proof 3: Verifier Skip Protection
- Static code inspection confirms that `verifier.run_verifier(work_dir)` runs unconditionally, and no `--skip-verifier` or `--no-verify` flags exist.

---

## 6. How to Run

### Command-Line Interface (CLI)

```bash
# Run full agent team graph on a company
python desk_app.py COST --peers WMT,TGT,BJ --price 920.00

# Run standalone verifier on an existing run folder
python desk_app.py --verify-only COST_SEEDED_ERROR

# Execute automated proof test suite
python test_verifier.py
```

### Browser Web Application (`ui.py`)

A zero-dependency browser application that enables interactive execution, live node tracking, and visualization of marks and reports:

```bash
python ui.py
```
Opens in your browser at `http://127.0.0.1:8501`.
