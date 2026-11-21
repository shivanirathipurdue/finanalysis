# Three-Column Comparison Table: Parts Alone vs. Joined Desk vs. Authoritative Filing
**Course**: FIN 67110 Mastering AI for Finance · Purdue University · Daniels School of Business · Fall 2026  
**Target Company**: BioHealth Solutions Inc. (BHSL)  
**Run Reference**: `BHSL_20261110_160000` / `BHSL_20261121_113757`  
**Authoritative Filing Sources**:
- Form 10-12B / Exhibit 99.1 (CIK: `0001928374`, Accession: `0001928374-26-000005`, Distribution Date: 2026-09-01)
- Form 10-Q (Period Ended September 30, 2026, Accession: `0001928374-26-000020`)
- Form 4 (Accession: `0001928374-26-000014`, Earliest Transaction: September 5, 2026)

---

## 1. Executive Summary & Join Architecture Analysis
As established in Week 5 (Teaching 3 & Lab 09), the honest measure of a joined system is what the join changed:
1. **Pipeline Join (Seeker & Facts)**: Preserves exact fact parity between parts. The seeker feeds candidates through `registry.json`, and filings are fetched once into the contract run folder. No filing is fetched twice, holding baseline facts invariant across all components.
2. **Tool Join (Worksheet as a Tool of the Financial Analyst)**: The Financial Analyst role receives `worksheet.md` as an external tool output file. The role quotes the Low Case Value Range ($18.00/sh) and Pro Forma Owner Cash Flow ($150,000,000.00) without recomputing them. This changes the decisive metric and directional recommendation from a generic Hold into an informed special-situation Buy view based on the 21.11% margin of safety against the low-case valuation floor.
3. **The Guard (Hook Verification)**: Silently validates every numerical claim against `facts.json`, filing texts, printed arithmetic, and `closes_reader.py`. Refuses 'done' if a single figure or arithmetic chain deviates.

---

## 2. The Three-Column Comparison Table

