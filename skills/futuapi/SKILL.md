OpenD GUI first (click "Unlock Trading" in the menu or interface), then re-run the order.

### Modify Order
When the user asks about "modify order", "change order", "change price", or "change quantity":
```bash
python skills/futuapi/scripts/trade/modify_order.py --order-id 12345678 [--price 410] [--quantity 200] [--market HK] [--trd-env SIMULATE] [--acc-id 12345] [--security-firm FUTUSECURITIES] [--json]
```
- `--order-id`: Order ID (required)
- `--price`: New price (optional, keeps original if not provided)
- `--quantity`: New total quantity, not incremental (optional, keeps original if not provided)
- At least `--price` or `--quantity` must be provided
- Missing parameters are automatically filled from the original order (e.g. if only changing price, quantity is automatically taken from the original order)
- Order modification is not supported for Stock Connect (A-share) markets
- If the user doesn't provide an order ID, first use `get_orders.py` to query

### Cancel Order
When the user asks about "cancel order" or "withdraw order":
```bash
python skills/futuapi/scripts/trade/cancel_order.py --order-id 12345678 [--acc-id 12345] [--market HK] [--trd-env SIMULATE] [--security-firm FUTUSECURITIES] [--json]
```
- If the user doesn't provide an order ID, first use `get_orders.py` to query

### Query Today's Orders
When the user asks about "orders" or "my orders":
```bash
python skills/futuapi/scripts/trade/get_orders.py [--market HK] [--trd-env SIMULATE] [--acc-id 12345] [--security-firm FUTUSECURITIES] [--json]
```

### Query Historical Orders
When the user asks about "historical orders" or "past orders":
```bash
python skills/futuapi/scripts/trade/get_history_orders.py [--acc-id 12345] [--market HK] [--trd-env SIMULATE] [--start 2026-01-01] [--end 2026-03-01] [--code US.AAPL] [--status FILLED_ALL CANCELLED_ALL] [--limit 200] [--security-firm FUTUSECURITIES] [--json]
```

---

## Futures Trading Commands

Futures trading must use **`OpenFutureTradeContext`** (not `OpenSecTradeContext` used by the existing trading scripts). The existing trading scripts (`place_order.py` etc.) use `OpenSecTradeContext` and are **not suitable for futures**. Futures trading requires generating Python code directly.

### Key Differences: Futures vs Securities

| Feature | Securities Trading | Futures Trading |
|---------|-------------------|-----------------|
| Context | `OpenSecTradeContext` | `OpenFutureTradeContext` |
| Existing Scripts | Available via `place_order.py` etc. | Not available — generate code |
| Simulated Accounts | Unified by market | Assigned per market (e.g. `FUTURES_SIMULATE_SG`) |
| Contract Code | Stock code (e.g. `HK.00700`) | Futures main contract code (e.g. `SG.CNmain`) — automatically mapped to actual monthly contract when placing orders |
| Quantity Unit | Shares | Lots |

### SG Futures Contract Codes

Common SG futures main contract codes (use the "main contract" code when placing orders — the system automatically maps to the current month's contract):

| Code | Name | Per Lot |
|------|------|---------|
| `SG.CNmain` | A50 Index Futures Main | 1 |
| `SG.NKmain` | Nikkei Futures Main | 500 |
| `SG.FEFmain` | Iron Ore Futures Main | 100 |
| `SG.SGPmain` | MSCI Singapore Index Futures Main | 100 |
| `SG.TWNmain` | FTSE Taiwan Index Futures Main | 40 |

Query all SG futures contracts:
```python
from futu import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = quote_ctx.get_stock_basicinfo(Market.SG, SecurityType.FUTURE)
# Filter main contracts
main_contracts = data[data['main_contract'] == True]
print(main_contracts[['code', 'name', 'lot_size']].to_string())
quote_ctx.close()
```

### Query Futures Accounts

Futures accounts are queried via `OpenFutureTradeContext`, managed separately from securities accounts:

```python
from futu import *
trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111)
ret, data = trd_ctx.get_acc_list()
print(data.to_string())
trd_ctx.close()
```

Futures simulated accounts are assigned per market; pay attention to the `trdmarket_auth` field:
- `FUTURES_SIMULATE_SG`: SG futures simulation
- `FUTURES_SIMULATE_HK`: HK futures simulation
- `FUTURES_SIMULATE_US`: US futures simulation
- `FUTURES_SIMULATE_JP`: JP futures simulation
- `FUTURES`: Live futures

### Futures Simulated Trading Flow

For simulated trading (`TrdEnv.SIMULATE`):

1. Use `OpenFutureTradeContext` to query accounts, find the one whose `trdmarket_auth` includes the corresponding simulated market (e.g. `FUTURES_SIMULATE_SG`)
2. Get contract quotes to confirm the price
3. Use AskUserQuestion to confirm order parameters (contract, direction, quantity, price)
4. Place the order

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111)

