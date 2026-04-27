"""Tiger Trade 交易自动化脚本 - 相对位置版本"""
import argparse
import time
import os
import win32gui
import win32con
import win32api
import pyautogui
import ctypes


# 锁文件配置
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".trade_lock")
LOCK_TIMEOUT = 60  # 锁超时时间（秒）


# 获取 DPI 缩放比例
try:
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    dpi_scale = user32.GetDpiForSystem() / 96.0
except:
    dpi_scale = 1.0


# ============================================================
# 相对位置配置（单位：像素，1.0x基准）
# 说明：
#   - stock_input: 相对于窗口左上角 (window_left + x, window_top + y)
#   - 其他所有控件: 相对于窗口右下角 (window_right - x, window_bottom - y)
#   - 操作时会根据当前DPI缩放值自动转换
# ============================================================

# 股票代码输入框（相对于左上角）
REL_STOCK_INPUT_X = 154
REL_STOCK_INPUT_Y = 16

# 买入按钮（相对于右下角）
REL_BUY_BUTTON_X = 292
REL_BUY_BUTTON_Y = 72
REL_BUY_BUTTON_2_X = 261
REL_BUY_BUTTON_2_Y = 370

# 卖出按钮（相对于右下角）
REL_SELL_BUTTON_X = 61
REL_SELL_BUTTON_Y = 75
REL_SELL_BUTTON_2_X = 98
REL_SELL_BUTTON_2_Y = 377

# 市价单按钮（相对于右下角）
REL_MARKET_ORDER_X = 187
REL_MARKET_ORDER_Y = 339

# 限价单按钮（相对于右下角）
REL_LIMIT_ORDER_X = 296
REL_LIMIT_ORDER_Y = 338

# 价格输入框（相对于右下角）- 限价单用
REL_PRICE_INPUT_X = 228
REL_PRICE_INPUT_Y = 299

# 数量输入框（相对于右下角）- 限价单用
REL_QUANTITY_INPUT_X = 229
REL_QUANTITY_INPUT_Y = 272

# 数量输入框（相对于右下角）- 市价单用（在价格输入框位置）
REL_MARKET_QUANTITY_INPUT_X = 228
REL_MARKET_QUANTITY_INPUT_Y = 299

# 提交订单按钮（相对于右下角）
REL_SUBMIT_ORDER_X = 182
REL_SUBMIT_ORDER_Y = 73

# 解锁交易按钮（相对于右下角）
REL_UNLOCK_TRADE_X = 0
REL_UNLOCK_TRADE_Y = 0

# 确认弹窗按钮（相对于右下角）
REL_CONFIRM_DIALOG_X = 826
REL_CONFIRM_DIALOG_Y = 600


class TradeAutomationError(Exception):
    """交易自动化异常基类"""
    pass


class WindowNotFoundError(TradeAutomationError):
    """窗口未找到"""
    pass


class ScriptLockError(TradeAutomationError):
    """脚本锁定异常"""
    pass


def acquire_lock():
    """
    获取脚本锁
    - 超时时间 60 秒
    - 如果锁文件存在且未超时，返回 False 并提示
    - 如果锁文件存在但已超时，自动删除并获取新锁
    - 获取成功后返回 True
    """
    # 检查锁文件是否存在
    if os.path.exists(LOCK_FILE):
        try:
            # 读取锁文件内容（包含创建时间）
            with open(LOCK_FILE, 'r') as f:
                lock_time = float(f.read().strip())

            current_time = time.time()
            elapsed = current_time - lock_time

            # 检查锁是否超时
            if elapsed < LOCK_TIMEOUT:
                print(f"\n[警告] 脚本正在运行中，请稍后再试")
                print(f"[提示] 锁将在 {int(LOCK_TIMEOUT - elapsed)} 秒后自动释放")
                return False
            else:
                # 锁已超时，删除旧锁文件
                print(f"[提示] 检测到超时的锁文件，自动清理并获取新锁")
                os.remove(LOCK_FILE)
        except (ValueError, IOError):
            # 锁文件内容无效，删除并创建新的
            try:
                os.remove(LOCK_FILE)
            except:
                pass

    # 创建锁文件
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(time.time()))
        return True
    except Exception as e:
        print(f"[错误] 无法创建锁文件: {e}")
        return False


