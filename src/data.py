"""
Generate synthetic OHLC data so the project runs out of the box.

IMPORTANT: this synthetic data exists ONLY so the pipeline is runnable
without downloading anything. Results on synthetic data are meaningless for
evaluating the strategy -- they only prove the code works. For real analysis,
replace this with genuine historical data (see data/README.md).

The generator blends a random walk with mild mean-reversion and regime
switches, so the strategy actually produces trades to demonstrate the metrics
and validation machinery.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_ohlc(
    n_bars: int = 40_000,
    start: str = "2020-01-01",
    freq: str = "15min",
    seed: int = 42,
    start_price: float = 1.10,
) -> pd.DataFrame:
    """Return a synthetic OHLC DataFrame with columns open/high/low/close."""
    rng = np.random.default_rng(seed)

    # Alternate between ranging and trending regimes.
    regime_len = 2_000
    n_regimes = n_bars // regime_len + 1
    regimes = rng.choice(["range", "trend"], size=n_regimes, p=[0.6, 0.4])

    prices = np.empty(n_bars)
    prices[0] = start_price
    mean_level = start_price

    for i in range(1, n_bars):
        regime = regimes[i // regime_len]
        noise = rng.normal(0, 0.0006)
        if regime == "range":
            # pull back toward a slowly drifting mean
            mean_level += rng.normal(0, 0.00002)
            pull = 0.02 * (mean_level - prices[i - 1])
            prices[i] = prices[i - 1] + pull + noise
        else:
            # persistent drift
            drift = 0.00008 * (1 if (i // regime_len) % 2 == 0 else -1)
            prices[i] = prices[i - 1] + drift + noise
            mean_level = prices[i]

    close = pd.Series(prices)
    # Build OHLC around the close path
    spread = rng.uniform(0.0002, 0.0009, n_bars)
    high = close + spread * rng.uniform(0.3, 1.0, n_bars)
    low = close - spread * rng.uniform(0.3, 1.0, n_bars)
    open_ = close.shift(1).fillna(close.iloc[0])

    idx = pd.date_range(start=start, periods=n_bars, freq=freq)
    df = pd.DataFrame(
        {"open": open_.to_numpy(), "high": high, "low": low, "close": close.to_numpy()},
        index=idx,
    )
    # ensure OHLC integrity
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


def load_ohlc_csv(path: str) -> pd.DataFrame:
    """Load real OHLC data from CSV.

    Expected columns (case-insensitive): datetime, open, high, low, close.
    This is what you use once you have real data from HistData / Dukascopy.
    """
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    dt_col = next(c for c in df.columns if c in ("datetime", "date", "time", "timestamp"))
    df[dt_col] = pd.to_datetime(df[dt_col])
    df = df.set_index(dt_col).sort_index()
    return df[["open", "high", "low", "close"]]
