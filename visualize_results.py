"""
Visualise the REAL MetaTrader 5 backtest findings.

These numbers are NOT from the synthetic generator. They are the actual results
of the mean-reversion strategy (long-only) backtested in MetaTrader 5 on real
tick data (History Quality 100%). The purpose of this script is to turn those
empirical findings into clear figures for the report.

Source: MT5 Strategy Tester, EURUSD/USDCHF/USDCAD M15, "Every tick based on
real ticks", initial deposit 10,000.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

RESULTS_DIR = Path(".")
RESULTS_DIR.mkdir(exist_ok=True)

# --- REAL MT5 results: same strategy & parameters, different instruments (2020-2025) ---
CROSS_INSTRUMENT = {
    "EURUSD": 1.27,   # net +583, recovery 2.85, DD 2.01%
    "USDCHF": 0.53,   # net -314
    "USDCAD": 0.62,   # net -235
}

# --- REAL MT5 results: EURUSD only, over different time horizons ---
PERIOD_DECAY = {
    "2020-2025\n(6 years)": 1.27,   # net +583
    "2014-2025\n(12 years)": 1.07,  # net +88, recovery 0.29
}

GREEN = "#2ea043"
RED = "#cf222e"
BLUE = "#1f6feb"
GREY = "#57606a"


def plot_cross_instrument() -> Path:
    """Bar chart of profit factor by instrument, with a breakeven reference."""
    fig, ax = plt.subplots(figsize=(8, 5))
    syms = list(CROSS_INSTRUMENT)
    pfs = [CROSS_INSTRUMENT[s] for s in syms]
    colors = [GREEN if pf >= 1.0 else RED for pf in pfs]

    bars = ax.bar(syms, pfs, color=colors, width=0.55, edgecolor="black", linewidth=0.6)
    ax.axhline(1.0, color=GREY, linestyle="--", linewidth=1.2)
    ax.text(len(syms) - 0.5, 1.02, "breakeven (PF = 1.0)", color=GREY,
            ha="right", va="bottom", fontsize=9)

    for bar, pf in zip(bars, pfs):
        ax.text(bar.get_x() + bar.get_width() / 2, pf + 0.02, f"{pf:.2f}",
                ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("Profit Factor")
    ax.set_ylim(0, 1.5)
    ax.set_title("Cross-Instrument Test — same strategy, same parameters\n"
                 "Profitable on EURUSD only; loses on USDCHF & USDCAD",
                 fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = RESULTS_DIR / "cross_instrument_pf.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_period_decay() -> Path:
    """Bar chart showing the EURUSD edge weakening over a longer horizon."""
    fig, ax = plt.subplots(figsize=(7, 5))
    labels = list(PERIOD_DECAY)
    pfs = [PERIOD_DECAY[l] for l in labels]

    bars = ax.bar(labels, pfs, color=[BLUE, GREY], width=0.5,
                  edgecolor="black", linewidth=0.6)
    ax.axhline(1.0, color=RED, linestyle="--", linewidth=1.2)
    ax.text(1.4, 1.005, "breakeven", color=RED, ha="right", va="bottom", fontsize=9)

    for bar, pf in zip(bars, pfs):
        ax.text(bar.get_x() + bar.get_width() / 2, pf + 0.005, f"{pf:.2f}",
                ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("Profit Factor (EURUSD)")
    ax.set_ylim(0.9, 1.35)
    ax.set_title("Longer Horizon = Weaker Edge\n"
                 "The apparent 2020-2025 edge fades toward breakeven over 12 years",
                 fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = RESULTS_DIR / "period_decay_pf.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


if __name__ == "__main__":
    p1 = plot_cross_instrument()
    p2 = plot_period_decay()
    print(f"Saved: {p1}")
    print(f"Saved: {p2}")
