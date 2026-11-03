#!/usr/bin/env python3
"""
FIN 67110 - Equity Research Desk (Data Side)
Implementation following Section 3.1 of Francis & Zhang (2026).
Retrieves SEC EDGAR filings, parses XBRL company facts, computes fundamental ratios,
extracts earnings release statements, and benchmarks against peers.
Rule: Nothing in the code names any specific company. All filers are resolved dynamically.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Rate limit delay for SEC EDGAR (courtesy delay, <= 10 req/sec)
SEC_REQUEST_DELAY = 0.15


def get_sec_user_agent() -> str:
    """Load and validate SEC_USER_AGENT from .env file."""
    load_dotenv()
    sec_agent = os.getenv("SEC_USER_AGENT")
    if not sec_agent or "[your full name]" in sec_agent or "sample company" in sec_agent:
        script_dir = Path(__file__).resolve().parent
        load_dotenv(script_dir / ".env")
        sec_agent = os.getenv("SEC_USER_AGENT")

    if not sec_agent:
        print("Error: SEC_USER_AGENT not found in .env file.", file=sys.stderr)
        print("Please ensure .env contains: SEC_USER_AGENT=Your Name email@domain.com", file=sys.stderr)
        sys.exit(1)
    return sec_agent.strip()


def sec_get(url: str, user_agent: str, retries: int = 3) -> requests.Response:
    """Perform a rate-limited GET request to SEC EDGAR with retry handling."""
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov" if "data.sec.gov" in url else "www.sec.gov",
    }
    time.sleep(SEC_REQUEST_DELAY)
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=25)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait_time = 2 * (attempt + 1)
                time.sleep(wait_time)
            elif resp.status_code in (404, 403):
                return resp
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1)
    return resp


def step_1_resolve_ticker(ticker: str, user_agent: str) -> Tuple[str, str, int]:
    """
    Step 1: Resolve ticker to CIK from SEC's company_tickers.json.
    Returns: (cik_10_digit_str, company_title, cik_int)
    """
    print("=" * 80)
    print("STEP 1: RESOLVE TICKER TO CIK")
    print("=" * 80)
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = sec_get(url, user_agent)
    if resp.status_code != 200:
        print(f"Error fetching company_tickers.json: HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    tickers_data = resp.json()
    ticker_clean = ticker.strip().upper()
    resolved_info = None

    for entry in tickers_data.values():
        if entry.get("ticker", "").upper() == ticker_clean:
            resolved_info = entry
            break

    if not resolved_info:
        print(f"Error: Ticker '{ticker_clean}' not found in SEC company_tickers.json.", file=sys.stderr)
        sys.exit(1)

    cik_int = int(resolved_info["cik_str"])
    cik_str = str(cik_int).zfill(10)
    title = resolved_info.get("title", "")

    print(f"Ticker:        {ticker_clean}")
    print(f"Company Title: {title}")
    print(f"CIK:           {cik_str} (Integer: {cik_int})")
    print()
    return cik_str, title, cik_int


def step_2_list_filings(cik_str: str, cik_int: int, user_agent: str) -> Dict[str, Dict[str, Any]]:
    """
    Step 2: List company filings from EDGAR submissions API and pick:
      - Latest 10-K
      - Latest 10-Q
      - Latest 8-K reporting Item 2.02 (earnings release)
    Print each accession number and the 'Accepted' time shown on its EDGAR index page.
    """
    print("=" * 80)
    print("STEP 2: RETRIEVE FILINGS FROM EDGAR SUBMISSIONS API")
    print("=" * 80)
    url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
    resp = sec_get(url, user_agent)
    if resp.status_code != 200:
        print(f"Error fetching submissions for CIK {cik_str}: HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accns = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    accept_times = recent.get("acceptanceDateTime", [])
    items_list = recent.get("items", [])
    primary_docs = recent.get("primaryDocument", [])

    latest_10k = None
    latest_10q = None
    latest_8k_202 = None

    for i, form in enumerate(forms):
        accn = accns[i]
        fdate = filing_dates[i]
        atime_raw = accept_times[i]
        pdoc = primary_docs[i]
        items_str = str(items_list[i]) if i < len(items_list) else ""

        # Latest 10-K
        if form == "10-K" and latest_10k is None:
            latest_10k = {
                "form": form,
                "accessionNumber": accn,
                "filingDate": fdate,
                "acceptanceDateTime": atime_raw,
                "primaryDocument": pdoc,
                "items": items_str,
            }

        # Latest 10-Q
        elif form == "10-Q" and latest_10q is None:
            latest_10q = {
                "form": form,
                "accessionNumber": accn,
                "filingDate": fdate,
                "acceptanceDateTime": atime_raw,
                "primaryDocument": pdoc,
                "items": items_str,
            }

        # Latest 8-K reporting Item 2.02 (skipping any newer 8-Ks without Item 2.02)
        elif form == "8-K" and latest_8k_202 is None:
            items_tokens = [it.strip() for it in items_str.split(",") if it.strip()]
            if "2.02" in items_tokens or "2.02" in items_str:
                latest_8k_202 = {
                    "form": form,
                    "accessionNumber": accn,
                    "filingDate": fdate,
                    "acceptanceDateTime": atime_raw,
                    "primaryDocument": pdoc,
                    "items": items_str,
                }

        if latest_10k and latest_10q and latest_8k_202:
            break

    selected = {
        "10-K": latest_10k,
        "10-Q": latest_10q,
        "8-K": latest_8k_202,
    }

    # Fetch exact "Accepted" time from the EDGAR index page for each filing
    for key, info in selected.items():
        if not info:
            print(f"Warning: Filing {key} could not be found.", file=sys.stderr)
            continue

        accn = info["accessionNumber"]
        accn_clean = accn.replace("-", "")
        index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accn_clean}/{accn}-index.htm"
        idx_resp = sec_get(index_url, user_agent)
        accepted_time_str = None

        if idx_resp.status_code == 200:
            soup = BeautifulSoup(idx_resp.text, "html.parser")
            # In EDGAR index pages: <div class="infoHead">Accepted</div> followed by <div class="info">YYYY-MM-DD HH:MM:SS</div>
            for head in soup.find_all("div", class_="infoHead"):
                if "accepted" in head.get_text().lower():
                    sib = head.find_next_sibling("div", class_="info")
                    if sib:
                        accepted_time_str = sib.get_text().strip()
                        break
            if not accepted_time_str:
                # Fallback to general grouping search
                for grouping in soup.find_all("div", class_="formGrouping"):
                    lbl = grouping.find("div", class_="formGroupingLabel")
                    val = grouping.find("div", class_="formGroupingData")
                    if lbl and val and "accepted" in lbl.get_text().lower():
                        accepted_time_str = val.get_text().strip()
                        break

        # Fallback to acceptanceDateTime if index parse was empty
        if not accepted_time_str:
            accepted_time_str = info["acceptanceDateTime"]

        info["acceptedTime"] = accepted_time_str

        print(f"Filing:            {info['form']}")
        print(f"Accession Number:  {info['accessionNumber']}")
        print(f"Accepted Time:     {info['acceptedTime']} (Shown on EDGAR Index Page)")
        print(f"Filing Date:       {info['filingDate']}")
        if key == "8-K":
            print(f"Items Reported:    {info['items']} (Verified Item 2.02 present; newer non-2.02 8-Ks skipped)")
        print(f"Primary Document:  {info['primaryDocument']}")
        print("-" * 65)

    print()
    return selected


def step_3_download_and_save_documents(
    cik_str: str,
    cik_int: int,
    filings: Dict[str, Dict[str, Any]],
    user_agent: str,
    ticker: str,
    base_dir: Optional[Path] = None,
) -> Tuple[Path, Optional[Path]]:
    """
    Step 3: Download the three documents, taking the 8-K's Exhibit 99.1 for the release,
    convert each to plain text and save them in a folder named by company and the date and time of the run.
    Returns: (output_folder_path, release_text_path)
    """
    print("=" * 80)
    print("STEP 3: DOWNLOAD DOCUMENTS & CONVERT TO PLAIN TEXT")
    print("=" * 80)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{ticker.upper()}_{now_str}"
    work_dir = (base_dir or Path.cwd()) / folder_name
    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"Destination Folder: {work_dir}")

    release_txt_path = None

    for fkey in ["10-K", "10-Q", "8-K"]:
        finfo = filings.get(fkey)
        if not finfo:
            continue

        accn = finfo["accessionNumber"]
        accn_clean = accn.replace("-", "")

        target_doc = finfo["primaryDocument"]
        output_filename = f"{fkey}.txt"

        if fkey == "8-K":
            output_filename = "8-K_Ex99-1.txt"
            # Discover Exhibit 99.1 from the filing index page
            index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accn_clean}/{accn}-index.htm"
            idx_resp = sec_get(index_url, user_agent)
            ex99_doc = None
            if idx_resp.status_code == 200:
                soup = BeautifulSoup(idx_resp.text, "html.parser")
                # Look for row containing EX-99.1 or EX-99 in index table
                for tr in soup.find_all("tr"):
                    tds = tr.find_all("td")
                    td_texts = [td.get_text(strip=True).upper() for td in tds]
                    if any("EX-99.1" in t or "EX-99" in t or "EXHIBIT 99.1" in t for t in td_texts):
                        a_tag = tr.find("a")
                        if a_tag and a_tag.get("href"):
                            ex99_doc = a_tag["href"].split("/")[-1]
                            break

            # Fallback to directory json if not found in table
            if not ex99_doc:
                dir_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accn_clean}/index.json"
                dir_resp = sec_get(dir_url, user_agent)
                if dir_resp.status_code == 200:
                    items = dir_resp.json().get("directory", {}).get("item", [])
                    for it in items:
                        name = it.get("name", "")
                        if ("ex99" in name.lower() or "99-1" in name.lower() or "991" in name.lower()) and name.endswith((".htm", ".html", ".txt")):
                            ex99_doc = name
                            break

            if ex99_doc:
                target_doc = ex99_doc
                print(f"Identified Exhibit 99.1 for 8-K: {target_doc}")
            else:
                print(f"Notice: Specific Exhibit 99.1 file not isolated, using primary doc {target_doc}")

        # Download document
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accn_clean}/{target_doc}"
        doc_resp = sec_get(doc_url, user_agent)
        if doc_resp.status_code != 200:
            print(f"Error downloading {target_doc}: HTTP {doc_resp.status_code}", file=sys.stderr)
            continue

        # Convert to plain text
        if target_doc.endswith((".htm", ".html", ".xml")):
            soup = BeautifulSoup(doc_resp.content, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.extract()
            raw_text = soup.get_text(separator="\n")
        else:
            raw_text = doc_resp.text

        # Clean whitespace and empty lines
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        dest_file = work_dir / output_filename
        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(clean_text)

        size_kb = len(clean_text.encode("utf-8")) / 1024
        print(f"Saved: {output_filename:<16s} ({size_kb:8.1f} KB, {len(lines)} lines) <- {target_doc}")

        if fkey == "8-K":
            release_txt_path = dest_file

    print()
    return work_dir, release_txt_path


# Standard concept definition list with candidate XBRL tags
FACT_CONCEPTS = {
    "Total Revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "TotalRevenuesAndOtherIncome",
    ],
    "Operating Income": ["OperatingIncomeLoss"],
    "Net Income": ["NetIncomeLoss", "ProfitLoss"],
    "Diluted EPS": ["EarningsPerShareDiluted"],
    "Stockholders' Equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "Long-Term Debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    "Current Portion LT Debt": [
        "LongTermDebtCurrent",
        "LongTermDebtAndCapitalLeaseObligationsCurrent",
        "DebtCurrent",
    ],
    "Cash from Operations": ["NetCashProvidedByUsedInOperatingActivities"],
    "Additions to PPE": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquireCapitalAssets",
    ],
}


def fetch_company_facts_json(cik_str: str, user_agent: str) -> Optional[Dict[str, Any]]:
    """Fetch raw company facts JSON from SEC EDGAR API."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"
    resp = sec_get(url, user_agent)
    if resp.status_code != 200:
        print(f"Error fetching company facts for CIK {cik_str}: HTTP {resp.status_code}", file=sys.stderr)
        return None
    return resp.json()