def release_lock():
    """释放脚本锁"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


def find_window(name):
    """查找窗口句柄"""
    hwnd = win32gui.FindWindow(None, name)
    if hwnd == 0:
        raise WindowNotFoundError(f"未找到窗口: {name}")
    return hwnd


def get_window_rect(hwnd):
    """获取窗口矩形区域（像素）"""
    rect = win32gui.GetWindowRect(hwnd)
    # rect = (left, top, right, bottom)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    return {
        'left': left,
        'top': top,
        'right': right,
        'bottom': bottom,
        'width': width,
        'height': height
    }


def activate_window(hwnd):
    """激活窗口"""
    # 判断窗口是否最小化
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    # 将窗口置顶
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)


def calc_absolute_position(rel_x, rel_y, window_rect, relative_to_top_left=False):
    """
    计算绝对坐标

    relative_to_top_left=True:  相对于窗口左上角
    relative_to_top_left=False: 相对于窗口右下角

    rel_x, rel_y: 相对于1.0x的像素偏移值
    """
    if relative_to_top_left:
        # 相对于左上角: window_left + offset * dpi_scale
        abs_x = window_rect['left'] + int(rel_x * dpi_scale)
        abs_y = window_rect['top'] + int(rel_y * dpi_scale)
    else:
        # 相对于右下角: window_right - offset * dpi_scale
        abs_x = window_rect['right'] - int(rel_x * dpi_scale)
        abs_y = window_rect['bottom'] - int(rel_y * dpi_scale)

    return abs_x, abs_y


def click_position(x, y):
    """点击指定位置"""
    pyautogui.click(x, y)
    time.sleep(0.5)


def click_relative(rel_x, rel_y, window_rect, relative_to_top_left=False):
    """基于相对位置点击"""
    abs_x, abs_y = calc_absolute_position(rel_x, rel_y, window_rect, relative_to_top_left)
    print(f"点击位置: ({abs_x}, {abs_y}) [偏移: ({rel_x}, {rel_y}), 基于{'左上' if relative_to_top_left else '右下'}]")
    click_position(abs_x, abs_y)


def clear_input():
    """清空输入框内容（全选后删除）"""
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.2)


def type_number(num):
    """使用 win32api 直接发送数字键，绕过输入法"""
    for char in str(num):
        if char == '.':
            vk_code = 0xBE  # 小数点
        elif char == '-':
            vk_code = 0xBD  # 负号
        else:
            vk_code = ord(char)
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.03)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)


def input_stock_code(code, window_rect):
    """输入股票代码"""
    print(f"输入股票代码: {code}")
    # 股票输入框相对于左上角
    click_relative(REL_STOCK_INPUT_X, REL_STOCK_INPUT_Y, window_rect, relative_to_top_left=True)

    # 切换到英文输入模式
    win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)

    # 清空输入框
    clear_input()

    # 使用 win32api 直接发送数字键
    for char in str(code):
        if char.isdigit():
            vk_code = ord(char)
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            pyautogui.typewrite(char, interval=0.05)

    time.sleep(0.3)

    # 按两次回车确认
    pyautogui.press('enter')
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(1.0)
    print("股票代码已输入")


def click_trade_button(action, window_rect):
    """点击买入或卖出按钮（点击两次在不同位置）"""
    if action == 'buy':
        click_relative(REL_BUY_BUTTON_X, REL_BUY_BUTTON_Y, window_rect)
        time.sleep(0.3)
        click_relative(REL_BUY_BUTTON_2_X, REL_BUY_BUTTON_2_Y, window_rect)
    else:
        click_relative(REL_SELL_BUTTON_X, REL_SELL_BUTTON_Y, window_rect)
        time.sleep(0.3)
        click_relative(REL_SELL_BUTTON_2_X, REL_SELL_BUTTON_2_Y, window_rect)
    time.sleep(0.5)


def click_order_type(order_type, window_rect):
    """点击市价单或限价单按钮"""
    if order_type == 'market':
        click_relative(REL_MARKET_ORDER_X, REL_MARKET_ORDER_Y, window_rect)
    else:
        click_relative(REL_LIMIT_ORDER_X, REL_LIMIT_ORDER_Y, window_rect)
    time.sleep(0.5)


def input_price_and_quantity(price, quantity, window_rect):
    """输入价格和数量（限价单）"""
    # 切换到英文输入模式
    win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

    # 点击价格输入框
    click_relative(REL_PRICE_INPUT_X, REL_PRICE_INPUT_Y, window_rect)
    clear_input()
    print(f"输入价格: {price}")
    type_number(price)
    time.sleep(0.3)

    # 点击数量输入框
    click_relative(REL_QUANTITY_INPUT_X, REL_QUANTITY_INPUT_Y, window_rect)
    clear_input()
    print(f"输入数量: {quantity}")
    type_number(quantity)
    time.sleep(0.3)


def input_quantity_only(quantity, window_rect):
    """仅输入数量（市价单）"""
    win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

    # 市价单数量输入框在价格输入框位置
    click_relative(REL_MARKET_QUANTITY_INPUT_X, REL_MARKET_QUANTITY_INPUT_Y, window_rect)
    clear_input()
    print(f"输入数量: {quantity}")
    type_number(quantity)
    time.sleep(0.3)


def click_submit_order(window_rect):
    """点击提交订单按钮"""
    print("点击提交订单按钮")
    click_relative(REL_SUBMIT_ORDER_X, REL_SUBMIT_ORDER_Y, window_rect)
    time.sleep(0.5)

    # 检查确认弹窗
    check_confirm_dialog(window_rect)


def check_confirm_dialog(window_rect):
    """确认弹窗：移动到窗口上方正中心，向下10像素，点击后多次按空格键"""
    # 计算窗口上方正中心位置
    top_center_x = (window_rect['left'] + window_rect['right']) // 2
    top_center_y = window_rect['top'] + 10

    for _ in range(5):
        pyautogui.moveTo(top_center_x, top_center_y, duration=0.2)
        time.sleep(0.2)
        pyautogui.click()
        time.sleep(0.3)
        pyautogui.press('space')
        time.sleep(0.5)


def main():
    # 获取脚本锁
    if not acquire_lock():
        return 1

    try:
        parser = argparse.ArgumentParser(description='Tiger Trade 自动化交易（相对位置版）')
        parser.add_argument('--code', required=True, help='股票代码')
        parser.add_argument('--action', required=True, choices=['buy', 'sell'], help='买入或卖出')
        parser.add_argument('--order_type', required=True, choices=['market', 'limit'], help='市价单或限价单')
        parser.add_argument('--price', type=float, help='价格（限价单必填）')
        parser.add_argument('--quantity', type=int, required=True, help='数量')
        args = parser.parse_args()

        if args.order_type == 'limit' and args.price is None:
            print("错误: 限价单必须指定价格 --price")
            return 1

        WINDOW_NAME = "Tiger Trade"

        print(f"[{time.strftime('%H:%M:%S')}] 开始执行交易指令...")

        # 1. 激活窗口
        print(f"[1/7] 激活窗口: {WINDOW_NAME}")
        hwnd = find_window(WINDOW_NAME)
        activate_window(hwnd)

        # 获取窗口尺寸
        window_rect = get_window_rect(hwnd)
        print(f"窗口尺寸: {window_rect['width']}x{window_rect['height']}, 位置: ({window_rect['left']}, {window_rect['top']})")

        # 2. 检查交易锁定（暂时跳过，需要模板）
        # print(f"[2/7] 检查交易锁定状态...")

        # 3. 输入股票代码
        print(f"[3/7] 输入股票代码: {args.code}")
        input_stock_code(args.code, window_rect)

        # 4. 点击买卖按钮
        print(f"[4/7] 点击{args.action}按钮")
        click_trade_button(args.action, window_rect)

        # 5. 点击市价单或限价单
        print(f"[5/7] 选择订单类型: {args.order_type}")
        click_order_type(args.order_type, window_rect)

        # 6. 输入价格和数量
        if args.order_type == 'limit':
            print(f"[6/7] 输入价格和数量: {args.price} x {args.quantity}")
            input_price_and_quantity(args.price, args.quantity, window_rect)
        else:
            print(f"[6/7] 输入数量: {args.quantity}")
            input_quantity_only(args.quantity, window_rect)

        # 7. 点击提交订单按钮
        print(f"[7/7] 点击提交订单按钮")
        click_submit_order(window_rect)

        order_desc = "市价单" if args.order_type == 'market' else f"限价单 @{args.price}"
        print(f"\n[OK] 交易指令已发送: {args.action.upper()} {args.code} {args.quantity}股 ({order_desc})")

    except WindowNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("请确保 Tiger Trade 窗口已打开")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1
    finally:
        release_lock()

    return 0


if __name__ == "__main__":
    main()
