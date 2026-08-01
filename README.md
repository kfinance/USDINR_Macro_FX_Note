# USDINR_Macro_FX_Note
Testing this properly, building on my NISM Series I (Currency Derivatives) prep: is the USD/INR forward market pricing depreciation fairly, or paying a premium for it?
The framework — Covered Interest Rate Parity. India's repo rate (5.25%) vs. Fed funds (3.625%) implies a ~1.6% fair forward premium. The market is actually pricing ~3.0%. That's a real, persistent gap.
 
So I backtested whether the rate differential itself predicts rupee moves — 26 quarters of RBI/Fed rate history against subsequent USD/INR returns. R² ≈ 0.01. Essentially no relationship.
 
That's not a null result — it's the finding. If the differential barely predicts anything historically, the ~1.4pp gap isn't mispricing to fade blindly — it's the market paying a genuine risk premium for FPI-flow volatility and oil/geopolitical risk that a simple carry model was never going to capture.
 
From there: built a defined-risk call spread around the Aug 5 RBI and Sept FOMC decisions, ran an event-vol stripping model to size the IV bump around each, and Monte Carlo'd the scenario tree into an actual expected P&L (+0.05/USD, capped downside) instead of eyeballing it.
