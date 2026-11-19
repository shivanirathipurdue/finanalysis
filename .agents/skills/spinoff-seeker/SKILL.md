---
name: spinoff-seeker
description: Finds and screens U.S. corporate spinoffs on SEC EDGAR from a given start date, tracks the filing trail (Form 10, CERT, 8-K distribution, Form 4), maintains an audited fact registry, prices names with the closes reader, and ranks candidates using declared value factors.
---

# Spinoff Seeker Skill

A procedural seeker that implements Joel Greenblatt's (*You Can Be a Stock Market Genius*, Ch. 3) and Seth Klarman's (*Margin of Safety*, Ch. 10) spinoff investment procedures on SEC EDGAR.

## Process Overview

The seeker executes a deterministic search on SEC EDGAR:
1. **Discovers Registrations**: Queries Form 10 (`10-12B`, `10-12G`) and amendment filings since `--start-date`.
2. **Filters & Drops**: Rejects funds, shells, and companies registering existing shares that lack an information statement showing a parent distributing the business.
3. **Establishes Stages**:
   - `registered`: Form 10 filed with Information Statement.
   - `listing approved`: Exchange `CERT` filing verified.
   - `trading`: Proven by Form 4 insider filing, first 10-Q, or 10-K in registrant's EDGAR feed.
   - `in its window`: Between distribution date and distribution date + `window_days` from `factors.json`.
   - `past it`: Beyond the declared investment window.
4. **Builds Fact Registry**: Extracts parent name, parent CIK, distribution ratio, record date, distribution date, and cited filing section. Never estimates missing facts.
5. **Prices Names**: Obtains the first official close *after* the distribution date using `closes_reader.py` (never when-issued prices).
6. **Ranks Candidates**: Scores names in the window against weights and directions in `factors.json`.
7. **Generates Report**: Outputs ranked table, watch list, dropped list, data limitations, and ends with `"screens, not recommendations"`.

## Usage

```powershell
# Run the seeker from a start date:
python seeker.py --start-date 2025-11-01

# Run unit tests on synthetic data:
python test_seeker.py
```