ret, data = trd_ctx.place_order(
    price=14782.0,         # Limit price
    qty=1,                 # Quantity (lots)
    code='SG.CNmain',      # Main contract code — automatically maps to actual contract
    trd_side=TrdSide.BUY,
    order_type=OrderType.NORMAL,
    trd_env=TrdEnv.SIMULATE,
    acc_id=9492210         # Simulated account ID
)

if ret == RET_OK:
    print('Order placed:', data)
else:
    print('Order failed:', data)

trd_ctx.close()
```

### Futures Live Trading Flow

Follow the same confirmation steps as "Live Order Flow" above (query account → second confirmation → execute), with the differences:
- Use `OpenFutureTradeContext` instead of `OpenSecTradeContext`
- Filter accounts whose `trdmarket_auth` includes `FUTURES`
- Change the confirmation prompt to "Confirm live futures order?"

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111)

# Live order
ret, data = trd_ctx.place_order(
    price=14785.0,
    qty=1,
    code='SG.CNmain',
    trd_side=TrdSide.BUY,
    order_type=OrderType.NORMAL,
    trd_env=TrdEnv.REAL,
    acc_id=281756475296104250  # Live futures account ID
)

if ret == RET_OK:
    print('Live order placed:', data)
else:
    print('Order failed:', data)

trd_ctx.close()
```

### Futures Positions & Funds Query

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111)

# Query positions
ret, data = trd_ctx.position_list_query(trd_env=TrdEnv.SIMULATE, acc_id=9492210)
if ret == RET_OK:
    print(data)

# Query account funds
ret, data = trd_ctx.accinfo_query(trd_env=TrdEnv.SIMULATE, acc_id=9492210)
if ret == RET_OK:
    print(data)

trd_ctx.close()
```

### Futures Order Query & Cancellation

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111)

# Query today's orders
ret, data = trd_ctx.order_list_query(trd_env=TrdEnv.SIMULATE, acc_id=9492210)
if ret == RET_OK:
    print(data)

# Cancel order
ret, data = trd_ctx.modify_order(
    modify_order_op=ModifyOrderOp.CANCEL,
    order_id='7679570',
    qty=0, price=0,
    trd_env=TrdEnv.SIMULATE,
    acc_id=9492210
)

trd_ctx.close()
```

### Futures Contract Info Query

```python
from futu import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = quote_ctx.get_future_info(['SG.CNmain', 'SG.NKmain'])
if ret == RET_OK:
    print(data)  # Contains contract multiplier, minimum tick size, trading hours, etc.
quote_ctx.close()
```

---

## Subscription Management Commands

### Subscribe to Market Data
When the user needs to subscribe to realtime data:
```bash
python skills/futuapi/scripts/subscribe/subscribe.py HK.00700 --types QUOTE ORDER_BOOK [--json]
```
- `--types`: List of subscription types (required)
- `--no-first-push`: Don't immediately push cached data
- `--push`: Enable push callbacks
- `--extended-time`: US stock pre-market/after-hours data

**Available subscription types**: QUOTE, ORDER_BOOK, TICKER, RT_DATA, BROKER, K_1M, K_5M, K_15M, K_30M, K_60M, K_DAY, K_WEEK, K_MON

### Unsubscribe
```bash
# Unsubscribe from specified subscriptions
python skills/futuapi/scripts/subscribe/unsubscribe.py HK.00700 --types QUOTE ORDER_BOOK [--json]

# Unsubscribe from all
python skills/futuapi/scripts/subscribe/unsubscribe.py --all [--json]
```
- **Note**: At least 1 minute must pass after subscribing before you can unsubscribe