def extract_facts_for_latest_fy(
    facts_json: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, Any]], int, str]:
    """
    Step 4 Core Logic:
    1. Determine latest fiscal year using revenue candidate tags:
       choose candidate tag whose latest year is newest.
       If tags tie for latest year, candidate list order provides definition priority
       (e.g. Revenues takes precedence over net sales tags).
    2. Read every concept for the same fiscal year as revenue, with prior year beside it.
    Returns: (extracted_facts_dict, latest_fiscal_year, period_end_date)
    """
    gaap = facts_json.get("facts", {}).get("us-gaap", {})

    # 1. Choose revenue tag whose latest fiscal year is newest
    best_rev_tag = None
    best_rev_year = -1
    best_rev_end = ""

    for tag in FACT_CONCEPTS["Total Revenue"]:
        if tag in gaap:
            units = gaap[tag].get("units", {})
            for u, flist in units.items():
                k_facts = [f for f in flist if f.get("form") == "10-K" and f.get("fp") == "FY"]
                if k_facts:
                    latest = max(k_facts, key=lambda x: (x.get("fy", 0), x.get("end", "")))
                    fy = latest.get("fy", 0)
                    end = latest.get("end", "")
                    if fy > best_rev_year:
                        best_rev_year = fy
                        best_rev_tag = tag
                        best_rev_end = end
                    elif fy == best_rev_year and best_rev_tag is None:
                        best_rev_tag = tag
                        best_rev_end = end

    if not best_rev_tag:
        raise ValueError("Could not find any standard revenue tag in company facts.")

    target_fy = best_rev_year
    target_end = best_rev_end
    extracted: Dict[str, Dict[str, Any]] = {}

    for cname, candidate_tags in FACT_CONCEPTS.items():
        chosen_entry = None
        for tag in candidate_tags:
            if tag in gaap:
                units = gaap[tag].get("units", {})
                for u, flist in units.items():
                    k_facts = [f for f in flist if f.get("form") == "10-K"]
                    # Match target fiscal year
                    cur_matches = [
                        f for f in k_facts
                        if f.get("fy") == target_fy and (f.get("fp") == "FY" or "start" not in f or f.get("end") == target_end)
                    ]
                    if not cur_matches:
                        cur_matches = [f for f in k_facts if f.get("end") == target_end]

                    if cur_matches:
                        cur_fact = cur_matches[-1]
                        # Match prior fiscal year
                        prior_matches = [
                            f for f in k_facts
                            if f.get("fy") == target_fy - 1 and (f.get("fp") == "FY" or "start" not in f)
                        ]
                        if not prior_matches:
                            prior_matches = [f for f in k_facts if f.get("fy") == target_fy - 1]
                        prior_fact = prior_matches[-1] if prior_matches else None

                        chosen_entry = {
                            "tag": tag,
                            "current_val": cur_fact.get("val"),
                            "prior_val": prior_fact.get("val") if prior_fact else None,
                            "period_end": cur_fact.get("end"),
                            "form": cur_fact.get("form"),
                            "accn": cur_fact.get("accn"),
                            "unit": u,
                            "fy": target_fy,
                        }
                        break
            if chosen_entry:
                break

        # If current portion of debt is not reported as separate tag, default to 0
        if not chosen_entry and cname == "Current Portion LT Debt":
            chosen_entry = {
                "tag": "Not Reported / 0",
                "current_val": 0,
                "prior_val": 0,
                "period_end": target_end,
                "form": "10-K",
                "accn": "N/A",
                "unit": "USD",
                "fy": target_fy,
            }

        if chosen_entry:
            extracted[cname] = chosen_entry
        else:
            extracted[cname] = {
                "tag": "N/A",
                "current_val": None,
                "prior_val": None,
                "period_end": target_end,
                "form": "10-K",
                "accn": "N/A",
                "unit": "USD",
                "fy": target_fy,
            }

    return extracted, target_fy, target_end


