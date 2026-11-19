---
name: worksheet
description: Generates an institutional spinoff worksheet for a screened company from its SEC filings and facts file. Calculates Owner Cash Flow and Low/Mid Value Range with printed arithmetic, applies investor persona judgment from Greenblatt Ch. 3 and Klarman Ch. 10, verifies client liquidity, and ends with 'screens, not recommendations'.
---

# Spinoff Worksheet Skill

Implements Teaching 4 and Lab 07 of FIN 67110 (*Mastering AI for Finance*).
Processes one screened spinoff candidate through a standardized worksheet, tracing every numerical claim to SEC filings, computing intrinsic value deterministically in code, and applying qualitative investor persona judgment.

## Process Overview

1. **Ingests Saved Run**:
   - Reads `facts.json`, `Form10_Ex99-1.txt`, `Form4.txt`, and periodic statements from the company's run folder.
   - Cross-references SEC EDGAR `registry.json`. Non-spinoff companies print "not applicable" for spinoff sections.
2. **Deterministic Financial Computations**:
   - Computes **Owner Cash Flow** in code:
     $$\text{Owner Cash Flow} = \text{After-Tax Earnings} + \text{Depreciation} - \text{Capital Spending}$$
   - Prints full arithmetic for both historical and pro forma periods.
   - Computes **Value Range** (Low Case and Mid Case) using declared multiples/rates in `worksheet_config.json`.
   - Computes prevailing market price against low-case valuation.
3. **Investor Persona Judgment**:
   - Hands filing facts, value range, and price against low case to `roles/investor_persona.md`.
   - Explains non-fundamental institutional selling, index exclusion effects, and what subsequent filing metrics would invalidate the view.
4. **Liquidity Check**:
   - Evaluates client purchase size against median daily dollar volume supplied by `closes_reader.py`.
5. **Directional View & Conviction**:
   - States whether the business is worth more or less than the price, citing the decisive number.
   - Assigns High or Low conviction based on the rule in `worksheet_config.json`.
   - Concludes strictly with: `screens, not recommendations`.

## Usage

```powershell
# Run the worksheet on a saved run directory or ticker:
python worksheet.py BHSL_20261110_160000

# Custom configuration or persona:
python worksheet.py BHSL --config worksheet_config.json --persona roles/investor_persona.md
```
