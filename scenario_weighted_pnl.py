"""
Scenario-Weighted P&L -- USD/INR Call Spread
-----------------------------------------------
Connects Section 6 (trade structure) and Section 7 (scenario tree) of the
main note, which sat side-by-side but weren't quantitatively linked. Instead
of reading the payoff table and the scenario probabilities separately, this
runs a Monte Carlo simulation: draw a scenario per its stated probability,
sample a spot level within that scenario's range, price the call spread,
and repeat many times to get an actual expected value and risk profile --
not just point-estimate payoffs at three midpoints.

Distribution choice: triangular within each scenario's range (peaked at the
midpoint, tapering to the edges) rather than uniform -- a reasonable
assumption when a range is given as a central estimate, and it avoids
artificially fat tails right at the scenario boundaries.
"""

import numpy as np

RNG = np.random.default_rng(seed=7)  # fixed seed so results are reproducible for the note
N_SIMULATIONS = 200_000

# Scenario tree from the main note, Section 7
SCENARIOS = [
    # name,                    probability, low,  high
    ("Bull USD / Bear INR",    0.40,        97.0, 98.0),
    ("Base case",              0.40,        94.0, 96.0),
    ("Bear USD / Bull INR",    0.20,        92.0, 93.0),
]

# Trade structure from Section 6
LONG_STRIKE = 96.50
SHORT_STRIKE = 98.00
NET_PREMIUM = 0.35


def call_spread_payoff(spot):
    long_leg = np.maximum(spot - LONG_STRIKE, 0.0)
    short_leg = np.maximum(spot - SHORT_STRIKE, 0.0)
    return long_leg - short_leg - NET_PREMIUM


def simulate():
    probs = np.array([s[1] for s in SCENARIOS])
    assert abs(probs.sum() - 1.0) < 1e-9, "Scenario probabilities must sum to 1"

    scenario_idx = RNG.choice(len(SCENARIOS), size=N_SIMULATIONS, p=probs)
    spots = np.empty(N_SIMULATIONS)

    for i, (name, prob, low, high) in enumerate(SCENARIOS):
        mask = scenario_idx == i
        n = mask.sum()
        mode = (low + high) / 2
        spots[mask] = RNG.triangular(low, mode, high, size=n)

    pnl = call_spread_payoff(spots)
    return spots, pnl, scenario_idx


def main():
    spots, pnl, scenario_idx = simulate()

    print("=" * 64)
    print(" SCENARIO-WEIGHTED P&L -- USD/INR CALL SPREAD")
    print(f" {N_SIMULATIONS:,} simulations | seed=7 | structure: long {LONG_STRIKE} "
          f"call / short {SHORT_STRIKE} call, net premium {NET_PREMIUM}")
    print("=" * 64)

    for i, (name, prob, low, high) in enumerate(SCENARIOS):
        mask = scenario_idx == i
        print(f" {name:<22s} ({prob:.0%}, range {low}-{high}): "
              f"mean P&L = {pnl[mask].mean():+.3f}")

    print("-" * 64)
    print(f" Overall expected P&L (probability-weighted): {pnl.mean():+.3f} per USD notional")
    print(f" Std. dev. of P&L:                              {pnl.std():.3f}")
    print(f" P(profit) [P&L > 0]:                           {(pnl > 0).mean():.1%}")
    print(f" P(max loss, i.e. P&L <= -{NET_PREMIUM}):                    {(pnl <= -NET_PREMIUM + 1e-9).mean():.1%}")

    var_95 = np.percentile(pnl, 5)
    cvar_95 = pnl[pnl <= var_95].mean()
    print(f" 95% VaR (5th percentile P&L):                  {var_95:+.3f}")
    print(f" 95% CVaR (mean P&L in worst 5% of outcomes):   {cvar_95:+.3f}")
    print("=" * 64)

    print("\nReading this alongside the note:")
    print(f" - Expected value is positive ({pnl.mean():+.3f}) but modest relative to the")
    print(f"   {NET_PREMIUM} premium at risk -- the trade is a positive-expectancy, capped-risk")
    print("   way to express the thesis, not a high-conviction directional bet.")
    print(f" - {(pnl <= -NET_PREMIUM + 1e-9).mean():.0%} of outcomes hit max loss (premium), concentrated in the")
    print("   Base and Bear-USD scenarios where spot never clears 96.50.")
    print(" - Worth comparing against a plain spot position or a wider-strike spread")
    print("   if you want to trade off premium cost against capped upside.")


if __name__ == "__main__":
    main()
