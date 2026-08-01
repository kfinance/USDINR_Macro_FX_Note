"""
USD/INR Event-Vol Stripper
----------------------------
Ties the main strategy note's options structure into your planned "Nifty IV
Surface & Event-Vol Tracker" project -- same methodology, applied here to
USD/INR around the two scheduled events that fall inside the note's trade
window: the RBI MPC decision (Aug 5, 2026) and the FOMC decision (Sept 15-16,
2026).

METHODOLOGY (variance additivity / event-vol stripping)
---------------------------------------------------------
Standard result used by options desks (see Wright, "Event Day Options", NBER
WP 28306: FOMC-day variance risk premia are large and positive; and the CCIL
working paper on USD/INR options, which finds implied vol is elevated in a
window around known events and decays after). Total variance over a period
is additive across days:

    Var(T) = sum of daily variances over T

Split each period into "quiet" days (background vol) and "event" days
(elevated vol). If you observe ATM implied vol for a QUIET benchmark tenor
and for a tenor that SPANS an event, you can algebraically strip out how
much variance the event day(s) are contributing -- and back into an
event-day vol multiple, instead of guessing a single flat number for an
event-spanning option (which is what the main note's illustrative ~6-7% IV
assumption did).

INPUTS BELOW ARE ILLUSTRATIVE (no live USD/INR options IV feed in this
sandbox -- CCIL publishes an interbank implied-vol matrix but it is not a
free/open API). Swap in real ATM IV quotes from your broker/CCIL feed to
make this live; the stripping logic is what's reusable across both this
note and the Nifty IV Surface project.
"""

from datetime import date, datetime
from math import sqrt

TODAY = date(2026, 8, 2)

EVENTS = {
    "RBI MPC decision": date(2026, 8, 5),
    "FOMC decision (day 2)": date(2026, 9, 16),
}

# Illustrative ATM IV inputs (annualised %, calendar-day convention to match
# the forward-premia convention used in the main note)
IV_QUIET_1M = 6.0        # ATM IV for a 1M tenor with NO major scheduled event
DAYS_QUIET_1M = 30

IV_SPANNING_RBI = 6.8    # ATM IV for a short tenor that spans only the RBI decision
DAYS_SPANNING_RBI = 10   # e.g. a ~10-day option straddling Aug 5
N_EVENT_DAYS_RBI = 1

IV_SPANNING_FOMC = 7.2   # ATM IV for a short tenor spanning the FOMC decision
DAYS_SPANNING_FOMC = 12  # e.g. a ~12-day option straddling Sept 15-16
N_EVENT_DAYS_FOMC = 2    # two-day meeting


def strip_event_vol(iv_quiet_pct, days_quiet, iv_event_window_pct, days_event_window, n_event_days):
    """Return (event_day_vol_multiple, implied_event_day_ann_vol_pct)."""
    var_quiet_daily = (iv_quiet_pct / 100) ** 2 / 365
    total_var_event_window = (iv_event_window_pct / 100) ** 2 * (days_event_window / 365)
    var_from_quiet_days = var_quiet_daily * (days_event_window - n_event_days)
    var_from_event_days = total_var_event_window - var_from_quiet_days

    if var_from_event_days <= 0:
        raise ValueError("Event window IV isn't elevated enough vs quiet IV for this day count -- check inputs")

    event_day_daily_var = var_from_event_days / n_event_days
    multiple = sqrt(event_day_daily_var / var_quiet_daily)
    implied_ann_vol = sqrt(event_day_daily_var * 365) * 100
    return multiple, implied_ann_vol


def blended_iv_for_note_tenor(iv_quiet_pct, days_total, event_day_variances):
    """Rebuild a fair ATM IV for the note's actual ~2M tenor (spans BOTH events)."""
    var_quiet_daily = (iv_quiet_pct / 100) ** 2 / 365
    n_event_days_total = len(event_day_variances)
    var_quiet_portion = var_quiet_daily * (days_total - n_event_days_total)
    var_event_portion = sum(event_day_variances)
    total_var = var_quiet_portion + var_event_portion
    return sqrt(total_var * 365 / days_total) * 100


def main():
    print("=" * 66)
    print(" USD/INR EVENT-VOL STRIPPER")
    print(f" Run date: {TODAY.isoformat()}")
    print("=" * 66)

    for name, edate in EVENTS.items():
        days_to = (edate - TODAY).days
        print(f" {name:<28s}: {edate.isoformat()}  ({days_to} days away)")

    print("-" * 66)
    print(f" Quiet-tenor benchmark ATM IV (1M, no events): {IV_QUIET_1M:.2f}%")

    rbi_mult, rbi_event_vol = strip_event_vol(
        IV_QUIET_1M, DAYS_QUIET_1M, IV_SPANNING_RBI, DAYS_SPANNING_RBI, N_EVENT_DAYS_RBI
    )
    print(f"\n RBI decision (Aug 5) window IV: {IV_SPANNING_RBI:.2f}% over {DAYS_SPANNING_RBI}d")
    print(f"   -> implied RBI event-day vol multiple : {rbi_mult:.2f}x a quiet day")
    print(f"   -> implied RBI event-day annualised vol (illustrative): {rbi_event_vol:.1f}%")

    fomc_mult, fomc_event_vol = strip_event_vol(
        IV_QUIET_1M, DAYS_QUIET_1M, IV_SPANNING_FOMC, DAYS_SPANNING_FOMC, N_EVENT_DAYS_FOMC
    )
    print(f"\n FOMC window IV (Sept 15-16): {IV_SPANNING_FOMC:.2f}% over {DAYS_SPANNING_FOMC}d")
    print(f"   -> implied FOMC event-day vol multiple : {fomc_mult:.2f}x a quiet day")
    print(f"   -> implied FOMC event-day annualised vol (illustrative): {fomc_event_vol:.1f}%")

    # Rebuild a fair IV for the note's actual ~2-month structure, which spans BOTH events
    days_total = (EVENTS["FOMC decision (day 2)"] - TODAY).days + 5  # a few days past FOMC to settle
    var_quiet_daily = (IV_QUIET_1M / 100) ** 2 / 365
    rbi_event_daily_var = (rbi_event_vol / 100) ** 2 / 365
    fomc_event_daily_var = (fomc_event_vol / 100) ** 2 / 365
    event_day_variances = [rbi_event_daily_var] + [fomc_event_daily_var] * N_EVENT_DAYS_FOMC

    blended_iv = blended_iv_for_note_tenor(IV_QUIET_1M, days_total, event_day_variances)

    print("-" * 66)
    print(f" Blended fair ATM IV for the note's ~{days_total}-day structure")
    print(f" (spans BOTH the RBI and FOMC decisions): {blended_iv:.2f}%")
    print(f" vs. the flat {'6-7%'} assumption used in the main note's illustrative")
    print(" call-spread premium -- this gives that assumption an explicit,")
    print(" event-aware derivation instead of a single guessed number.")
    print("=" * 66)
    print("\nNext step for the bigger IV Surface & Event-Vol Tracker project:")
    print(" replace IV_QUIET_1M / IV_SPANNING_* with real CCIL/broker ATM IV")
    print(" quotes and this same stripping function generalises directly to")
    print(" Nifty event windows (RBI, FOMC, Union Budget, earnings).")


if __name__ == "__main__":
    main()
