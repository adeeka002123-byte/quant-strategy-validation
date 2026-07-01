"""
Validation -- the heart of this project.

Anyone can produce a good-looking backtest on one dataset by tuning until the
curve points up. The hard, honest question is: does the edge SURVIVE data the
strategy was never fitted to? These functions answer that three ways:

  1. In-sample / out-of-sample split  -> does it hold on unseen later data?
  2. Walk-forward analysis            -> is it stable across rolling windows?
  3. Cross-instrument test            -> is the edge a real market property,
                                          or did we accidentally fit one symbol?

A strategy that only looks good in-sample, on one instrument, is not an edge.
It is a story the past told us that the future will not repeat.
"""
from __future__ import annotations

import pandas as pd

from .backtest import BacktestConfig, run_backtest
from .indicators import add_all_indicators
from .metrics import compute_metrics
from .strategy import StrategyConfig, generate_signals


def _run_once(df_ohlc: pd.DataFrame, scfg: StrategyConfig, bcfg: BacktestConfig) -> dict:
    """Indicators -> signals -> backtest -> metrics, for one slice of data."""
    df = add_all_indicators(df_ohlc)
    signals = generate_signals(df, scfg)
    res = run_backtest(df, signals, bcfg)
    return compute_metrics(res.trades, res.equity_curve, bcfg.initial_equity)


def in_sample_out_of_sample(
    df_ohlc: pd.DataFrame,
    scfg: StrategyConfig,
    bcfg: BacktestConfig,
    split: float = 0.6,
) -> pd.DataFrame:
    """Split chronologically; report metrics for both halves side by side."""
    cut = int(len(df_ohlc) * split)
    is_metrics = _run_once(df_ohlc.iloc[:cut], scfg, bcfg)
    oos_metrics = _run_once(df_ohlc.iloc[cut:], scfg, bcfg)
    return pd.DataFrame({"in_sample": is_metrics, "out_of_sample": oos_metrics}).T


def walk_forward(
    df_ohlc: pd.DataFrame,
    scfg: StrategyConfig,
    bcfg: BacktestConfig,
    n_windows: int = 6,
) -> pd.DataFrame:
    """Split the data into N consecutive windows and evaluate each separately.

    Consistency across windows is the signal we want; one blow-up window
    matters far more than one great one.
    """
    size = len(df_ohlc) // n_windows
    rows = {}
    for w in range(n_windows):
        start = w * size
        end = len(df_ohlc) if w == n_windows - 1 else (w + 1) * size
        window = df_ohlc.iloc[start:end]
        label = f"{window.index[0].date()}__{window.index[-1].date()}"
        rows[label] = _run_once(window, scfg, bcfg)
    return pd.DataFrame(rows).T


def cross_instrument(
    data: dict[str, pd.DataFrame],
    scfg: StrategyConfig,
    bcfg: BacktestConfig,
) -> pd.DataFrame:
    """Run the SAME strategy/params on several instruments.

    `data` maps symbol -> OHLC DataFrame. If the edge only appears on the
    instrument it was designed on, it is overfit to that symbol.
    """
    rows = {sym: _run_once(df, scfg, bcfg) for sym, df in data.items()}
    return pd.DataFrame(rows).T
