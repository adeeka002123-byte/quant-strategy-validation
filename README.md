# Quant Strategy Validation — Detecting Overfitting in a Trading Strategy

> A rigorous, honest study of a mean-reversion trading strategy in Python.
> The headline result is not "I found a profitable strategy" — it is
> **"I built the validation framework that proved the strategy was overfit."**

Most trading-strategy projects report a beautiful backtest and stop there.
This project does the opposite: it treats a strategy as a **hypothesis to be
falsified**, and builds the machinery to test whether an apparent edge survives
data it was never fitted to. Spoiler: it does not — and demonstrating *how you
detect that* is the point.

---

## Why this project exists

Anyone can tune a strategy until its backtest points up. The genuinely hard
question in quantitative finance is **generalisation**: does the edge hold
out-of-sample, across time, and across instruments? Or is it just a pattern the
past happened to contain that the future will not repeat?

This mirrors the core problem in machine learning — the gap between training
performance and real-world performance. The discipline is identical: honest
out-of-sample evaluation, and the willingness to reject your own model when the
evidence says so.

## The strategy under test

A classic **mean-reversion** system on FX:

- **Entry:** price closes outside a Bollinger Band **and** RSI is at an extreme
  (oversold → long, overbought → short)
- **Regime filter:** only trade when **ADX is low** (ranging market) — because
  mean-reversion is destroyed by strong trends ("catching a falling knife")
- **Exit:** take-profit at the mean (Bollinger mid), ATR-based stop-loss, and a
  time-based exit (mean-reversion edges decay with holding time)
- **Risk:** fixed-fractional position sizing from the stop distance, plus a
  spread cost on every entry (ignoring costs is the #1 way backtests lie)

## The validation framework (the actual contribution)

Three independent tests, in `validation.py`:

| Test | Question it answers |
|------|---------------------|
| **In-sample / out-of-sample split** | Does the edge hold on unseen *later* data? |
| **Walk-forward analysis** | Is performance *stable* across rolling time windows? |
| **Cross-instrument test** | Is the edge a real market property, or did we fit *one symbol*? |

## Findings (real data — honest)

The strategy was backtested in **MetaTrader 5 on real tick data (History
Quality 100%)**. Full breakdown in [`RESULTS.md`](RESULTS.md).

**Step 1 — EURUSD 2020–2025 looks strong (the trap):**

| Metric | Value |
|--------|-------|
| Net Profit | +582.97 (+5.83%) |
| Profit Factor | **1.27** |
| Recovery Factor | 2.85 |
| Sharpe Ratio | 5.59 |
| Max Drawdown | 2.01% |
| Trades / Win Rate | 197 / 42.13% |

Positive expectancy, low drawdown. In isolation this looks deployable — which
is exactly why a single-instrument backtest is not enough.

**Step 2 — Cross-instrument test is decisive:** the *same strategy, same
parameters* on other pairs:

| Instrument | Net | Profit Factor |
|-----------|----:|--------------:|
| EURUSD | +583 | **1.27** ✅ |
| USDCHF | −314 | **0.53** ❌ |
| USDCAD | −235 | **0.62** ❌ |

![Cross-instrument profit factor](cross_instrument_pf.png)

**Step 3 — Longer horizon confirms decay:** extending EURUSD to 12 years
(2014–2025) collapses the profit factor from 1.27 to **1.07** (near breakeven).

![Period decay](period_decay_pf.png)

**Conclusion:** the edge is specific to one instrument in one regime. It does
not generalise across instruments or survive a longer horizon, so the correct
decision is to **reject the strategy**. The value delivered is the framework and
the discipline to act on it — exactly the judgement that separates a usable
model from a dangerous one.

## What this project demonstrates

- **Data engineering** — indicators built from scratch in pandas, OHLC handling
- **Software engineering** — modular design, typed dataclasses, docstrings,
  clear separation of concerns (indicators / strategy / backtest / metrics / validation)
- **Statistical rigour** — out-of-sample and walk-forward evaluation, awareness
  of look-ahead bias and transaction costs
- **Intellectual honesty** — rejecting a strategy because the evidence demands it

## Tech stack

`Python` · `pandas` · `numpy` · `matplotlib`

## Run it

```bash
pip install -r requirements.txt

# runs on synthetic data out of the box (proves the pipeline works)
python run_analysis.py

# regenerate the result charts
python visualize_results.py

# with real data (see "Data" section below)
python run_analysis.py --data EURUSD_M15.csv --symbol EURUSD --direction long_only

# the honesty check — same params across instruments
python run_analysis.py --data EURUSD_M15.csv --symbol EURUSD \
    --cross USDCHF:USDCHF_M15.csv USDCAD:USDCAD_M15.csv
```

## Project structure

```
quant-strategy-validation/
├── README.md
├── RESULTS.md              # full real MT5 empirical findings
├── requirements.txt
├── run_analysis.py         # entry point: baseline + all validation tests
├── visualize_results.py    # renders the real MT5 findings as charts
├── indicators.py           # Bollinger, RSI, ADX, ATR (from scratch)
├── strategy.py             # mean-reversion signal logic
├── backtest.py             # event-driven engine (SL/TP/time-exit, costs)
├── metrics.py              # PF, Sharpe, drawdown, recovery, expectancy
├── validation.py           # IS/OOS split, walk-forward, cross-instrument
├── data.py                 # synthetic generator + real-CSV loader
├── cross_instrument_pf.png
└── period_decay_pf.png
```

## Data

The **headline results** (`RESULTS.md`) come from **MetaTrader 5 on real tick
data** — this is the actual empirical study. The **Python code** reimplements
the same validation methodology so it is transparent and runnable; it ships
with a synthetic data generator (`data.py`) purely so the pipeline runs out of
the box (synthetic numbers are not a real evaluation).

To reproduce on genuine data, download historical FX data (free) and save the
CSV in the project folder:

- **HistData.com** — free M1 data back to ~2000 (`EURUSD`, `USDCHF`, `USDCAD`, ...)
- **Dukascopy** — tick/minute data since ~2003, via the free **Tickstory** tool

Expected CSV columns (case-insensitive): `datetime, open, high, low, close`.

---

*Built as a study in honest quantitative research. If a strategy can't survive
out-of-sample and cross-instrument testing, it isn't an edge — and knowing that
is worth more than any backtest.*
