"""
Event-driven backtest engine.

Deliberately written as a readable bar-by-bar loop rather than a clever
vectorised one. For a research/portfolio project, correctness and clarity
matter more than micro-optimisation, and an explicit loop makes the
exit logic (stop-loss vs take-profit vs time-exit) auditable.

Key design choices (each one guards against a common backtesting mistake):
  * Signals come from closed bars; entry is at the NEXT bar's open -> no look-ahead.
  * Exits are checked intrabar using the bar's high/low.
  * If both SL and TP could be hit within the same bar, we assume the worse
    case (SL first) -> conservative, avoids over-optimistic results.
  * Position size is derived from a fixed % risk of equity and the SL distance
    -> mirrors real risk management, keeps drawdowns comparable across assets.
  * A configurable spread cost is applied on entry -> avoids the classic
    "profitable in backtest, dead live" trap where costs are ignored.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    initial_equity: float = 10_000.0
    risk_perc: float = 0.5          # % of equity risked per trade
    sl_atr_mult: float = 1.5        # stop-loss distance = ATR * this
    tp_at_mean: bool = True         # take profit at Bollinger mid (the "mean")
    tp_atr_mult: float = 2.0        # used only if tp_at_mean is False
    max_hold_bars: int = 24         # time-exit: close if held longer than this
    spread: float = 0.0001          # round-trip cost applied on entry (price units)
    contract_value: float = 100_000.0  # 1 lot notional (FX standard)


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    config: BacktestConfig = field(repr=False)


def run_backtest(df: pd.DataFrame, signals: pd.Series, cfg: BacktestConfig) -> BacktestResult:
    """Simulate the strategy bar by bar and return equity curve + trade log."""
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    low = df["low"].to_numpy()
    mid = df["bb_mid"].to_numpy()
    atr = df["atr"].to_numpy()
    idx = df.index
    sig = signals.to_numpy()

    equity = cfg.initial_equity
    equity_points: list[tuple] = []
    trades: list[dict] = []

    in_pos = False
    direction = 0
    entry_price = sl = tp = 0.0
    size = 0.0
    entry_i = 0

    n = len(df)
    for i in range(1, n):
        # ---- manage an open position against bar i ----
        if in_pos:
            exit_price = None
            reason = None

            if direction == 1:  # long
                if low[i] <= sl:
                    exit_price, reason = sl, "stop_loss"      # worse case first
                elif h[i] >= tp:
                    exit_price, reason = tp, "take_profit"
            else:  # short
                if h[i] >= sl:
                    exit_price, reason = sl, "stop_loss"
                elif low[i] <= tp:
                    exit_price, reason = tp, "take_profit"

            if exit_price is None and (i - entry_i) >= cfg.max_hold_bars:
                exit_price, reason = o[i], "time_exit"

            if exit_price is not None:
                pnl = direction * (exit_price - entry_price) * size * cfg.contract_value
                equity += pnl
                trades.append(
                    {
                        "entry_time": idx[entry_i],
                        "exit_time": idx[i],
                        "direction": "long" if direction == 1 else "short",
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "reason": reason,
                        "bars_held": i - entry_i,
                        "equity_after": equity,
                    }
                )
                in_pos = False
                equity_points.append((idx[i], equity))

        # ---- look for a new entry (signal on bar i-1, enter at bar i open) ----
        if not in_pos and sig[i - 1] != 0 and not np.isnan(atr[i - 1]):
            direction = int(sig[i - 1])
            sl_dist = atr[i - 1] * cfg.sl_atr_mult
            if sl_dist <= 0:
                continue

            if direction == 1:
                entry_price = o[i] + cfg.spread / 2
                sl = entry_price - sl_dist
                tp = mid[i - 1] if cfg.tp_at_mean else entry_price + atr[i - 1] * cfg.tp_atr_mult
                if tp <= entry_price:  # skip degenerate targets
                    continue
            else:
                entry_price = o[i] - cfg.spread / 2
                sl = entry_price + sl_dist
                tp = mid[i - 1] if cfg.tp_at_mean else entry_price - atr[i - 1] * cfg.tp_atr_mult
                if tp >= entry_price:
                    continue

            # position size from fixed-fractional risk
            risk_amount = equity * cfg.risk_perc / 100.0
            loss_per_unit = sl_dist * cfg.contract_value
            size = risk_amount / loss_per_unit
            entry_i = i
            in_pos = True

    equity_curve = pd.Series(
        dict(equity_points), name="equity"
    ) if equity_points else pd.Series([cfg.initial_equity], index=[idx[0]], name="equity")
    equity_curve = equity_curve.sort_index()

    trades_df = pd.DataFrame(trades)
    return BacktestResult(equity_curve=equity_curve, trades=trades_df, config=cfg)
