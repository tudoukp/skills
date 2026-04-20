---
name: tiger-trade
description: Tiger Trade 自动化交易工具。通过相对位置坐标自动执行买入、卖出、市价单、限价单等交易操作。当用户提到「老虎交易」、「Tiger Trade 自动下单」、「自动买入/卖出股票」时使用此 Skill。
---

# Tiger Trade 自动化交易

## 命令格式

```bash
python scripts/trade.py --code <股票代码> --action <buy|sell> --order_type <market|limit> --price <价格> --quantity <数量>
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--code` | ✅ | 股票代码，如 `600519` |
| `--action` | ✅ | `buy`（买入）或 `sell`（卖出） |
| `--order_type` | ✅ | `market`（市价单）或 `limit`（限价单） |
| `--price` | 限价单必填 | 限价单价格 |
| `--quantity` | ✅ | 交易数量（股数） |

## 使用示例

**市价买入**：
```bash
python scripts/trade.py --code 600519 --action buy --order_type market --quantity 100
```

**限价买入**：
```bash
python scripts/trade.py --code 600519 --action buy --order_type limit --price 1800 --quantity 100
```

**市价卖出**：
```bash
python scripts/trade.py --code 600519 --action sell --order_type market --quantity 100
```

**限价卖出**：
```bash
python scripts/trade.py --code 600519 --action sell --order_type limit --price 1850 --quantity 100
```

## 使用前提

1. **安装依赖**：`pip install pyautogui pywin32 numpy`
2. Tiger Trade 窗口已打开并处于交易界面

## 注意事项

1. 交易过程中请勿移动鼠标或切换窗口
2. 限价单必须指定 `--price`，市价单无需指定价格
3. 建议先在模拟交易中测试