| # | Core Claim / Metric | Column 1: Parts Alone (Week 4 Baseline) | Column 2: Joined Desk (`desk.py` Final Report) | Column 3: Authoritative Filing Source & Line | Join Effect & Status |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Total Revenue** | Form 10-Q: $48,200,000.00 | Form 10-Q: $48,200,000.00 | Form 10-Q Item 1, Statement of Operations, Line 13: `Revenues: $48,200,000` | **Same** (Pipeline join holds values constant) |
| **2** | **Revenue Growth** | N/A (first standalone period) | N/A (first standalone period) | Form 10-Q Item 1, Note 1 (initial month of post-separation standalone operations) | **Same** (Pipeline join holds values constant) |
| **3** | **Operating Income** | Form 10-Q: $15,100,000.00 | Form 10-Q: $15,100,000.00 | Form 10-Q Item 1, Statement of Operations, Line 14: `Operating Income: $15,100,000` | **Same** (Pipeline join holds values constant) |
| **4** | **Operating Margin** | 31.33% (`$15.1M / $48.2M`) | 31.33% (`$15.1M / $48.2M`) | Form 10-Q Item 1, Lines 13–14: `15,100,000 / 48,200,000 = 31.3278%` | **Same** (Pipeline join holds values constant) |
| **5** | **Net Income (GAAP Pro Forma)** | Pro Forma FY25: $140,000,000.00; Quarter: $11,800,000.00 | Pro Forma FY25: $140,000,000.00; Quarter: $11,800,000.00 | Form 10 Ex 99.1, Pro Forma Stmt, Line 16: `Unaudited Pro Forma Combined Net Income was $140,000,000`; Form 10-Q Line 15: `$11,800,000` | **Same** (Pipeline join holds values constant) |
| **6** | **Return on Average Equity (ROAE)** | N/A (pro forma capitalization) | N/A (pro forma capitalization) | Form 10 Ex 99.1, Note 2 (standalone equity established at spin date) | **Same** (Pipeline join holds values constant) |
| **7** | **Total Debt Raised** | $120,000,000.00 | $120,000,000.00 | Form 10 Ex 99.1, Financing Arrangements, Line 26: `senior notes yielding debt raised of $120,000,000` | **Same** (Pipeline join holds values constant) |
| **8** | **Free Cash Flow / Owner Cash Flow (OCF)** | Team Report alone: N/A; Worksheet alone: $150,000,000.00 | **$150,000,000.00** (quoted directly from worksheet tool) | Form 10 Ex 99.1 Pro Forma Lines 16–18: Net Income ($140M) + D&A ($35M) - CapEx ($25M) = `$150,000,000.00` | **Changed by Tool Join** (Financial Analyst integrates worksheet tool into Part 3; verified against Form 10) |
| **9** | **Quarterly Revenue (Q3)** | $48,200,000.00 | $48,200,000.00 | Form 10-Q Item 1, Line 13: `Revenues: $48,200,000` | **Same** (Pipeline join holds values constant) |
| **10** | **Quarterly Net Income (Q3)** | $11,800,000.00 | $11,800,000.00 | Form 10-Q Item 1, Line 15: `Net Income: $11,800,000` | **Same** (Pipeline join holds values constant) |
| **11** | **Quarterly Operating Cash Flow** | $16,400,000.00 | $16,400,000.00 | Form 10-Q Item 1, Cash Flows, Line 18: `Net Cash Provided by Operating Activities: $16,400,000` | **Same** (Pipeline join holds values constant) |
| **12** | **The Directional View** | Team alone: Hold; Worksheet alone: More than price | **Buy / More than price** | Form 10 Ex 99.1 & `worksheet_config.json`: Low Case Value Range ($18.00/sh) vs price ($14.20) provides 21.11% margin of safety | **Changed by Tool Join** (Synthesis aligns thesis with Klarman Margin of Safety & Greenblatt spinoff dynamics) |
| **13** | **The One Decisive Number** | Team alone: P/E Multiple; Worksheet alone: Low Case Value $18.00 | **Low Case Valuation $900,000,000.00 ($18.00 per share) vs prevailing price $14.20** | Form 10 Ex 99.1 & printed code arithmetic: `6.0 * $150,000,000 / 50,000,000 shares = $18.00` | **Changed by Tool Join** (Decisive metric replaced by audited intrinsic valuation floor) |

---

## 3. Detailed Audit of Rows Changed by the Join

### Row 8: Pro Forma Owner Cash Flow
- **Before Join (Parts Alone)**: The agent team alone had no mechanism to parse Form 10 pro forma adjustments, reporting FCF as N/A. The worksheet alone computed OCF in isolation ($150,000,000.00) without integration into the research narrative.
- **After Join (Joined Desk)**: The Financial Analyst calls the worksheet skill as a tool, quoting the audited arithmetic:
  `After-Tax Earnings ($140,000,000.00) + D&A ($35,000,000.00) - CapEx ($25,000,000.00) = $150,000,000.00`.
- **Filing Check**: Verified verbatim against Form 10 Exhibit 99.1, Unaudited Pro Forma Combined Financial Statements, Lines 16 to 18. The tool join is completely accurate.

### Rows 12 & 13: The Directional View & The Decisive Number
- **Before Join (Parts Alone)**: The Investment Advisor role evaluated standard multiples without knowledge of the parent distribution overhang, producing a generic "Hold" on unpopulated P/E ratios.
- **After Join (Joined Desk)**: The Investment Advisor role receives the Financial Analyst's tool quote, recognizing that BHSL trades at $14.20 against an audited low-case intrinsic value of $18.00 per share (a 21.11% discount). The decisive metric becomes the **Low Case Value $18.00 per share**, upgrading the thesis to **Buy / More than price**.
- **Filing Check**: Verified against Form 10 Exhibit 99.1 pro forma numbers, 50,000,000 shares outstanding, and `worksheet_config.json` 6.0x multiple.

---

screens, not recommendations
