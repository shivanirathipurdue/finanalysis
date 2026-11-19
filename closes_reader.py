#!/usr/bin/env python3
"""
FIN 67110 - Closes Reader (Week 4 Prework & Lab 06 Data Contract)
Implements two required market close functions:
  1. get_daily_closes(ticker, start_date, end_date) -> Dict[str, float]
  2. get_last_close_before(ticker, target_datetime) -> Tuple[Optional[float], Optional[str]]

Data Sources:
  - LSEG Workspace (lseg-data Python library) using LSEG_APP_KEY from .env
  - Fallback local CSV/JSON file using CLOSES_FILE_PATH from .env
  - If data is absent, returns 'not available' / None without crashing the agent team.

Rule: Takes a trading day's close as 4:00 PM Eastern (16:00:00). Zero hardcoded company names.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Cutoff: Trading day close is 4:00 PM Eastern
MARKET_CLOSE_TIME = time(16, 0, 0)


def load_env_config() -> Tuple[Optional[str], Optional[Path]]:
    """Load LSEG_APP_KEY and CLOSES_FILE_PATH from .env."""
    load_dotenv()
    script_dir = Path(__file__).resolve().parent
    load_dotenv(script_dir / ".env")

    app_key = os.getenv("LSEG_APP_KEY")
    if app_key in ["paste-here", "", None]:
        app_key = None

    file_path_str = os.getenv("CLOSES_FILE_PATH")
    file_path = None
    if file_path_str:
        candidate = Path(file_path_str)
        if not candidate.is_absolute():
            candidate = script_dir / file_path_str
        if candidate.exists():
            file_path = candidate
    return (app_key.strip() if app_key else None, file_path)


def read_closes_from_file(file_path: Path, ticker: str) -> Dict[str, float]:
    """Read historical daily closes from a local CSV or JSON file."""
    closes: Dict[str, float] = {}
    if not file_path.exists():
        return closes

    clean_ticker = ticker.strip().upper()
    try:
        if file_path.suffix.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if clean_ticker in data:
                    for k, v in data[clean_ticker].items():
                        if isinstance(v, dict):
                            c_val = v.get("close", v.get("Close", None))
                            if c_val is not None:
                                closes[k] = float(c_val)
                        else:
                            closes[k] = float(v)
                    return closes
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_ticker = row.get("Ticker", row.get("ticker", "")).strip().upper()
                    if row_ticker == clean_ticker or not row_ticker:
                        date_str = row.get("Date", row.get("date", "")).strip()
                        close_str = row.get("Close", row.get("close", "")).strip()
                        if date_str and close_str:
                            try:
                                closes[date_str] = float(close_str.replace("$", "").replace(",", ""))
                            except ValueError:
                                pass
    except Exception as e:
        print(f"[Notice] Error reading local closes file ({e}).", file=sys.stderr)
    return closes


def read_closes_and_volumes_from_file(file_path: Path, ticker: str) -> Dict[str, Dict[str, float]]:
    """Read historical daily closes and trading volume from local JSON or CSV file."""
    records: Dict[str, Dict[str, float]] = {}
    if not file_path.exists():
        return records

    clean_ticker = ticker.strip().upper()
    try:
        if file_path.suffix.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if clean_ticker in data:
                    for k, v in data[clean_ticker].items():
                        if isinstance(v, dict):
                            c = float(v.get("close", v.get("Close", 0.0)))
                            vol = float(v.get("volume", v.get("Volume", 0.0)))
                            records[k] = {"close": c, "volume": vol}
                        else:
                            records[k] = {"close": float(v), "volume": 0.0}
                    return records
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_ticker = row.get("Ticker", row.get("ticker", "")).strip().upper()
                    if row_ticker == clean_ticker or not row_ticker:
                        d_str = row.get("Date", row.get("date", "")).strip()
                        c_str = row.get("Close", row.get("close", "")).strip()
                        vol_str = row.get("Volume", row.get("volume", "0")).strip()
                        if d_str and c_str:
                            try:
                                c = float(c_str.replace("$", "").replace(",", ""))
                                vol = float(vol_str.replace(",", "")) if vol_str else 0.0
                                records[d_str] = {"close": c, "volume": vol}
                            except ValueError:
                                pass
    except Exception as e:
        print(f"[Notice] Error reading local closes/volumes file ({e}).", file=sys.stderr)
    return records


def read_closes_from_lseg(app_key: str, ticker: str, start_date: str, end_date: str) -> Dict[str, float]:
    """Fetch official daily closes from LSEG Workspace using lseg-data."""
    closes: Dict[str, float] = {}
    try:
        import lseg.data as ld
        ld.open_session(app_key=app_key)
        df = ld.get_history(
            universe=[ticker],
            fields=["TR.PriceClose"],
            start=start_date,
            end=end_date,
            interval="1D"
        )
        if df is not None and not df.empty:
            for idx, row in df.iterrows():
                dt_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                val = row.get("TR.PriceClose", row.get("Close", None))
                if val is not None and not pd.isna(val):
                    closes[dt_str] = float(val)
        ld.close_session()
    except Exception as e:
        print(f"[Notice] LSEG Data Library call failed or not configured ({e}).", file=sys.stderr)
    return closes


def get_daily_closes_and_volumes(ticker: str, start_date: str, end_date: str) -> Dict[str, Dict[str, float]]:
    """
    Contract Function:
    Retrieve daily closes and volumes for a ticker between start_date and end_date (inclusive).
    Returns: Dict mapping 'YYYY-MM-DD' -> {'close': float, 'volume': float}.
    """
    app_key, file_path = load_env_config()
    clean_ticker = ticker.strip().upper()
    data: Dict[str, Dict[str, float]] = {}

    if file_path and file_path.exists():
        file_data = read_closes_and_volumes_from_file(file_path, clean_ticker)
        data = {d: v for d, v in file_data.items() if start_date <= d <= end_date}

    return data


def get_median_daily_dollar_volume(ticker: str, start_date: str, end_date: str) -> Optional[float]:
    """
    Contract Function:
    Compute the median daily dollar volume (Close * Volume) across available days in the window.
    Returns: float dollar amount or None if unavailable.
    """
    records = get_daily_closes_and_volumes(ticker, start_date, end_date)
    if not records:
        return None
    dollar_volumes = [
        v["close"] * v["volume"]
        for v in records.values()
        if v.get("close") and v.get("volume", 0) > 0
    ]
    if not dollar_volumes:
        return None
    sorted_vols = sorted(dollar_volumes)
    mid = len(sorted_vols) // 2
    if len(sorted_vols) % 2 == 1:
        return sorted_vols[mid]
    else:
        return (sorted_vols[mid - 1] + sorted_vols[mid]) / 2.0


def get_daily_closes(ticker: str, start_date: str, end_date: str) -> Dict[str, float]:
    """
    Contract Function 1:
    Retrieve official daily closes for a ticker between start_date and end_date (inclusive).
    Returns a dict mapping 'YYYY-MM-DD' -> float close price.
    """
    app_key, file_path = load_env_config()
    clean_ticker = ticker.strip().upper()
    closes: Dict[str, float] = {}

    # Try LSEG if app key is available
    if app_key:
        closes = read_closes_from_lseg(app_key, clean_ticker, start_date, end_date)

    # Fallback to local file if LSEG returned nothing
    if not closes and file_path and file_path.exists():
        file_closes = read_closes_from_file(file_path, clean_ticker)
        closes = {d: p for d, p in file_closes.items() if start_date <= d <= end_date}

    return closes


def get_last_close_before(ticker: str, target_dt: datetime) -> Tuple[Optional[float], Optional[str]]:
    """
    Contract Function 2:
    Retrieve the last official trading close before a given filing date and time.
    Trading day close is taken as 4:00 PM Eastern (16:00:00).
    - If target_dt is on day D after 16:00:00, day D's close is eligible.
    - If target_dt is on day D at or before 16:00:00, the latest prior day D-1 close is taken.
    Returns: (close_price, price_date_str) or (None, None) if not available.
    """
    clean_ticker = ticker.strip().upper()
    # Lookback window of 30 days before target_dt
    start_dt = target_dt.date() - timedelta(days=30)
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = target_dt.strftime("%Y-%m-%d")

    closes = get_daily_closes(clean_ticker, start_str, end_str)
    if not closes:
        return None, None

    sorted_dates = sorted(closes.keys())
    target_date_str = target_dt.strftime("%Y-%m-%d")

    # Determine eligibility of target date
    if target_dt.time() >= MARKET_CLOSE_TIME:
        eligible_dates = [d for d in sorted_dates if d <= target_date_str]
    else:
        eligible_dates = [d for d in sorted_dates if d < target_date_str]

    if not eligible_dates:
        return None, None

    best_date = eligible_dates[-1]
    return closes[best_date], best_date


def format_close_output(ticker: str, target_iso: str) -> str:
    """Helper to parse filing time and print formatted close result."""
    clean_ticker = ticker.strip().upper()
    try:
        dt = datetime.fromisoformat(target_iso)
    except ValueError:
        return f"Error: Invalid datetime format '{target_iso}'. Use YYYY-MM-DDTHH:MM:SS."

    close_val, close_date = get_last_close_before(clean_ticker, dt)
    if close_val is None:
        return f"{clean_ticker} last close before {target_iso}: not available"
    return f"{clean_ticker} last close before {target_iso}: ${close_val:.2f} on {close_date}"


def main():
    parser = argparse.ArgumentParser(
        description="FIN 67110 - Official Closes Reader (LSEG Workspace & Local File Support)."
    )
    parser.add_argument("ticker", type=str, help="Stock ticker symbol")
    parser.add_argument("--before", type=str, help="Filing timestamp in ISO format: YYYY-MM-DDTHH:MM:SS")
    parser.add_argument("--start", type=str, default="", help="Start date: YYYY-MM-DD")
    parser.add_argument("--end", type=str, default="", help="End date: YYYY-MM-DD")
    parser.add_argument("--median-volume", action="store_true", help="Print median daily dollar volume over start/end range")

    args = parser.parse_args()

    if args.median_volume and args.start and args.end:
        med_vol = get_median_daily_dollar_volume(args.ticker, args.start, args.end)
        if med_vol is None:
            print(f"{args.ticker.upper()} median daily dollar volume: not available")
        else:
            print(f"{args.ticker.upper()} median daily dollar volume ({args.start} to {args.end}): ${med_vol:,.2f}")
    elif args.before:
        result = format_close_output(args.ticker, args.before)
        print(result)
    elif args.start and args.end:
        daily = get_daily_closes(args.ticker, args.start, args.end)
        if not daily:
            print(f"{args.ticker.upper()} daily closes: not available")
        else:
            print(f"Daily Closes for {args.ticker.upper()} ({args.start} to {args.end}):")
            for d in sorted(daily.keys()):
                print(f"  {d}: ${daily[d]:.2f}")
    else:
        # Default test using current timestamp
        now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print(format_close_output(args.ticker, now_iso))


if __name__ == "__main__":
    main()