### Query Subscription Status
When the user asks about "what am I subscribed to" or "subscription status":
```bash
python skills/futuapi/scripts/subscribe/query_subscription.py [--current] [--json]
```
- `--current`: Only query the current connection (default queries all connections)

---

## Push Receiver Commands

### Receive Quote Push
When the user needs realtime quote push:
```bash
python skills/futuapi/scripts/subscribe/push_quote.py HK.00700 US.AAPL --duration 60 [--json]
```
- `--duration`: Duration to receive (seconds, default 60)
- Press Ctrl+C to stop early

### Receive K-Line Push
When the user needs realtime K-line push:
```bash
python skills/futuapi/scripts/subscribe/push_kline.py HK.00700 --ktype K_1M --duration 300 [--json]
```
- `--ktype`: K_1M, K_5M, K_15M, K_30M, K_60M, K_DAY, K_WEEK, K_MON (default: K_1M)
- `--duration`: Duration to receive (seconds, default 300)

---

## Common Options

All scripts support `--json` for JSON format output, convenient for program parsing.

Most trading scripts support:
- `--market`: US, HK, HKCC, CN, SG
- `--trd-env`: REAL, SIMULATE (default: SIMULATE)
- `--acc-id`: Account ID (optional)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FUTU_OPEND_HOST` | OpenD host | 127.0.0.1 |
| `FUTU_OPEND_PORT` | OpenD port | 11111 |
| `FUTU_TRD_ENV` | Trading environment | SIMULATE |
| `FUTU_DEFAULT_MARKET` | Default market | US |
| ~~`FUTU_TRADE_PWD`~~ | ~~Trading password~~ | Removed — must be manually unlocked in OpenD GUI |
| `FUTU_ACC_ID` | Default account ID | (First account) |
| `FUTU_SECURITY_FIRM` | Broker identifier (see table below) | (Auto-detected) |

`FUTU_SECURITY_FIRM` possible values:

| Value | Region |
|-------|--------|
| `FUTUSECURITIES` | Futu Securities (HK) |
| `FUTUINC` | Futu (US) |
| `FUTUSG` | Futu (Singapore) |
| `FUTUAU` | Futu (Australia) |
| `FUTUCA` | Futu (Canada) |
| `FUTUJP` | Futu (Japan) |
| `FUTUMY` | Futu (Malaysia) |

## Broker Auto-Detection (security_firm)

When trading operations are first involved, if the environment variable `FUTU_SECURITY_FIRM` is not set, you need to determine the user's broker:

1. Run `get_accounts.py --json` to get all accounts (the script automatically iterates through all SecurityFirms)
2. Look at the `security_firm` field of accounts where `trd_env` is `REAL`
3. Use that value as the `--security-firm` parameter for all subsequent trading commands
4. If no live account is found after iterating, tell the user they may not have completed account opening, or confirm their region

Detection code example:

```python
from futu import *

FIRMS = ['FUTUSECURITIES', 'FUTUINC', 'FUTUSG', 'FUTUAU', 'FUTUCA', 'FUTUJP', 'FUTUMY']

for firm in FIRMS:
    trd_ctx = OpenSecTradeContext(
        filter_trdmarket=TrdMarket.NONE,
        host='127.0.0.1', port=11111,
        security_firm=getattr(SecurityFirm, firm)
    )
    ret, data = trd_ctx.get_acc_list()
    trd_ctx.close()
    if ret == RET_OK and not data.empty:
        real_accounts = data[data['trd_env'] == 'REAL']
        if not real_accounts.empty:
            print(f'Found live account, broker: {firm}')
            print(real_accounts.to_string())
            break
