"""
Technical indicators implemented from scratch in pandas.

Implementing these manually (instead of importing TA-Lib) is intentional:
it demonstrates understanding of what each indicator actually computes,
and keeps the project dependency-light and fully transparent.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def bollinger_bands(
    close: pd.Series, period: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """Bollinger Bands: a moving average with volatility-scaled envelopes.

    Returns a DataFrame with columns: bb_mid, bb_upper, bb_lower.
    """
    mid = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    return pd.DataFrame(
        {
            "bb_mid": mid,
            "bb_upper": mid + num_std * std,
            "bb_lower": mid - num_std * std,
        }
    )


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder's smoothing == EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100 - (100 / (1 + rs))
    # When avg_loss is 0 the market only went up -> RSI 100
    out[avg_loss == 0] = 100.0
    return out.rename("rsi")


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (Wilder), a volatility measure in price units."""
    prev_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().rename("atr")


def adx(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """Average Directional Index: trend-strength (not direction), 0-100.

    Low ADX ~ ranging market; high ADX ~ strong trend. Used here as a
    regime filter (mean-reversion is only expected to work when ADX is low).
    """
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    atr_ = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().rename("adx")


def add_all_indicators(
    df: pd.DataFrame,
    bb_period: int = 20,
    bb_std: float = 2.0,
    rsi_period: int = 14,
    adx_period: int = 14,
    atr_period: int = 14,
) -> pd.DataFrame:
    """Attach every indicator the strategy needs to an OHLC DataFrame."""
    out = df.copy()
    bb = bollinger_bands(out["close"], bb_period, bb_std)
    out = out.join(bb)
    out["rsi"] = rsi(out["close"], rsi_period)
    out["adx"] = adx(out["high"], out["low"], out["close"], adx_period)
    out["atr"] = atr(out["high"], out["low"], out["close"], atr_period)
    return out
