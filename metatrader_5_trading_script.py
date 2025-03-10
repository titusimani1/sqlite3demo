import MetaTrader5 as mt5
import time
from datetime import datetime
import decimal
from decimal import Decimal
from typing import Optional, List, Tuple


# Configuration Variables (Simplified for MT5)
class MT5ConfigVar:
    def __init__(self, key: str, prompt: str, default, validator=None, required_if=None):
        self.key = key
        self.prompt = prompt
        self.value = default
        self.validator = validator
        self.required_if = required_if

    def validate(self):
        if self.validator and self.validator(self.value) is not None:
            raise ValueError(self.validator(self.value))

# Strategy-Specific Validators (Adapted for MT5)
def validate_decimal_mt5(value: Decimal, min_value: Decimal = None, max_value: Decimal = None, inclusive: bool = True) -> Optional[str]:
    try:
        if min_value is not None and ((inclusive and value < min_value) or (not inclusive and value <= min_value)):
            return f"Value must be greater than {min_value}."
        if max_value is not None and ((inclusive and value > max_value) or (not inclusive and value >= max_value)):
            return f"Value must be less than {max_value}."
        return None
    except decimal.InvalidOperation:
        return "Invalid decimal format."

def validate_price_floor_ceiling_mt5(value: str) -> Optional[str]:
    try:
        decimal_value = Decimal(value)
    except Exception:
        return f"{value} is not in decimal format."
    if not (decimal_value == Decimal("-1") or decimal_value > Decimal("0")):
        return "Value must be more than 0 or -1 to disable this feature."

def validate_decimal_list_mt5(value: str) -> Optional[str]:
    decimal_list = list(value.split(","))
    for number in decimal_list:
        try:
            validate_result = validate_decimal_mt5(Decimal(number), 0, 100, inclusive=False)
        except decimal.InvalidOperation:
            return "Please enter valid decimal numbers"
        if validate_result is not None:
            return validate_result

