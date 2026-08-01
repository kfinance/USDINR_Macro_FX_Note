"""
USD/INR Rate-Differential Backtest
-----------------------------------
Question: does the India-US nominal policy-rate differential (the input to the
Covered Interest Rate Parity model used in the main strategy note) actually
predict subsequent USD/INR moves? Or is the currency driven by something the
rate differential alone doesn't capture (flow shocks, oil, geopolitics)?

This directly tests the note's central "honest gap" finding: that the market's
forward premium (~3.0% ann.) prices in more depreciation than the nominal rate
differential (~1.6%) implies. If the historical differential-vs-return
relationship is weak, that's independent evidence the forward market IS
pricing a risk premium beyond pure carry -- not just this cycle, but as a
recurring pattern.

DATA NOTE
---------
This sandbox has no live market-data feed (no Bloomberg/Refinitiv/NSE API
access). The quarterly series below is manually compiled from public sources
researched for this project:
  - India repo rate: RBI MPC announcements (full history, dates exact)
  - US Fed funds rate: FOMC meeting history (full history, dates exact)
  - USD/INR spot: quarter-end/quarter-average levels from published exchange-
    rate history (exchangerates.org, poundsterlinglive, Forbes India, RBI
    reference rate via CEIC). 2023 onward figures are closely sourced;
    2020-2022 figures are reasonable quarter-level approximations from
    widely-reported year ranges, since exact quarter-end fixes weren't part
    of the source set pulled for this project.

This is a compact, directionally-honest dataset for a portfolio-piece
backtest -- not a substitute for a Bloomberg/Refinitiv time series. Swap in
`load_data()` with a real feed (e.g. `yfinance`, NSE data vendor, or a CSV
export) to make this production-grade; the analysis logic below is unchanged
either way.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# ---------------------------------------------------------------------------
# 1. DATA: quarterly (India repo %, US Fed funds mid %, USD/INR spot)
# ---------------------------------------------------------------------------
data = [
    # quarter,      repo,  fedfunds_mid, usdinr
    ("2020-Q1",     4.40,  0.125,        75.4),
    ("2020-Q2",     4.00,  0.125,        75.5),
    ("2020-Q3",     4.00,  0.125,        73.5),
    ("2020-Q4",     4.00,  0.125,        73.1),
    ("2021-Q1",     4.00,  0.125,        73.5),
    ("2021-Q2",     4.00,  0.125,        74.3),
    ("2021-Q3",     4.00,  0.125,        73.5),
    ("2021-Q4",     4.00,  0.125,        74.3),
    ("2022-Q1",     4.00,  0.375,        76.2),
    ("2022-Q2",     4.90,  1.625,        78.9),
    ("2022-Q3",     5.90,  3.125,        81.3),
    ("2022-Q4",     6.25,  4.375,        82.7),
    ("2023-Q1",     6.50,  4.875,        82.2),
    ("2023-Q2",     6.50,  5.125,        82.0),
    ("2023-Q3",     6.50,  5.375,        83.1),
    ("2023-Q4",     6.50,  5.375,        83.2),
    ("2024-Q1",     6.50,  5.375,        83.4),
    ("2024-Q2",     6.50,  5.375,        83.5),
    ("2024-Q3",     6.50,  4.875,        83.8),
    ("2024-Q4",     6.50,  4.375,        85.6),
    ("2025-Q1",     6.25,  4.375,        85.5),
    ("2025-Q2",     5.50,  4.375,        85.8),
    ("2025-Q3",     5.50,  4.125,        87.0),
    ("2025-Q4",     5.25,  3.625,        88.5),
    ("2026-Q1",     5.25,  3.625,        91.0),
    ("2026-Q2",     5.25,  3.625,        95.0),
    ("2026-Q3",     5.25,  3.625,        95.4),  # partial quarter (Jul 2026 only)
]

df = pd.DataFrame(data, columns=["quarter", "repo", "fedfunds_mid", "usdinr"])
df["nominal_diff"] = df["repo"] - df["fedfunds_mid"]

# ---------------------------------------------------------------------------
# 2. Forward return: % change in USD/INR over the NEXT quarter
#    (i.e. does today's differential predict next quarter's rupee move?)
# ---------------------------------------------------------------------------
df["fwd_1q_return_pct"] = df["usdinr"].pct_change().shift(-1) * 100

analysis = df.dropna(subset=["fwd_1q_return_pct"]).copy()

# ---------------------------------------------------------------------------
# 3. Regression: nominal_diff -> next-quarter USD/INR return
# ---------------------------------------------------------------------------
slope, intercept, r_value, p_value, std_err = stats.linregress(
    analysis["nominal_diff"], analysis["fwd_1q_return_pct"]
)
r_squared = r_value ** 2
corr = analysis["nominal_diff"].corr(analysis["fwd_1q_return_pct"])

print("=" * 70)
print("USD/INR RATE-DIFFERENTIAL BACKTEST -- SUMMARY")
print("=" * 70)
print(f"Sample: {analysis['quarter'].iloc[0]} to {analysis['quarter'].iloc[-1]} "
      f"({len(analysis)} quarterly observations)")
print(f"\nCorrelation (nominal differential vs next-Q USD/INR return): {corr:.3f}")
print(f"Regression R-squared:                                          {r_squared:.3f}")
print(f"Regression slope (return % per 1pp of differential):           {slope:.3f}")
print(f"p-value:                                                       {p_value:.3f}")

print("\nCurrent snapshot (2026-Q3, per the main strategy note):")
current_diff = df["nominal_diff"].iloc[-1]
print(f"  Nominal differential today:        {current_diff:.2f}%")
print(f"  Market 3M forward premium (ann.):  3.00%  <- from RBI interbank data")
print(f"  Gap (market premium - differential): {3.00 - current_diff:.2f}pp")

print("\nInterpretation:")
if r_squared < 0.15:
    print(" -> Weak/no historical relationship between the nominal rate")
    print("    differential and subsequent 1-quarter USD/INR moves in this")
    print("    sample. That supports the note's reading of the forward-premium")
    print("    gap: the currency has historically been driven more by capital-")
    print("    flow shocks and risk events (2022 hiking cycle, 2026 Hormuz/oil")
    print("    shock) than by the carry differential alone -- so a ~1.4pp")
    print("    'unexplained' forward premium today is consistent with the")
    print("    market pricing a risk premium, not an anomaly to fade blindly.")
else:
    print(" -> Meaningful historical relationship found -- the differential")
    print("    has some predictive value in this sample; the current forward-")
    print("    premium gap deserves more weight as a directional signal.")
print("=" * 70)

# ---------------------------------------------------------------------------
# 4. Charts
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(9, 9))

# Top: differential vs spot over time (twin axis)
ax1 = axes[0]
ax1.plot(df["quarter"], df["usdinr"], color="#0F4C81", marker="o", markersize=3, label="USD/INR spot")
ax1.set_ylabel("USD/INR", color="#0F4C81")
ax1.tick_params(axis="y", labelcolor="#0F4C81")
ax1.set_xticks(range(0, len(df), 2))
ax1.set_xticklabels(df["quarter"][::2], rotation=45, ha="right", fontsize=8)
ax1.set_title("USD/INR spot vs. India-US nominal rate differential (quarterly)")

ax2 = ax1.twinx()
ax2.plot(df["quarter"], df["nominal_diff"], color="#B45309", marker="s", markersize=3, label="Nominal differential (Repo - Fed funds)")
ax2.set_ylabel("Nominal differential (pp)", color="#B45309")
ax2.tick_params(axis="y", labelcolor="#B45309")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

# Bottom: scatter + regression
ax3 = axes[1]
ax3.scatter(analysis["nominal_diff"], analysis["fwd_1q_return_pct"], color="#0F4C81", s=35)
xs = np.linspace(analysis["nominal_diff"].min(), analysis["nominal_diff"].max(), 50)
ax3.plot(xs, intercept + slope * xs, color="#B45309", linewidth=2,
          label=f"fit: R\u00b2={r_squared:.2f}, p={p_value:.2f}")
ax3.axhline(0, color="grey", linewidth=0.8)
ax3.set_xlabel("Nominal rate differential, quarter t (pp)")
ax3.set_ylabel("USD/INR return, quarter t+1 (%)")
ax3.set_title("Does the rate differential predict next-quarter rupee moves?")
ax3.legend(fontsize=9)

plt.tight_layout()
plt.savefig("/home/claude/fx_note/backtest_chart.png", dpi=150)
print("\nChart saved: backtest_chart.png")

df.to_csv("/home/claude/fx_note/usdinr_rate_differential_dataset.csv", index=False)
print("Dataset saved: usdinr_rate_differential_dataset.csv")
