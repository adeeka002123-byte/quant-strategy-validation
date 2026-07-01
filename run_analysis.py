"""
Main entry point: run the full mean-reversion validation study.

Usage:
    python run_analysis.py                 # uses synthetic data (demo)
    python run_analysis.py --data eurusd.csv --symbol EURUSD

The script:
  1. loads data (synthetic by default, real CSV if provided)
  2. runs a baseline backtest and prints headline metrics
  3. runs in-sample / out-of-sample split
  4. runs walk-forward analysis
  5. (if extra CSVs given) runs a cross-instrument test
  6. saves an equity-curve chart to results/
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from backtest import BacktestConfig, run_backtest
from data import generate_ohlc, load_ohlc_csv
from indicators import add_all_indicators
from metrics import compute_metrics
from strategy import StrategyConfig, generate_signals
from validation import cross_instrument, in_sample_out_of_sample, walk_forward

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mean-reversion strategy validation study")
    parser.add_argument("--data", type=str, default=None, help="Path to OHLC CSV (optional)")
    parser.add_argument("--symbol", type=str, default="SYNTHETIC", help="Symbol label")
    parser.add_argument("--direction", type=str, default="both",
                        choices=["both", "long_only", "short_only"])
    parser.add_argument("--cross", nargs="*", default=[],
                        help="Extra 'SYMBOL:path.csv' pairs for cross-instrument test")
    args = parser.parse_args()

    results_dir = Path(".")
    results_dir.mkdir(exist_ok=True)

    scfg = StrategyConfig(direction=args.direction)
    bcfg = BacktestConfig()

    # ---- 1. load data ----
    if args.data:
        ohlc = load_ohlc_csv(args.data)
        print(f"Loaded {len(ohlc):,} bars of REAL data for {args.symbol}")
    else:
        ohlc = generate_ohlc()
        print(f"Loaded {len(ohlc):,} bars of SYNTHETIC data "
              f"(demo only -- results are not meaningful; see data/README.md)")

    # ---- 2. baseline backtest ----
    df = add_all_indicators(ohlc)
    signals = generate_signals(df, scfg)
    result = run_backtest(df, signals, bcfg)
    metrics = compute_metrics(result.trades, result.equity_curve, bcfg.initial_equity)

    print("\n" + "=" * 60)
    print(f"BASELINE  |  {args.symbol}  |  direction={args.direction}")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k:<20} {v}")

    # ---- 3. in-sample / out-of-sample ----
    print("\n" + "=" * 60)
    print("IN-SAMPLE vs OUT-OF-SAMPLE (60/40 chronological split)")
    print("=" * 60)
    print(in_sample_out_of_sample(ohlc, scfg, bcfg)[
        ["n_trades", "return_pct", "profit_factor", "max_drawdown_pct", "recovery_factor"]
    ])

    # ---- 4. walk-forward ----
    print("\n" + "=" * 60)
    print("WALK-FORWARD (6 consecutive windows)")
    print("=" * 60)
    wf = walk_forward(ohlc, scfg, bcfg, n_windows=6)
    print(wf[["n_trades", "return_pct", "profit_factor", "max_drawdown_pct"]])

    # ---- 5. cross-instrument (optional) ----
    if args.cross:
        data = {args.symbol: ohlc}
        for pair in args.cross:
            sym, path = pair.split(":")
            data[sym] = load_ohlc_csv(path)
        print("\n" + "=" * 60)
        print("CROSS-INSTRUMENT (same params, different symbols)")
        print("=" * 60)
        ci = cross_instrument(data, scfg, bcfg)
        print(ci[["n_trades", "return_pct", "profit_factor", "recovery_factor"]])

    # ---- 6. equity-curve chart ----
    if not result.equity_curve.empty:
        plt.figure(figsize=(11, 5))
        result.equity_curve.plot(color="#1f6feb", linewidth=1.4)
        plt.title(f"Equity Curve -- {args.symbol} (mean-reversion, {args.direction})")
        plt.ylabel("Equity")
        plt.xlabel("Time")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        out_path = results_dir / f"equity_{args.symbol}_{args.direction}.png"
        plt.savefig(out_path, dpi=130)
        print(f"\nSaved equity curve -> {out_path}")


if __name__ == "__main__":
    main()