# MT5 Pure Market Making Configuration Map
mt5_pure_market_making_config_map = {
    "symbol": MT5ConfigVar(key="symbol", prompt="Enter the trading symbol (e.g., EURUSD) >>> ", default="EURUSD"),
    "bid_spread": MT5ConfigVar(key="bid_spread", prompt="Bid spread (%) >>> ", default=Decimal("0.1"), validator=lambda v: validate_decimal_mt5(v, 0, 100, inclusive=False)),
    "ask_spread": MT5ConfigVar(key="ask_spread", prompt="Ask spread (%) >>> ", default=Decimal("0.1"), validator=lambda v: validate_decimal_mt5(v, 0, 100, inclusive=False)),
    "order_amount": MT5ConfigVar(key="order_amount", prompt="Order amount (lots) >>> ", default=Decimal("0.1"), validator=lambda v: validate_decimal_mt5(v, min_value=Decimal("0"), inclusive=False)),
    "price_ceiling": MT5ConfigVar(key="price_ceiling", prompt="Price ceiling (-1 to disable) >>> ", default=Decimal("-1"), validator=validate_price_floor_ceiling_mt5),
    "price_floor": MT5ConfigVar(key="price_floor", prompt="Price floor (-1 to disable) >>> ", default=Decimal("-1"), validator=validate_price_floor_ceiling_mt5),
    "order_refresh_time": MT5ConfigVar(key="order_refresh_time", prompt="Order refresh time (seconds) >>> ", default=Decimal("30"), validator=lambda v: validate_decimal_mt5(v, 0, inclusive=False)),
    "order_levels": MT5ConfigVar(key="order_levels", prompt="Number of order levels >>> ", default=1, validator=lambda v: validate_decimal_mt5(Decimal(v), min_value=0, inclusive=False)),
    "order_level_spread": MT5ConfigVar(key="order_level_spread", prompt="Order level spread (%) >>> ", default=Decimal("0.05"), validator=lambda v: validate_decimal_mt5(v, 0, 100, inclusive=False)),
    "order_level_amount": MT5ConfigVar(key="order_level_amount", prompt="Order level amount change (lots) >>> ", default=Decimal("0.0"), validator=validate_decimal_mt5),
    "split_order_levels_enabled": MT5ConfigVar(key="split_order_levels_enabled", prompt="Use split order levels? (True/False) >>> ", default=False, validator=validate_bool_mt5),
    "bid_order_level_spreads": MT5ConfigVar(key="bid_order_level_spreads", prompt="Bid order level spreads (e.g., 0.1,0.2) >>> ", default=None, validator=validate_decimal_list_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("split_order_levels_enabled").value),
    "ask_order_level_spreads": MT5ConfigVar(key="ask_order_level_spreads", prompt="Ask order level spreads (e.g., 0.1,0.2) >>> ", default=None, validator=validate_decimal_list_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("split_order_levels_enabled").value),
    "bid_order_level_amounts": MT5ConfigVar(key="bid_order_level_amounts", prompt="Bid order level amounts (e.g., 0.1,0.2) >>> ", default=None, validator=validate_decimal_list_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("split_order_levels_enabled").value),
    "ask_order_level_amounts": MT5ConfigVar(key="ask_order_level_amounts", prompt="Ask order level amounts (e.g., 0.1,0.2) >>> ", default=None, validator=validate_decimal_list_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("split_order_levels_enabled").value),
    "minimum_spread": MT5ConfigVar(key="minimum_spread", prompt="Minimum spread to cancel orders (%) >>> ", default=Decimal("-100"), validator=lambda v: validate_decimal_mt5(v, -100, 100, True)),
    "moving_price_band_enabled": MT5ConfigVar(key="moving_price_band_enabled", prompt="Enable moving price bands? (True/False) >>> ", default=False, validator=validate_bool_mt5),
    "price_ceiling_pct": MT5ConfigVar(key="price_ceiling_pct", prompt="Price ceiling percentage >>> ", default=Decimal("1"), validator=validate_decimal_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("moving_price_band_enabled").value),
    "price_floor_pct": MT5ConfigVar(key="price_floor_pct", prompt="Price floor percentage >>> ", default=Decimal("-1"), validator=validate_decimal_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("moving_price_band_enabled").value),
    "price_band_refresh_time": MT5ConfigVar(key="price_band_refresh_time", prompt="Price band refresh time (seconds) >>> ", default=Decimal("86400"), validator=validate_decimal_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("moving_price_band_enabled").value),
    "ping_pong_enabled": MT5ConfigVar(key="ping_pong_enabled", prompt="Enable ping pong? (True/False) >>> ", default=False, validator=validate_bool_mt5),
    "order_level_spread": MT5ConfigVar(key="order_level_spread", prompt="Order level spread (%) >>> ", default=Decimal("1"), validator=lambda v: validate_decimal_mt5(v, 0, 100, inclusive=False), required_if=lambda: mt5_pure_market_making_config_map.get("order_levels").value > 1),
    "order_level_amount": MT5ConfigVar(key="order_level_amount", prompt="Order level amount change (lots) >>> ", default=Decimal("0"), validator=validate_decimal_mt5, required_if=lambda: mt5_pure_market_making_config_map.get("order_levels").value > 1),
    "inventory_skew_enabled": MT5ConfigVar(key="inventory_skew_enabled", prompt="Enable inventory skew? (True/False) >>> ", default=False, validator=validate_bool_mt5),
    "inventory_target_base_pct": MT5ConfigVar(key="inventory_target_base_pct", prompt="Inventory target base percentage >>> ", default=Decimal("50"), validator=lambda v: validate_decimal_mt5(v, 0, 100), required_if=lambda: mt5_pure_market_making_config_map.get("inventory_skew_enabled").value),
    "inventory_range_multiplier": MT5ConfigVar(key="inventory_range_multiplier", prompt="Inventory range multiplier >>> ", default=Decimal("1"), validator=lambda v: validate_decimal_mt5(v, min_value=0, inclusive=False), required_if=lambda: mt5_pure_market_making_config_map.get("inventory_skew_enabled").value),
    "inventory_price": MT5ConfigVar(key="inventory_price", prompt="Inventory price >>> ", default=Decimal("1"), validator=lambda v: validate_decimal_mt5(v, min_value=0, inclusive=True), required_if=lambda: mt5_pure_market_making_config_map.get("price_type").value == "inventory_cost"),
    "filled_order_delay": MT5ConfigVar(key="filled_order_delay", prompt="Filled order delay (seconds) >>> ", default=Decimal("60"), validator=lambda v: validate_decimal_mt5(v, min_value=0, inclusive=False)),
    "hanging_orders_enabled": MT5ConfigVar(key="hanging_orders_enabled", prompt="Enable hanging orders? (True/False) >>> ", default=False, validator=validate_bool_mt5),
    "hanging_orders_cancel_pct": MT5ConfigVar(key="hanging_orders_cancel_pct", prompt="Hanging order cancel percentage >>> ", default=Decimal("10"), validator=lambda v: validate_decimal_mt5(v, 0, 1

def initialize_mt5():
    """Initializes MT5 connection."""
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    print("MT5 initialized successfully.")



def validate_price_source_mt5(value: str) -> Optional[str]:
    if value not in {"current_market", "historical_csv"}:
        return "Invalid price source type. Use 'current_market' or 'historical_csv'."
    return None




def get_symbol_info(symbol: str):
    """Retrieves symbol information."""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        raise ValueError(f"Symbol {symbol} not found.")
    return symbol_info

def get_tick_info(symbol: str):
    """Retrieves tick information."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise ValueError(f"Failed to get tick info for {symbol}.")
    return tick

def send_order(symbol: str, order_type: int, volume: float, price: float, magic: int = 123456):
    """Sends an order to MT5."""
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "magic": magic,
        "deviation": 20, #Slippage control, in points.
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise ValueError(f"Order send failed, retcode={result.retcode}, comment={result.comment}")
    return result

def close_order(ticket: int):
    """Closes an order."""
    positions = mt5.positions_get()
    for position in positions:
        if position.ticket == ticket:
            symbol_info_tick = mt5.symbol_info_tick(position.symbol)
            if position.type == 0:  # BUY order, close with SELL
                close_price = symbol_info_tick.bid
            else:  # SELL order, close with BUY
                close_price = symbol_info_tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": position.ticket,
                "price": close_price,  # Corrected: Added the close price
                "deviation": 20, #Slippage
                "magic": 123456,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Order close failed, retcode={result.retcode}, comment={result.comment}")
            else:
                print(f"Order {ticket} closed successfully")
            return result




# ... (rest of the code)

def main():
    initialize_mt5()
    symbol = mt5_pure_market_making_config_map["symbol"].value
    order_amount = float(mt5_pure_market_making_config_map["order_amount"].value)
    bid_spread = float(mt5_pure_market_making_config_map["bid_spread"].value) / 100
    ask_spread = float(mt5_pure_market_making_config_map["ask_spread"].value) / 100
    order_refresh_time = float(mt5_pure_market_making_config_map["order_refresh_time"].value)
    price_ceiling = float(mt5_pure_market_making_config_map["price_ceiling"].value)
    price_floor = float(mt5_pure_market_making_config_map["price_floor"].value)
    price_source = mt5_pure_market_making_config_map.get("price_source").value

    if price_source == "historical_csv":
        csv_file_path = "historical.csv"  # Replace with your CSV file path
        try:
            with open(csv_file_path, mode='r') as file:
                csv_reader = csv.reader(file)  # Use csv.reader instead of csv.DictReader
                next(csv_reader) # Skip the header row.
                for row in csv_reader:
                    try:
                        date_str, time_str, bid_str, ask_str, *_ = row #unpack row
                        bid_price = float(bid_str)
                        ask_price = float(ask_str)
                        timestamp_str = f"{date_str} {time_str}"
                        timestamp = datetime.strptime(timestamp_str, "%Y.%m.%d %H:%M") # adjust timestamp string format to your csv file.
                        print(f"Processing timestamp: {timestamp}")

                        if price_ceiling != -1 and ask_price >= price_ceiling:
                            print(f"Price ceiling reached ({ask_price} >= {price_ceiling}). Skipping order placement.")
                            time.sleep(order_refresh_time)
                            continue

                        if price_floor != -1 and bid_price <= price_floor:
                            print(f"Price floor reached ({bid_price} <= {price_floor}). Skipping order placement.")
                            time.sleep(order_refresh_time)
                            continue

                        bid_order_price = bid_price * (1 - bid_spread)
                        ask_order_price = ask_price * (1 + ask_spread)

                        # Place bid order
                        try:
                            send_order(symbol, mt5.ORDER_TYPE_BUY, order_amount, bid_order_price)
                            print(f"Placed bid order at {bid_order_price}")
                        except ValueError as e:
                            print(f"Failed to place bid order: {e}")

                        # Place ask order
                        try:
                            send_order(symbol, mt5.ORDER_TYPE_SELL, order_amount, ask_order_price)
                            print(f"Placed ask order at {ask_order_price}")
                        except ValueError as e:
                            print(f"Failed to place ask order: {e}")

                        time.sleep(order_refresh_time)

                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error processing CSV row: {e}")
                        continue # skip to the next csv row.

        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_file_path}")

    elif price_source == "current_market":
        while True:
            try:
                tick = get_tick_info(symbol)
                bid_price = tick.bid
                ask_price = tick.ask

                if price_ceiling != -1 and ask_price >= price_ceiling:
                    print(f"Price ceiling reached ({ask_price} >= {price_ceiling}). Skipping order placement.")
                    time.sleep(order_refresh_time)
                    continue

                if price_floor != -1 and bid_price <= price_floor:
                    print(f"Price floor reached ({bid_price} <= {price_floor}). Skipping order placement.")
                    time.sleep(order_refresh_time)
                    continue

                bid_order_price = bid_price * (1 - bid_spread)
                ask_order_price = ask_price * (1 + ask_spread)

                # Place bid order
                try:
                    send_order(symbol, mt5.ORDER_TYPE_BUY, order_amount, bid_order_price)
                    print(f"Placed bid order at {bid_order_price}")
                except ValueError as e:
                    print(f"Failed to place bid order: {e}")

                # Place ask order
                try:
                    send_order(symbol, mt5.ORDER_TYPE_SELL, order_amount, ask_order_price)
                    print(f"Placed ask order at {ask_order_price}")
                except ValueError as e:
                    print(f"Failed to place ask order: {e}")

                time.sleep(order_refresh_time)

            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

