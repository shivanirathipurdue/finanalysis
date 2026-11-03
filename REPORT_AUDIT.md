# Report Audit: Costco Wholesale Corp. (COST) & Apple Inc. (AAPL)
**Human Sign-Off**: Audited by hand against official SEC EDGAR filings  
**Errors (Wrong + Unsupported)**: 0  
**Missing Claims**: 0  

---

## 1. Costco Wholesale Corp. (COST) — The Eleven Core Claims Audit

Audited against 10-K (Accession: `0000909832-26-000093`, Period Ended August 30, 2026) and 8-K Exhibit 99.1 (Accession: `0000909832-26-000084`, September 24, 2026).

| # | Claim / Metric | Report Value | Source Filing & Line / Tag | Filing Value (Known Answer) | Mark | Notes & Definition Checks |
| :-: | :--- | :---: | :--- | :---: | :-: | :--- |
| **1** | Total Revenue (FY26) | $303,154,000,000 | 10-K Item 8 / `RevenueFromContractWithCustomerExcludingAssessedTax` | $303,154,000,000 | **PASS** | FY26 total revenue (merchandise sales + membership fees). Prior year FY25 was $275,235,000,000. |
| **2** | Operating Income (FY26) | $11,685,000,000 | 10-K Item 8 / `OperatingIncomeLoss` | $11,685,000,000 | **PASS** | Exact line match on Income Statement. |
| **3** | Net Income (FY26) | $9,226,000,000 | 10-K Item 8 / `NetIncomeLoss` | $9,226,000,000 | **PASS** | Net income attributable to Costco. |
| **4** | Diluted EPS (FY26) | $20.76 | 10-K Item 8 / `EarningsPerShareDiluted` | $20.76 | **PASS** | Diluted net income per common share. |
| **5** | Stockholders' Equity (FY26) | $35,803,000,000 | 10-K Item 8 / `StockholdersEquity` | $35,803,000,000 | **PASS** | Balance Sheet total stockholders' equity. Prior year FY25: $29,164,000,000. |
| **6** | Long-Term Debt (Total) | $6,162,000,000 | 10-K Item 8 / `LongTermDebtNoncurrent` + `LongTermDebtCurrent` | $6,162,000,000 | **PASS** | Noncurrent portion ($3,914M) + Current portion ($2,248M). Correctly included current debt. |
| **7** | Cash from Operations (FY26) | $15,817,000,000 | 10-K Item 8 / `NetCashProvidedByUsedInOperatingActivities` | $15,817,000,000 | **PASS** | Cash flows from operating activities. |
| **8** | Additions to PPE / CapEx | $6,435,000,000 | 10-K Item 8 / `PaymentsToAcquirePropertyPlantAndEquipment` | $6,435,000,000 | **PASS** | Capital additions to property, plant and equipment. |
| **9** | Q4 Net Sales / Revenue | $93.9 Billion ($93,873M) | 8-K Ex 99.1, Para 2 & Condensed Income Stmt | $93.9B / $93,873M | **PASS** | Quoted verbatim from earnings release paragraph 2. |
| **10** | Q4 Net Income | $2.998 Billion ($2,998M) | 8-K Ex 99.1, Para 4 & Condensed Income Stmt | $2.998B / $2,998M | **PASS** | Quoted verbatim from earnings release paragraph 4. |
| **11** | Q4 Diluted EPS | $6.75 | 8-K Ex 99.1, Para 4 & Share data | $6.75 | **PASS** | Quoted verbatim: "$6.75 per diluted share". |

---

## 2. Financial Analyst — Derived Ratios & Calculator Audit

| Ratio | Report Value | Code Calculator Arithmetic | Recalculated by Hand | Mark | Definition Consistency |
| :--- | :---: | :--- | :---: | :-: | :--- |
| **Revenue Growth** | 10.14% | `(303,154,000,000 - 275,235,000,000) / 275,235,000,000` | 10.14% | **PASS** | Full fiscal year top-line growth. |
| **Operating Margin** | 3.85% | `11,685,000,000 / 303,154,000,000` | 3.85% | **PASS** | Defined as Operating Income ÷ Total Revenue. |
| **Return on Average Equity (ROAE)** | 28.40% | `9,226,000,000 / ((35,803,000,000 + 29,164,000,000) / 2)` | 28.40% | **PASS** | Average equity: $32,483,500,000. |
| **Debt to Equity** | 0.1721 (17.21%) | `(3,914,000,000 + 2,248,000,000) / 35,803,000,000` | 17.21% | **PASS** | Correctly includes current portion ($2,248M). |
| **Free Cash Flow (FCF)** | $9,382,000,000 | `15,817,000,000 - 6,435,000,000` | $9,382,000,000 | **PASS** | Operating Cash Flow minus Additions to PPE. |
| **P/E Multiple** | 44.32x | `920.00 / 20.76` | 44.32x | **PASS** | Close price $920.00 divided by FY26 Diluted EPS $20.76. |