def format_num(val: Any) -> str:
    """Format numeric values with appropriate commas or decimal places."""
    if val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        if abs(val) < 100:
            return f"{val:.2f}"
        return f"{val:,.0f}"
    return str(val)


def step_4_fetch_facts(cik_str: str, user_agent: str) -> Tuple[Dict[str, Dict[str, Any]], int, str]:
    """
    Step 4: Fetch XBRL company facts and print for the latest fiscal year:
    total revenue, operating income, net income, diluted EPS, stockholders' equity,
    long-term debt and its current portion, cash from operations, additions to property and equipment,
    each with its tag, period end, filing, and prior year beside it.
    """
    print("=" * 80)
    print("STEP 4: FETCH XBRL COMPANY FACTS (LATEST FISCAL YEAR & PRIOR YEAR)")
    print("=" * 80)
    facts_json = fetch_company_facts_json(cik_str, user_agent)
    if not facts_json:
        sys.exit(1)

    facts, fy, end_date = extract_facts_for_latest_fy(facts_json)

    print(f"Latest Fiscal Year: FY {fy} | Period End Date: {end_date}")
    print("-" * 125)
    header = f"{'Concept':<25s} | {'Tag':<45s} | {'Period End':<10s} | {'Current (FY)':>18s} | {'Prior (FY-1)':>18s} | {'Filing Accn'}"
    print(header)
    print("-" * 125)

    for cname, finfo in facts.items():
        tag = finfo.get("tag", "N/A")
        pend = finfo.get("period_end", "N/A")
        cval = format_num(finfo.get("current_val"))
        pval = format_num(finfo.get("prior_val"))
        accn = finfo.get("accn", "N/A")
        print(f"{cname:<25s} | {tag:<45s} | {pend:<10s} | {cval:>18s} | {pval:>18s} | {accn}")

    print("-" * 125)
    print()
    return facts, fy, end_date


