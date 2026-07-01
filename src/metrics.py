"""
Performance metrics.

These are the numbers that decide whether a strategy has an edge. The point
of this project is NOT to maximise them on one dataset (that is how you
overfit) but to see whether they SURVIVE out-of-sample and across assets.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    """Largest peak-to-trough drop of the equity curve, as a fraction (0-1)."""
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    return float(-drawdown.min())


def compute_metrics(trades: pd.DataFrame, equity: pd.Series, initial_equity: float) -> dict:
    """Return the standard battery of strategy quality metrics."""
    if trades.empty:
        return {
            "n_trades": 0,
            "net_profit": 0.0,
            "return_pct": 0.0,
            "profit_factor": np.nan,
            "win_rate": np.nan,
            "avg_win": np.nan,
            "avg_loss": np.nan,
            "expectancy": np.nan,
            "max_drawdown_pct": 0.0,
            "recovery_factor": np.nan,
            "sharpe_per_trade": np.nan,
        }

    pnl = trades["pnl"]
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    gross_profit = wins.sum()
    gross_loss = -losses.sum()
    net_profit = pnl.sum()
    mdd = max_drawdown(equity)

    return {
        "n_trades": int(len(trades)),
        "net_profit": round(float(net_profit), 2),
        "return_pct": round(float(net_profit / initial_equity * 100), 2),
        "profit_factor": round(float(gross_profit / gross_loss), 3) if gross_loss > 0 else np.inf,
        "win_rate": round(float(len(wins) / len(pnl) * 100), 2),
        "avg_win": round(float(wins.mean()), 2) if len(wins) else 0.0,
        "avg_loss": round(float(losses.mean()), 2) if len(losses) else 0.0,
        "expectancy": round(float(pnl.mean()), 2),
        "max_drawdown_pct": round(float(mdd * 100), 2),
        "recovery_factor": round(float(net_profit / (mdd * initial_equity)), 2)
        if mdd > 0 else np.inf,
        "sharpe_per_trade": round(float(pnl.mean() / pnl.std(ddof=0)), 3)
        if pnl.std(ddof=0) > 0 else np.nan,
    }


def metrics_table(results: dict[str, dict]) -> pd.DataFrame:
    """Turn {label: metrics_dict} into a comparison DataFrame for reporting."""
    return pd.DataFrame(results).T