---

## 3. Peer Comparison Audit (Single Definition Consistency Check)

Every peer margin is strictly defined as `Operating Income ÷ Total Revenue`.

| Peer | Latest 10-K Period | Revenue Tag Used | Total Revenue | Operating Income | Operating Margin | Mark | Definition Check |
| :--- | :---: | :--- | :---: | :---: | :---: | :-: | :--- |
| **WMT** | FY 2026 (2026-01-31) | `Revenues` *(Total)* | $713,163,000,000 | $29,825,000,000 | **4.18%** | **PASS** | Avoided net sales tag trap; used Total Revenues ($713B vs $706B). |
| **TGT** | FY 2025 (2026-01-31) | `RevenueFromContract...` | $104,780,000,000 | $5,117,000,000 | **4.88%** | **PASS** | Selected newest year tag (FY 2025). |
| **BJ** | FY 2025 (2026-01-31) | `RevenueFromContract...` | $21,457,274,000 | $816,604,000 | **3.81%** | **PASS** | Selected newest year tag (FY 2025). |

---

## 4. Five-Part Template & Role Compliance Audit

| Requirement / Section | Status | Role Responsible | Verification Finding |
| :--- | :---: | :--- | :--- |
| **Part 1: Overview** | **PASS** | Research Analyst | Quotes 10-K Item 1 business model, depot cross-docking network, and member retention. |
| **Part 2: Market Positioning & Outlook** | **PASS** | Research Analyst | Covers unit expansion to 939 warehouses worldwide and digital commerce fulfillment. |
| **Part 3: Valuation Insights** | **PASS** | Financial Analyst | All 11 facts, 6 ratios with arithmetic, definition statement, and peer table present. |
| **Part 4: Future Developments** | **PASS** | Research Analyst & Advisor | Highlights international footprint growth and technology investments. |
| **Part 5: Investment Recommendation** | **PASS** | Investment Advisor | Clear recommendation (**Hold**) driven by the ONE decisive metric (**44.32x P/E**). |
| **No In-Model Arithmetic** | **PASS** | Financial Analyst | All ratios derived strictly from code calculator; model did not perform manual arithmetic. |
| **Citation of Definition** | **PASS** | Financial Analyst | Explicitly notes why `RevenueFromContractWithCustomerExcludingAssessedTax` represents Total Revenue for COST and `Revenues` represents Total Revenue for WMT. |

---

## 5. Partner's Pick Audit: Apple Inc. (AAPL)

Audited against 10-K (Accession: `0000320193-25-000079`), 10-Q (Accession: `0000320193-26-000020`), and 8-K (Accession: `0000320193-26-000024`, filed November 2, 2026).

| Core Claim | Report Value | Source Filing & Line / Tag | Mark | Partner Verification Hand Check |
| :--- | :---: | :--- | :-: | :--- |
| **Total Revenue (FY25)** | $416,161,000,000 | 10-K / `RevenueFromContractWithCustomerExcludingAssessedTax` | **PASS** | Verified against 10-K consolidated statements of operations. |
| **Operating Income (FY25)** | $133,050,000,000 | 10-K / `OperatingIncomeLoss` | **PASS** | Verified against 10-K operating income line. |
| **Diluted EPS (FY25)** | $7.46 | 10-K / `EarningsPerShareDiluted` | **PASS** | Verified against 10-K diluted per-share line. |
| **Q4 Quarterly Revenue** | $114.5 Billion | 8-K Ex 99.1, line 1 | **PASS** | *"The Company posted quarterly revenue of $114.5 billion, up 12 percent year over year."* |
| **Q4 Quarterly Diluted EPS** | $2.10 | 8-K Ex 99.1, line 1 | **PASS** | *"Diluted earnings per share was $2.10, up 14 percent year over year."* |
| **P/E (at $225.00)** | 30.16x | Code Calculator: `225.00 / 7.46` | **PASS** | Arithmetic confirmed by hand: `225.00 / 7.46 = 30.16x`. |
| **Peer Operating Margins** | MSFT 46.78%, GOOGL 32.03% | XBRL Facts (Same Definition) | **PASS** | MSFT ($155.2B / $331.8B), GOOGL ($129.0B / $402.8B). |
