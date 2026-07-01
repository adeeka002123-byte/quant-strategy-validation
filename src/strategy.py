"""
Mean-reversion signal generation.

Thesis: when price stretches far from its moving average (outside the
Bollinger band) AND momentum is extreme (RSI), price tends to revert to the
mean -- BUT only in ranging markets. In strong trends, mean-reversion gets
run over ("catching a falling knife"), so we gate every signal behind a
low-ADX regime filter.

Signals are generated on CLOSED bars only. The backtester enters on the NEXT
bar's open to avoid look-ahead bias.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class StrategyConfig:
    """All tunable knobs for the mean-reversion strategy."""

    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    adx_max: float = 25.0          # regime filter: only trade when ADX < this
    direction: str = "both"        # "both" | "long_only" | "short_only"


def generate_signals(df: pd.DataFrame, cfg: StrategyConfig) -> pd.Series:
    """Return a Series of {+1 long, -1 short, 0 flat} aligned to df.index.

    A signal on bar t means: the entry order is placed for bar t+1's open.
    """
    ranging = df["adx"] < cfg.adx_max

    long_ok = cfg.direction in ("both", "long_only")
    short_ok = cfg.direction in ("both", "short_only")

    long_signal = (
        long_ok
        & ranging
        & (df["close"] < df["bb_lower"])
        & (df["rsi"] < cfg.rsi_oversold)
    )
    short_signal = (
        short_ok
        & ranging
        & (df["close"] > df["bb_upper"])
        & (df["rsi"] > cfg.rsi_overbought)
    )

    signal = pd.Series(0, index=df.index, dtype=int)
    signal[long_signal] = 1
    signal[short_signal] = -1
    return signal
