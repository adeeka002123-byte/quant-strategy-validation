# Data

This project ships with a **synthetic data generator** (`src/data.py`) so the
pipeline runs out of the box. Synthetic results are meaningless for judging the
strategy -- they only prove the code works.

## Getting real data

For genuine analysis, download historical FX data (free) and drop the CSV here:

- **HistData.com** — free M1 data back to ~2000 (`EURUSD`, `USDCHF`, `USDCAD`, ...).
  Export/convert to CSV.
- **Dukascopy** — tick/minute data since ~2003, via the free **Tickstory** tool.

### Expected CSV format

Case-insensitive columns: `datetime, open, high, low, close`

```
datetime,open,high,low,close
2020-01-02 00:00:00,1.12100,1.12130,1.12080,1.12115
...
```

### Run against real data

```bash
python run_analysis.py --data data/EURUSD_M15.csv --symbol EURUSD --direction long_only

# cross-instrument test (the honesty check):
python run_analysis.py --data data/EURUSD_M15.csv --symbol EURUSD \
    --cross USDCHF:data/USDCHF_M15.csv USDCAD:data/USDCAD_M15.csv
```