def step_5_calculator(facts: Dict[str, Dict[str, Any]], price: Optional[float] = None) -> Dict[str, Any]:
    """
    Step 5: Calculator in code printing with full arithmetic:
      1. Revenue growth: (Rev_t - Rev_{t-1}) / Rev_{t-1}
      2. Operating margin: Operating Income_t / Revenue_t
      3. Return on average equity: Net Income_t / Average(Equity_t, Equity_{t-1})
      4. Debt to equity with current portion included: (LT_Debt_t + Current_Debt_t) / Equity_t
      5. Free cash flow: Cash_Operations_t - Additions_PPE_t
      6. P/E from --price: Price / Diluted_EPS_t
    """
    print("=" * 80)
    print("STEP 5: FINANCIAL RATIOS & CALCULATOR (WITH ARITHMETIC)")
    print("=" * 80)

    rev_cur = facts.get("Total Revenue", {}).get("current_val")
    rev_prior = facts.get("Total Revenue", {}).get("prior_val")
    op_inc = facts.get("Operating Income", {}).get("current_val")
    net_inc = facts.get("Net Income", {}).get("current_val")
    eps = facts.get("Diluted EPS", {}).get("current_val")
    eq_cur = facts.get("Stockholders' Equity", {}).get("current_val")
    eq_prior = facts.get("Stockholders' Equity", {}).get("prior_val")
    lt_debt = facts.get("Long-Term Debt", {}).get("current_val") or 0.0
    cur_debt = facts.get("Current Portion LT Debt", {}).get("current_val") or 0.0
    cfo = facts.get("Cash from Operations", {}).get("current_val")
    capex = facts.get("Additions to PPE", {}).get("current_val")

    results = {}

    # 1. Revenue Growth
    if rev_cur is not None and rev_prior is not None and rev_prior != 0:
        rev_growth = (rev_cur - rev_prior) / rev_prior
        results["revenue_growth"] = rev_growth
        print("1. Revenue Growth:")
        print(f"   Formula:    (Revenue_t - Revenue_{{t-1}}) / Revenue_{{t-1}}")
        print(f"   Arithmetic: ({format_num(rev_cur)} - {format_num(rev_prior)}) / {format_num(rev_prior)}")
        print(f"   Result:     {rev_growth * 100:.2f}%\n")
    else:
        print("1. Revenue Growth: N/A (Missing current or prior revenue)\n")

    # 2. Operating Margin
    if op_inc is not None and rev_cur is not None and rev_cur != 0:
        op_margin = op_inc / rev_cur
        results["operating_margin"] = op_margin
        print("2. Operating Margin:")
        print("   Formula:    Operating Income_t / Revenue_t")
        print(f"   Arithmetic: {format_num(op_inc)} / {format_num(rev_cur)}")
        print(f"   Result:     {op_margin * 100:.2f}%\n")
    else:
        print("2. Operating Margin: N/A\n")

    # 3. Return on Average Equity (ROAE)
    if net_inc is not None and eq_cur is not None and eq_prior is not None:
        avg_equity = (eq_cur + eq_prior) / 2.0
        if avg_equity != 0:
            roae = net_inc / avg_equity
            results["roae"] = roae
            print("3. Return on Average Equity (ROAE):")
            print("   Formula:    Net Income_t / ((Equity_t + Equity_{t-1}) / 2)")
            print(f"   Arithmetic: {format_num(net_inc)} / (({format_num(eq_cur)} + {format_num(eq_prior)}) / 2)")
            print(f"   Result:     {roae * 100:.2f}%\n")
        else:
            print("3. Return on Average Equity: N/A (Average equity is zero)\n")
    else:
        print("3. Return on Average Equity: N/A (Missing equity data)\n")

    # 4. Debt to Equity (with current portion included)
    if eq_cur is not None and eq_cur != 0:
        total_debt = lt_debt + cur_debt
        d_to_e = total_debt / eq_cur
        results["debt_to_equity"] = d_to_e
        print("4. Debt to Equity (Current Portion Included):")
        print("   Formula:    (Long-Term Debt_t + Current Portion_t) / Stockholders' Equity_t")
        print(f"   Arithmetic: ({format_num(lt_debt)} + {format_num(cur_debt)}) / {format_num(eq_cur)}")
        print(f"   Result:     {d_to_e:.4f} ({d_to_e * 100:.2f}%)\n")
    else:
        print("4. Debt to Equity: N/A\n")

    # 5. Free Cash Flow
    if cfo is not None and capex is not None:
        fcf = cfo - capex
        results["free_cash_flow"] = fcf
        print("5. Free Cash Flow (FCF):")
        print("   Formula:    Cash from Operations_t - Additions to Property and Equipment_t")
        print(f"   Arithmetic: {format_num(cfo)} - {format_num(capex)}")
        print(f"   Result:     {format_num(fcf)}\n")
    else:
        print("5. Free Cash Flow: N/A\n")

    # 6. P/E from --price
    if price is not None:
        if eps is not None and eps != 0:
            pe_ratio = price / eps
            results["pe_ratio"] = pe_ratio
            print(f"6. Price to Earnings (P/E) [Given Price = {price:.2f}]:")
            print("   Formula:    Price / Diluted EPS_t")
            print(f"   Arithmetic: {price:.2f} / {eps:.2f}")
            print(f"   Result:     {pe_ratio:.2f}x\n")
        else:
            print(f"6. P/E: N/A (Diluted EPS is 0 or unavailable)\n")
    else:
        print("6. Price to Earnings (P/E): Omitted (--price not provided in command line)\n")

    return results


