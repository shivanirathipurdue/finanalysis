### Verifier Table of Marks
**Verification Summary**: Total Checks: 22 | **Correct**: 20 | **Wrong**: 2 | **Unsupported**: 0 | **Missing**: 0

| Claim / Metric | Report Value | Source Cited | Filing Value / Real Source | Mark | Verifier Finding & Correction |
| :--- | :--- | :--- | :--- | :-: | :--- |
| Total Revenue | `$303,154,000,000` | 10-K Item 8 / `RevenueFromContractWithCustomerExcludingAssessedTax` (2026-08-30) | $303,154,000,000 | **Correct** | Matches official XBRL facts. |
| Operating Income | `$11,685,000,000` | 10-K Item 8 / `OperatingIncomeLoss` (2026-08-30) | $11,685,000,000 | **Correct** | Matches official XBRL facts. |
| Net Income | `$9,226,000,000` | 10-K Item 8 / `NetIncomeLoss` (2026-08-30) | $9,226,000,000 | **Correct** | Matches official XBRL facts. |
| Diluted EPS | `$21.76` | 10-K Item 8 / `EarningsPerShareDiluted` (2026-08-30) | $20.76 | **Wrong** | Corrected to $20.76 (Source: 10-K Item 8 `EarningsPerShareDiluted`, accn: 0000909832-26-000093). |
| Stockholders' Equity | `$35,803,000,000` | 10-K Item 8 / `StockholdersEquity` (2026-08-30) | $35,803,000,000 | **Correct** | Matches official XBRL facts. |
| Long-Term Debt | `$3,914,000,000` | 10-K Item 8 / `LongTermDebtNoncurrent` (2026-08-30) | $3,914,000,000 | **Correct** | Matches official XBRL facts. |
| Cash from Operations | `$15,817,000,000` | 10-K Item 8 / `NetCashProvidedByUsedInOperatingActivities` (2026-08-30) | $15,817,000,000 | **Correct** | Matches official XBRL facts. |
| Additions to PPE | `$6,435,000,000` | 10-K Item 8 / `PaymentsToAcquirePropertyPlantAndEquipment` (2026-08-30) | $6,435,000,000 | **Correct** | Matches official XBRL facts. |
| Revenue Growth Rate | `14.14%` | Stated Inputs in Report | 10.14% | **Wrong** | Arithmetic error in report. Corrected to 10.14% from inputs. |
| Operating Margin | `3.85%` | Code Calculator Arithmetic | 3.85% | **Correct** | Operating Income ÷ Total Revenue arithmetic verified. |
| P/E Multiple | `44.3200x` | Code Calculator (`Price ÷ Diluted EPS`) | 44.3160x | **Correct** | Valuation multiple arithmetic verified. |
| Return on Average Equity (ROAE) | `28.40%` | Code Calculator (Average Equity Basis) | 28.40% | **Correct** | Appropriately used average equity definition. |
| Quarterly Release Citation | `"Net sales for the quarter increased 11.2 perc..."` | Form 8-K Exhibit 99.1 | Verbatim Match in Release | **Correct** | Quoted text verified word-for-word in earnings release. |
| Quarterly Release Citation | `"Net income for the fourth quarter was $2.998 ..."` | Form 8-K Exhibit 99.1 | Verbatim Match in Release | **Correct** | Quoted text verified word-for-word in earnings release. |
| 10-K Disclosure Citation | `"Costco Wholesale Corporation and its subsidia..."` | Form 10-K Text | Verbatim Match in 10-K | **Correct** | Quoted line verified word-for-word in 10-K filing. |
| 10-K Disclosure Citation | `"We operate membership warehouses and e-commer..."` | Form 10-K Text | Verbatim Match in 10-K | **Correct** | Quoted line verified word-for-word in 10-K filing. |
| Peer Margin (WMT) | `4.18%` | Peer 10-K Facts (`29,825,000,000 / 713,163,000,000`) | 4.18% | **Correct** | Identical definition consistency (`Operating Income ÷ Total Revenue`). |
| Peer Margin (TGT) | `4.88%` | Peer 10-K Facts (`5,117,000,000 / 104,780,000,000`) | 4.88% | **Correct** | Identical definition consistency (`Operating Income ÷ Total Revenue`). |
| Peer Margin (BJ) | `3.81%` | Peer 10-K Facts (`816,604,000 / 21,457,274,000`) | 3.81% | **Correct** | Identical definition consistency (`Operating Income ÷ Total Revenue`). |
| Role Insight Line | `Global warehouse operating footprint expanded...` | [10-K.txt, Line 11] | Verified Filing Fact | **Correct** | Insight verified against filing and distinct from release headline. |
| Role Insight Line | `Free cash flow conversion stood at 101.7% of ...` | [10-K Item 8, Cash Flows] | Verified Filing Fact | **Correct** | Insight verified against filing and distinct from release headline. |
| Role Insight Line | `Operating margin of 3.85% closely tracks whol...` | [Peer Operating Margins, facts.json] | Verified Filing Fact | **Correct** | Insight verified against filing and distinct from release headline. |