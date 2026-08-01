"""
USD/INR CIRP Gap Dashboard
---------------------------
Live version of the "Fair-Value Framework" section from the main strategy
note: pulls current Fed funds rate + USD/INR spot automatically, and
computes the Covered Interest Rate Parity (CIRP) gap against the
market-quoted forward premium, so the signal in the note can be refreshed
any time without redoing the research by hand.

IMPORTANT -- run this on your own machine, not inside a locked-down sandbox.
This script needs outbound internet access to:
  - query1/query2.finance.yahoo.com   (via the `yfinance` package, no key needed)
  - api.stlouisfed.org                (FRED API, free key: https://fred.stlouisfed.org/docs/api/api_key.html)
If those hosts are blocked (as they are in this environment's network
allowlist), the script automatically falls back to DEMO_MODE using the last
values captured for the note (1 Aug 2026) so you can still see the dashboard
output and verify the logic before running it live.

Two inputs are NOT available via a free API and must be entered manually
after each release, since neither RBI nor NSE publish a clean open API for
them:
  - REPO_RATE            -> update after each bi-monthly MPC decision
  - MARKET_FWD_PREMIUM_3M -> update from RBI's weekly WSS or your broker's
                              NDF/forward desk quote

Usage:
  export FRED_API_KEY=your_key_here     # optional, enables live Fed funds pull
  python3 cirp_gap_dashboard.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

# ---------------------------------------------------------------------------
# Manual inputs -- update these after each RBI MPC meeting / forward-desk check
# ---------------------------------------------------------------------------
REPO_RATE = 5.25                  # RBI repo rate, % (last set: Dec 2025, held since)
MARKET_FWD_PREMIUM_3M = 3.00      # USD/INR 3M forward premium, % ann. (RBI interbank, 10 Jul 2026)
GAP_ALERT_THRESHOLD = 1.00        # flag if |gap| exceeds this many percentage points

# Cached fallback values (captured 1 Aug 2026, for DEMO_MODE / offline runs)
DEMO_FED_FUNDS_MID = 3.625
DEMO_USDINR_SPOT = 95.37


def fetch_fed_funds_mid():
    """Pull the current Fed funds target-range midpoint from FRED (needs FRED_API_KEY)."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY not set")
    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=DFEDTARU&api_key={api_key}&file_type=json&sort_order=desc&limit=1"
    )
    with urllib.request.urlopen(url, timeout=8) as resp:
        payload = json.loads(resp.read().decode())
    upper = float(payload["observations"][0]["value"])
    # DFEDTARU is the upper bound; approximate midpoint by subtracting 12.5bp
    return round(upper - 0.125, 3)


def fetch_usdinr_spot():
    """Pull the latest USD/INR spot via yfinance (needs outbound access to Yahoo Finance)."""
    import yfinance as yf
    hist = yf.Ticker("USDINR=X").history(period="5d")
    if hist.empty:
        raise RuntimeError("No data returned")
    return round(float(hist["Close"].iloc[-1]), 3)


def get_inputs():
    """Try live pulls; fall back to cached DEMO values with a clear warning."""
    demo_mode = False
    try:
        fed_funds_mid = fetch_fed_funds_mid()
    except Exception as e:
        print(f"[warn] Live Fed funds pull failed ({e}); using cached demo value.")
        fed_funds_mid = DEMO_FED_FUNDS_MID
        demo_mode = True

    try:
        usdinr_spot = fetch_usdinr_spot()
    except Exception as e:
        print(f"[warn] Live USD/INR pull failed ({e}); using cached demo value.")
        usdinr_spot = DEMO_USDINR_SPOT
        demo_mode = True

    return fed_funds_mid, usdinr_spot, demo_mode


def run_dashboard():
    fed_funds_mid, usdinr_spot, demo_mode = get_inputs()

    nominal_diff = REPO_RATE - fed_funds_mid
    gap = MARKET_FWD_PREMIUM_3M - nominal_diff

    print("=" * 62)
    print(f" USD/INR CIRP GAP DASHBOARD   {'[DEMO MODE]' if demo_mode else '[LIVE]'}")
    print(f" Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 62)
    print(f" India repo rate                    : {REPO_RATE:.2f}%")
    print(f" US Fed funds (mid, {'cached' if demo_mode else 'live'})       : {fed_funds_mid:.3f}%")
    print(f" Nominal rate differential           : {nominal_diff:.2f}%  <- CIRP fair value")
    print(f" USD/INR spot ({'cached' if demo_mode else 'live'})            : {usdinr_spot:.2f}")
    print("-" * 62)
    print(f" Market 3M forward premium (input)   : {MARKET_FWD_PREMIUM_3M:.2f}%")
    print(f" Gap (market premium - CIRP fair)    : {gap:+.2f}pp")
    print("-" * 62)

    if abs(gap) >= GAP_ALERT_THRESHOLD:
        direction = "MORE depreciation" if gap > 0 else "LESS depreciation"
        print(f" SIGNAL: market is pricing {direction} than the rate")
        print(f"         differential alone justifies (|gap| >= {GAP_ALERT_THRESHOLD}pp).")
        print(" Read alongside the flow data (FPI/FDI) in the main note before")
        print(" treating this as a standalone trade trigger.")
    else:
        print(" No signal: forward premium is broadly consistent with CIRP fair value.")
    print("=" * 62)

    if demo_mode:
        print("\nNote: one or more inputs used the cached 1-Aug-2026 fallback because")
        print("this run had no outbound access to the live data hosts. Run again from")
        print("a machine/network that allows query*.finance.yahoo.com and")
        print("api.stlouisfed.org for a fully live pull.")


if __name__ == "__main__":
    run_dashboard()