def step_6_extract_release_lines(release_txt_path: Optional[Path]) -> Tuple[List[str], List[str]]:
    """
    Step 6: From the release text, print the lines that state the quarter's total revenue and diluted EPS.
    Returns: (matching_revenue_lines, matching_eps_lines)
    """
    print("=" * 80)
    print("STEP 6: EXTRACT EARNINGS RELEASE REVENUE & DILUTED EPS LINES")
    print("=" * 80)

    if not release_txt_path or not release_txt_path.exists():
        print("Earnings release text file not found. Run Step 3 first.", file=sys.stderr)
        return [], []

    with open(release_txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    # Heuristic pattern matching for lines stating quarter's revenue and diluted EPS
    rev_candidates = []
    eps_candidates = []

    q_keywords = [
        "quarter", "fourth quarter", "third quarter", "second quarter", "first quarter",
        "16-week", "13-week", "three months", "three-month", "q1", "q2", "q3", "q4"
    ]

    for line in lines:
        low = line.lower()
        has_quarter = any(k in low for k in q_keywords)
        has_num = any(ch in line for ch in ["$", "%"]) or any(w in low for w in ["billion", "million"])

        # Revenue / Net Sales
        if any(w in low for w in ["revenue", "net sales", "sales"]) and has_num:
            if has_quarter and not any(w in low for w in ["comparable sales"]):
                rev_candidates.append(line)

        # Diluted EPS / Net Income per share
        if any(w in low for w in ["per diluted share", "diluted eps", "diluted share", "gaap eps", "reported eps", "adjusted eps", "per share"]) and has_num:
            if has_quarter or any(w in low for w in ["gaap eps", "diluted", "net income"]):
                eps_candidates.append(line)

    print("Quarter Total Revenue / Sales Statement Line(s) in Release:")
    if rev_candidates:
        for l in rev_candidates[:2]:
            print(f'  "{l}"')
    else:
        print("  [Could not isolate a single narrative line; see full release text]")

    print("\nQuarter Diluted EPS Statement Line(s) in Release:")
    if eps_candidates:
        for l in eps_candidates[:2]:
            print(f'  "{l}"')
    else:
        print("  [Could not isolate a single narrative line; see full release text]")

    print()
    return rev_candidates, eps_candidates


def step_7_peers(
    peers: List[str],
    user_agent: str,
    target_ticker: str,
    target_facts: Dict[str, Dict[str, Any]],
    output_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Step 7: For each peer, the same facts and the operating margin on the same definition.
    Save the facts beside the texts.
    """
    print("=" * 80)
    print("STEP 7: PEER COMPARISON (XBRL FACTS & OPERATING MARGIN ON SAME DEFINITION)")
    print("=" * 80)

    # SEC tickers map for fast lookup
    resp = sec_get("https://www.sec.gov/files/company_tickers.json", user_agent)
    tickers_map = resp.json() if resp.status_code == 200 else {}

    peer_results = []

    # Include target company as base
    target_rev = target_facts.get("Total Revenue", {}).get("current_val")
    target_op = target_facts.get("Operating Income", {}).get("current_val")
    target_margin = (target_op / target_rev) if (target_op and target_rev) else None
    target_end = target_facts.get("Total Revenue", {}).get("period_end", "")
    target_fy = target_facts.get("Total Revenue", {}).get("fy", "")

    print(f"Target Company: {target_ticker.upper()} (FY {target_fy}, Ended {target_end})")
    print(f"Total Revenue:    {format_num(target_rev)}")
    print(f"Operating Income: {format_num(target_op)}")
    print(f"Operating Margin: {target_margin * 100:.2f}%" if target_margin is not None else "N/A")
    print("-" * 80)

    all_data_to_save = {
        "target": {
            "ticker": target_ticker.upper(),
            "fy": target_fy,
            "period_end": target_end,
            "facts": target_facts,
            "operating_margin": target_margin,
        },
        "peers": {},
    }

    for peer_raw in peers:
        peer = peer_raw.strip().upper()
        if not peer:
            continue

        # Resolve CIK
        cik_str = None
        title = peer
        for item in tickers_map.values():
            if item.get("ticker", "").upper() == peer:
                cik_str = str(item["cik_str"]).zfill(10)
                title = item.get("title", peer)
                break

        if not cik_str:
            print(f"Skipping peer {peer}: Ticker not found in SEC database.")
            continue

        # Fetch facts
        facts_json = fetch_company_facts_json(cik_str, user_agent)
        if not facts_json:
            print(f"Skipping peer {peer}: Facts unavailable.")
            continue

        try:
            pfacts, pfy, pend = extract_facts_for_latest_fy(facts_json)
        except Exception as e:
            print(f"Error parsing facts for {peer}: {e}")
            continue

        prev = pfacts.get("Total Revenue", {}).get("current_val")
        pop = pfacts.get("Operating Income", {}).get("current_val")
        prev_tag = pfacts.get("Total Revenue", {}).get("tag", "")
        pmargin = (pop / prev) if (pop and prev) else None

        print(f"Peer:             {title} ({peer})")
        print(f"CIK:              {cik_str}")
        print(f"Latest 10-K FY:   FY {pfy} (Period End: {pend})")
        print(f"Revenue Tag:      {prev_tag}")
        print(f"Total Revenue:    {format_num(prev)}")
        print(f"Operating Income: {format_num(pop)}")
        if pmargin is not None:
            print(f"Operating Margin: {pop:,.0f} / {prev:,.0f} = {pmargin * 100:.2f}%\n")
        else:
            print("Operating Margin: N/A\n")

        peer_entry = {
            "ticker": peer,
            "title": title,
            "cik": cik_str,
            "fy": pfy,
            "period_end": pend,
            "revenue_tag": prev_tag,
            "total_revenue": prev,
            "operating_income": pop,
            "operating_margin": pmargin,
            "facts": pfacts,
        }
        peer_results.append(peer_entry)
        all_data_to_save["peers"][peer] = peer_entry

    # Save facts beside the texts in output_dir
    if output_dir and output_dir.exists():
        facts_path = output_dir / "facts.json"
        with open(facts_path, "w", encoding="utf-8") as f:
            json.dump(all_data_to_save, f, indent=2, default=str)
        print(f"Facts successfully saved beside filings at:\n -> {facts_path}\n")

    return peer_results


def find_latest_run_folder(ticker: str) -> Optional[Path]:
    """Find the most recent output folder for a given ticker."""
    candidates = list(Path.cwd().glob(f"{ticker.upper()}_*"))
    candidates = [p for p in candidates if p.is_dir()]
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="FIN 67110 - Equity Research Desk (Data Side). Section 3.1 of Francis & Zhang (2026)."
    )
    parser.add_argument("ticker", type=str, help="Company stock ticker symbol")
    parser.add_argument("--peers", type=str, default="", help="Comma-separated list of peer tickers")
    parser.add_argument("--price", type=float, default=None, help="Stock closing price for P/E computation")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4, 5, 6, 7], default=None, help="Run one step only (1-7)")

    args = parser.parse_args()
    user_agent = get_sec_user_agent()
    ticker = args.ticker.strip().upper()
    peers_list = [p.strip().upper() for p in args.peers.split(",") if p.strip()] if args.peers else []

    target_step = args.step

    # Single-step mode execution paths
    if target_step == 1:
        step_1_resolve_ticker(ticker, user_agent)
        return

    if target_step == 2:
        cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
        step_2_list_filings(cik_str, cik_int, user_agent)
        return

    if target_step == 3:
        cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
        filings = step_2_list_filings(cik_str, cik_int, user_agent)
        step_3_download_and_save_documents(cik_str, cik_int, filings, user_agent, ticker)
        return

    if target_step == 4:
        cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
        step_4_fetch_facts(cik_str, user_agent)
        return

    if target_step == 5:
        cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
        facts, fy, end_date = step_4_fetch_facts(cik_str, user_agent)
        step_5_calculator(facts, price=args.price)
        return

    if target_step == 6:
        run_folder = find_latest_run_folder(ticker)
        release_path = (run_folder / "8-K_Ex99-1.txt") if run_folder else None
        if not release_path or not release_path.exists():
            cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
            filings = step_2_list_filings(cik_str, cik_int, user_agent)
            run_folder, release_path = step_3_download_and_save_documents(cik_str, cik_int, filings, user_agent, ticker)
        step_6_extract_release_lines(release_path)
        return

    if target_step == 7:
        cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
        facts, fy, end_date = step_4_fetch_facts(cik_str, user_agent)
        run_folder = find_latest_run_folder(ticker)
        step_7_peers(peers_list, user_agent, ticker, facts, output_dir=run_folder)
        return

    # Default: Run all seven steps in order
    cik_str, title, cik_int = step_1_resolve_ticker(ticker, user_agent)
    filings = step_2_list_filings(cik_str, cik_int, user_agent)
    work_dir, release_txt_path = step_3_download_and_save_documents(
        cik_str=cik_str,
        cik_int=cik_int,
        filings=filings,
        user_agent=user_agent,
        ticker=ticker,
    )
    facts, fy, end_date = step_4_fetch_facts(cik_str, user_agent)
    ratios = step_5_calculator(facts, price=args.price)
    rev_lines, eps_lines = step_6_extract_release_lines(release_txt_path)
    step_7_peers(
        peers=peers_list,
        user_agent=user_agent,
        target_ticker=ticker,
        target_facts=facts,
        output_dir=work_dir,
    )


if __name__ == "__main__":
    main()
