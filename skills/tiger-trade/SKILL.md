---
name: tiger-trade
description: Tiger Trade automation tool. Executes buy, sell, market orders, and limit orders via relative coordinate-based automation. Use when the user mentions "Tiger Trade", "automated trading", or "auto buy/sell stocks".
---

# Tiger Trade Automated Trading

> ⚠️ **Live trading requires unlocking first.** Before executing any real trades, make sure the trading function is unlocked in Tiger Trade. Trading with locked accounts is not supported.

## Command Format

```bash
python scripts/trade.py --code <stock_code> --action <buy|sell> --order_type <market|limit> --price <price> --quantity <quantity>
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--code` | ✅ | Stock code, e.g. `AAPL` |
| `--action` | ✅ | `buy` or `sell` |
| `--order_type` | ✅ | `market` (market order) or `limit` (limit order) |
| `--price` | Required for limit orders | Limit order price |
| `--quantity` | ✅ | Number of shares |

## Usage Examples

**Market buy:**
```bash
python scripts/trade.py --code AAPL --action buy --order_type market --quantity 100
```

**Limit buy:**
```bash
python scripts/trade.py --code AAPL --action buy --order_type limit --price 180 --quantity 100
```

**Market sell:**
```bash
python scripts/trade.py --code AAPL --action sell --order_type market --quantity 100
```

**Limit sell:**
```bash
python scripts/trade.py --code AAPL --action sell --order_type limit --price 185 --quantity 100
```

## Prerequisites

1. **Install dependencies**: `pip install pyautogui pywin32 numpy`
2. Tiger Trade window is open and on the trading interface

## Notes

1. Do not move the mouse or switch windows during trading operations
2. Limit orders must specify `--price`; market orders do not require a price
3. Recommended to test first with paper trading
4. **Only one script at a time**: Do not run multiple trade.py scripts simultaneously. You must wait for the current script to finish (success or failure) before starting the next one. Running a new script while a previous one is still executing may cause order conflicts or window state issues.
