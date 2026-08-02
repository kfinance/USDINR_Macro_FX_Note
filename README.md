# USD/INR Macro-FX Thesis: A Covered Interest Parity Cross-Check

A macro/FX research project testing whether the USD/INR forward market is pricing
rupee depreciation fairly, or paying a risk premium for it — combining a
research note, a historical backtest, a live pricing dashboard, an event-vol
model, and a Monte Carlo scenario simulation.

## Key finding

The market-quoted 3M USD/INR forward premium (3.00% ann.) sits ~1.4
percentage points above the Covered Interest Rate Parity (CIRP) fair value
implied by the India-US policy rate differential (1.625%). A 26-quarter
historical backtest (2020–2026) shows the rate differential has essentially
no predictive power over subsequent USD/INR moves (R² ≈ 0.01) — supporting
the read that this gap is a genuine risk premium (FPI-flow volatility,
oil/geopolitical risk), not a mispricing to fade blindly.

## Contents

| File | What it does |
|---|---|
| `USDINR_Macro_FX_Note.docx` | Full research note — Fed/RBI backdrop, FPI/FDI flow analysis, CIRP fair-value framework, trade structure, scenario tree, historical sanity check |
| `rate_differential_backtest.py` | Backtests the India-US rate differential against realized USD/INR returns (2020–2026, quarterly); outputs the R²/correlation stats and a chart |
| `backtest_chart.png` | Output chart from the backtest (spot vs. differential, and the regression scatter) |
| `usdinr_rate_differential_dataset.csv` | The compiled quarterly dataset (repo rate, Fed funds, USD/INR spot) used for the backtest |
| `cirp_gap_dashboard.py` | Live CIRP-gap dashboard — pulls Fed funds rate (FRED API) and USD/INR spot (Yahoo Finance) and re-computes the fair-value gap on demand; falls back to cached values if run somewhere without API access |
| `event_vol_stripper.py` | Variance-additivity model that strips out how much of the USD/INR options-implied vol is attributable to the RBI (Aug 5) and FOMC (Sept 15–16) decisions specifically, vs. background vol |
| `scenario_weighted_pnl.py` | Monte Carlo simulation (200k draws) that prices the note's call-spread structure across the probability-weighted scenario tree, producing expected P&L, VaR, and probability of profit |

## Methodology in brief

1. **Fair value** — CIRP says the forward premium should equal the nominal
   rate differential. Compare market-quoted premium to that benchmark.
2. **Validate historically** — does the differential actually predict rupee
   moves? Backtest says: not really, which reframes the "gap" as a risk
   premium rather than an anomaly.
3. **Express the view with defined risk** — a call spread, not a spot bet,
   given the two-sided flow picture (record FPI outflows in H1 2026 vs. a
   July reversal).
4. **Price the event risk explicitly** — strip out how much of the option's
   implied vol comes from the two scheduled decisions inside the trade
   window, instead of guessing a flat number.
5. **Quantify the payoff** — Monte Carlo the scenario tree through the
   actual option structure to get expected value and downside, not just
   payoffs at three point estimates.

## Running the scripts

```bash
pip install pandas numpy matplotlib scipy yfinance
python3 rate_differential_backtest.py
python3 event_vol_stripper.py
python3 scenario_weighted_pnl.py

# optional: needs a free FRED API key + outbound network access for a live pull
export FRED_API_KEY=your_key_here
python3 cirp_gap_dashboard.py
```

## Data & disclaimer

Rate and flow data sourced from RBI, US Federal Reserve, and BLS public
releases as of August 2026 (full source list in the note). The 2020–2023
portion of the backtest dataset uses quarter-level approximations from
published exchange-rate history rather than exact daily fixes; 2023 onward
figures are more precisely sourced. Options pricing and IV inputs are
illustrative, not live dealer quotes. This project is for academic and
portfolio-demonstration purposes only — not investment advice.