```

## API Quick Reference (Complete Function Signatures)

### Quote APIs (OpenQuoteContext)

#### Subscription Management (4)

```
subscribe(code_list, subtype_list, is_first_push=True, subscribe_push=True, is_detailed_orderbook=False, extended_time=False, session=Session.NONE)  -- Subscribe (consumes quota; 1 quota per stock per type; check quota with query_subscription before calling)
unsubscribe(code_list, subtype_list, unsubscribe_all=False)  -- Unsubscribe (at least 1 min must pass after subscribing)
unsubscribe_all()  -- Unsubscribe all
query_subscription(is_all_conn=True)  -- Query subscription status (check before calling subscribe)
```

#### Realtime Data — Requires Prior Subscription (6)

```
get_stock_quote(code_list)  -- Get realtime quotes
get_cur_kline(code, num, ktype=KLType.K_DAY, autype=AuType.QFQ)  -- Get realtime K-line
get_rt_data(code)  -- Get realtime intraday data
get_rt_ticker(code, num=500)  -- Get realtime tick data
get_order_book(code, num=10)  -- Get realtime order book
get_broker_queue(code)  -- Get realtime broker queue (HK only)
```

#### Snapshots & History (4)

```
get_market_snapshot(code_list)  -- Get snapshot (no subscription needed, max 400 per request)
request_history_kline(code, start=None, end=None, ktype=KLType.K_DAY, autype=AuType.QFQ, fields=[KL_FIELD.ALL], max_count=1000, page_req_key=None, extended_time=False, session=Session.NONE)  -- Get historical K-line (consumes historical K-line quota; check quota with get_history_kl_quota first; max 1000 per single request, use page_req_key for pagination)
get_rehab(code)  -- Get adjustment factors
get_history_kl_quota(get_detail=False)  -- Query historical K-line quota (check before calling request_history_kline)
```

#### Basic Info (5)

```
get_stock_basicinfo(market, stock_type=SecurityType.STOCK, code_list=None)  -- Get stock basic info
get_global_state()  -- Get market states for all markets (returns dict with keys including market_hk/market_us/market_sh/market_sz/market_hkfuture/market_usfuture/server_ver/qot_logined/trd_logined etc.)
request_trading_days(market=None, start=None, end=None, code=None)  -- Get trading calendar
get_market_state(code_list)  -- Get market status
get_stock_filter(market, filter_list, plate_code=None, begin=0, num=200)  -- Stock screener
```

#### Sectors (3)

```
get_plate_list(market, plate_class)  -- Get sector list
get_plate_stock(plate_code, sort_field=SortField.CODE, ascend=True)  -- Get stocks in a sector
get_owner_plate(code_list)  -- Get sectors a stock belongs to
```

#### Derivatives (5)

```
get_option_chain(code, index_option_type=IndexOptionType.NORMAL, start=None, end=None, option_type=OptionType.ALL, option_cond_type=OptionCondType.ALL, data_filter=None)  -- Get option chain
get_option_expiration_date(code, index_option_type=IndexOptionType.NORMAL)  -- Get option expiration dates
get_referencestock_list(code, reference_type)  -- Get related stocks (underlying/warrants/bull-bear certificates/options)
get_future_info(code_list)  -- Get futures contract info
get_warrant(stock_owner='', req=None)  -- Get warrants/bull-bear certificates
```

#### Capital (2)

```
get_capital_flow(stock_code, period_type=PeriodType.INTRADAY, start=None, end=None)  -- Get capital flow
get_capital_distribution(stock_code)  -- Get capital distribution
```

#### Watchlist (3)

```
get_user_security_group(group_type=UserSecurityGroupType.ALL)  -- Get watchlist groups
get_user_security(group_name)  -- Get watchlist stocks
modify_user_security(group_name, op, code_list)  -- Modify watchlist
```

#### Price Alerts (2)

```
get_price_reminder(code=None, market=None)  -- Get price reminders
set_price_reminder(code, op, key=None, reminder_type=None, reminder_freq=None, value=None, note=None)  -- Set price reminders
```

#### IPO (1)

```
get_ipo_list(market)  -- Get IPO list
```

**Quote API Total: 35**

---

### Trading APIs (OpenSecTradeContext / OpenFutureTradeContext)

#### Account (3)

```
get_acc_list()  -- Get trading account list
unlock_trade(password=None, password_md5=None, is_unlock=True)  -- Unlock/lock trading (⚠️ This skill does not unlock via API — user must manually unlock in OpenD GUI)
accinfo_query(trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False, currency=Currency.HKD, asset_category=AssetCategory.NONE)  -- Query account funds
```

#### Order Placement & Modification (3)

```
place_order(price, qty, code, trd_side, order_type=OrderType.NORMAL, adjust_limit=0, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, remark=None, time_in_force=TimeInForce.DAY, fill_outside_rth=False, aux_price=None, trail_type=None, trail_value=None, trail_spread=None, session=Session.NONE)  -- Place order (rate limit: 15 times/30 sec)
modify_order(modify_order_op, order_id, qty, price, adjust_limit=0, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, aux_price=None, trail_type=None, trail_value=None, trail_spread=None)  -- Modify/cancel order (rate limit: 20 times/30 sec)
cancel_all_order(trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, trdmarket=TrdMarket.NONE)  -- Cancel all orders
```

#### Order Query (3)

```
order_list_query(order_id="", order_market=TrdMarket.NONE, status_filter_list=[], code='', start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)  -- Query today's orders
history_order_list_query(status_filter_list=[], code='', order_market=TrdMarket.NONE, start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0)  -- Query historical orders
order_fee_query(order_id_list=[], acc_id=0, acc_index=0, trd_env=TrdEnv.REAL)  -- Query order fees
```

#### Trade Query (2)

```
deal_list_query(code="", deal_market=TrdMarket.NONE, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)  -- Query today's trades
history_deal_list_query(code='', deal_market=TrdMarket.NONE, start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0)  -- Query historical trades
```

#### Position & Funds (4)

```
position_list_query(code='', position_market=TrdMarket.NONE, pl_ratio_min=None, pl_ratio_max=None, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)  -- Query positions
acctradinginfo_query(order_type, code, price, order_id=None, adjust_limit=0, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0)  -- Query max buy/sell quantity
get_acc_cash_flow(clearing_date='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, cashflow_direction=CashFlowDirection.NONE)  -- Query account cash flow
get_margin_ratio(code_list)  -- Query margin ratio
```

**Trading API Total: 15**

---

### Push Handlers (9)

#### Quote Push (7)

```
StockQuoteHandlerBase   -- Quote push callback
OrderBookHandlerBase    -- Order book push callback
CurKlineHandlerBase     -- K-line push callback
TickerHandlerBase       -- Tick-by-tick push callback
RTDataHandlerBase       -- Intraday push callback
BrokerHandlerBase       -- Broker queue push callback
PriceReminderHandlerBase -- Price alert push callback
```

#### Trade Push (2)

```
TradeOrderHandlerBase   -- Order status push callback
TradeDealHandlerBase    -- Trade push callback
```

Note: Trade push does not require separate subscription — automatically received after setting a Handler.

---

### Basic Interfaces

```
OpenQuoteContext(host='127.0.0.1', port=11111)  -- Create quote connection
OpenSecTradeContext(filter_trdmarket=TrdMarket.NONE, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)  -- Create securities trading connection (security_firm must be set according to the user's broker — see FUTU_SECURITY_FIRM enum table)
OpenFutureTradeContext(host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)  -- Create futures trading connection (security_firm same as above)
ctx.close()  -- Close connection
ctx.set_handler(handler)  -- Register push callback
SysNotifyHandlerBase  -- System notification callback
```

**All API Total: Quote 35 + Trading 15 + Push Handler 9 + Basic 6 = 65 interfaces**

## SubType Full List

| SubType | Description | Corresponding Push Handler |
|---------|-------------|---------------------------|
| `QUOTE` | Quotes | `StockQuoteHandlerBase` |
| `ORDER_BOOK` | Order book | `OrderBookHandlerBase` |
| `TICKER` | Tick-by-tick | `TickerHandlerBase` |
| `K_1M` ~ `K_MON` | K-line | `CurKlineHandlerBase` |
| `RT_DATA` | Intraday | `RTDataHandlerBase` |
| `BROKER` | Broker queue (HK only) | `BrokerHandlerBase` |

## Key Enum Values

- **TrdSide**: `BUY` | `SELL`
- **OrderType**: `NORMAL` (limit) | `MARKET` (market)
- **TrdEnv**: `REAL` | `SIMULATE`
- **ModifyOrderOp**: `NORMAL` (modify) | `CANCEL` (cancel)
- **TrdMarket**: `HK` | `US` | `CN` | `HKCC` | `SG`

## API Limits (Must Consider Before Calling)

Must consider the following limits when calling APIs to avoid requests failing due to insufficient quota or rate limit violations.

### Rate Limits

Rate limit rule: Max n calls within 30 seconds; the interval between the 1st and n+1st call must exceed 30 seconds.

| API | Rate Limit |
|-----|-----------|
| `place_order` | 15 times/30 sec |
| `modify_order` | 20 times/30 sec |
| `order_list_query` | 10 times/30 sec |

**Batch Operation Note**: When looping through rate-limited APIs (e.g. batch order placement, batch historical K-line queries), you must add appropriate `time.sleep()` intervals in the loop to avoid triggering rate limits.

### Subscription Quota Limits

- Each stock subscribed to one type consumes 1 subscription quota; unsubscribing releases the quota
- Different SubTypes for the same stock are counted separately
- At least 1 minute must pass after subscribing before unsubscribing
- All connections must unsubscribe the same ticker before the quota is released
- Closing a connection before 1 minute elapses does not release the subscription quota — wait 1 minute for automatic unsubscription
- Query used quota via `query_subscription.py`
- HK market requires LV1 or above permission to subscribe
- US pre-market/after-hours requires `--extended-time`

### Historical K-Line Quota Limits

- Within the last 30 days, each stock's historical K-line request consumes 1 quota
- Repeated requests for the same stock within 30 days do not accumulate additional quota
- Different cycles for the same stock only count as 1 quota
- **Before calling `request_history_kline`**, check remaining quota via `get_history_kl_quota(get_detail=True)` to confirm quota is sufficient
- **When batch-fetching K-lines for multiple stocks**, check quota first, confirm remaining quota >= number of stocks to query, then proceed

### Quota Tiers

Subscription and historical K-line quotas are tiered by user assets and trading activity:

| User Type | Subscription Quota | Historical K-Line Quota |
|-----------|-------------------|------------------------|
| New account | 100 | 100 |
| Total assets ≥ 10,000 HKD | 300 | 300 |
| Total assets ≥ 500,000 HKD OR monthly trades > 200 OR monthly trade value > 2,000,000 HKD (any one) | 1000 | 1000 |
| Total assets ≥ 5,000,000 HKD OR monthly trades > 2000 OR monthly trade value > 20,000,000 HKD (any one) | 2000 | 2000 |

### Other Limits

| API | Limit |
|-----|-------|
| `get_market_snapshot` | Max 400 tickers per request |
| `get_order_book` | Max num is 10 |
| `get_rt_ticker` | Max num is 1000 |
| `get_cur_kline` | Max num is 1000 |
| `request_history_kline` | Max single request max_count is 1000, use page_req_key for pagination |
| `get_stock_filter` | Max 200 results per request |

## Custom Handler Template

For push types not covered by scripts (e.g. order book, tick data, trade push), you can generate temporary code:

```python
import time
from futu import *

class MyHandler(OrderBookHandlerBase):  # Replace with the needed Handler base class
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("error:", data)
            return RET_ERROR, data
        print("Received push:")
        print(data)
        return RET_OK, data

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
quote_ctx.set_handler(MyHandler())
ret, data = quote_ctx.subscribe(['HK.00700'], [SubType.ORDER_BOOK], subscribe_push=True)
if ret == RET_OK:
    print('Subscription successful, waiting for push...')
time.sleep(60)
quote_ctx.close()
```

## Known Issues

### OpenD Slow Connection / Multi-Account Query Timeout

**Symptoms**: OpenD responses slow down or timeout when continuously querying multiple accounts, especially when creating multiple `OpenSecTradeContext` connections.

**Solution**:
- **Reuse the same connection**: Create `OpenSecTradeContext` only once and use the same `trd_ctx` to query all accounts, avoiding repeated connection setup
- **Don't loop scripts**: Don't run `get_portfolio.py` separately for each account (each creates/closes a connection) — write Python code to complete all queries in one connection
- **Add `sys.stdout.flush()`**: Flush output after each print in a loop to avoid output buffering hiding intermediate results

### Non-Margin Account Fields Return N/A

**Symptoms**: For non-margin accounts like TFSA and RRSP, `accinfo_query` returns `N/A` for margin-related fields like `initial_margin`, `maintenance_margin`, and `available_funds`. Directly calling `float()` on these values raises `ValueError`.

**Solution**:
- Use safe conversion for all numeric fields: `float(val) if val != 'N/A' else 0.0`
- When `available_funds` is N/A, for margin accounts use `total_assets - initial_margin`; for non-margin accounts (TFSA/RRSP), available funds equal `total_assets` (since there's no margin requirement)

### pandas & numpy Version Incompatibility

**Symptoms**: Running code throws `ValueError: numpy.dtype size changed`.

**Solution**: `pip install --upgrade pandas`

## Error Handling

| Error | Solution |
|-------|---------|
| Connection failed | Start OpenD |
| Order doesn't exist | Check with get_orders.py |
| Account not found | Check with get_accounts.py. If live account not found, `security_firm` may not match — run the broker auto-detection flow (get_accounts.py iterates through all SecurityFirms), or ask the user to confirm their region and manually specify `--security-firm` |
| Trading unlock failed / `unlock needed` | Must manually unlock trading password in OpenD GUI |
| Insufficient quote permissions (e.g. subscription failed, BMP permission not supported) | Tell the user to enable quote permissions — reference: https://openapi.futunn.com/futu-api-doc/intro/authority.html |
| Insufficient futures buying power | Tell the user to deposit funds or close some contracts to release margin |
| Futures order failed with OpenSecTradeContext | Futures must use `OpenFutureTradeContext`, not the securities trading context |
| Live order `Nonexisting acc_id` | The `acc_id` output by get_accounts.py may have precision loss due to `safe_int` using `int(float())` (already fixed). If still encountered, create context with `filter_trdmarket=TrdMarket.NONE` and directly print the DataFrame to verify the real acc_id |
| Live order `not unlocked` / `unlock needed` | Live trading requires the user to click "Unlock Trading" in the **OpenD GUI** first, enter the trading password, and the API cannot do this. Re-run the order after unlocking |
| Insufficient account buying power | Account available funds are insufficient to complete the order. Check funds details with `get_portfolio.py` — reduce quantity, sell positions to free up funds, or deposit and retry |
| Insufficient simulated account funds | There are two ways to restore simulated account funds: 1) Sell current position stocks to free up funds; 2) Reset the simulated account in the mobile App (path: 牛牛 → 我的 → 模拟交易 → 我的头像 → 我的道具 → 复活卡 — reference https://openapi.futunn.com/futu-api-doc/qa/trade.html#1690). Note: After reset, account funds restore to the initial value but historical order records are cleared |

## Response Rules

1. **Default to simulated environment** `SIMULATE`, unless the user explicitly requests live trading
2. **Prefer using scripts**: For features listed above, run the corresponding Python script directly
3. **For needs not covered by scripts**: Generate a temporary .py file to execute, then delete it after execution
4. Use the correct stock code format
5. **Do not manually specify `--market`**: The script automatically infers the market from the `--code` prefix (hard constraint in code)
6. When the user says "live", "real trading", or "real money", use `--trd-env REAL`
7. **Live orders are two-step execution (hard constraint in code)**: `place_order.py` enforces the `--confirmed` parameter in live environments. The first call without `--confirmed` returns the order summary and exits (exit code 2). After confirmation, the second call with `--confirmed` actually places the order. You should also use AskUserQuestion to confirm order details with the user first. If the API returns an unlock error, tell the user to manually unlock the trading password in the OpenD GUI. **Exception**: When the user asks to run their own strategy script, no additional confirmation is needed before each order, as the order logic in the strategy script is controlled by the user
8. All scripts support `--json` for easy parsing
9. For unclear interfaces, look them up in this skill's API quick reference first
10. **Futures trading must use `OpenFutureTradeContext`**: Existing trading scripts use `OpenSecTradeContext` and are not suitable for futures. Futures order placement, position queries, order cancellations, etc. require generating Python code directly — refer to the "Futures Trading Commands" chapter
11. **Backtesting uses pure backend mode**: When the user requests backtesting or running a backtest script, do not use any GUI components — use pure backend backtesting mode and save charts to files instead of displaying popups
12. **Check limits before calling interfaces** — see the "API Limits" chapter above
13. **Trading audit log**: All trading operations (place, modify, cancel orders) are automatically recorded to `~/.futu_trade_audit.jsonl`, including timestamp, operation parameters, and execution results — supports post-hoc audit tracing

User request: $ARGUMENTS
