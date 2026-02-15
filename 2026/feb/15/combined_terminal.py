#!/usr/bin/env python3
"""
Combined Crypto Terminal Application
Displays Binance trades, BitMEX trades, and BitMEX trollbox in 3 vertical sections
"""

import curses
import json
import threading
import websocket
import time
from datetime import datetime, timezone
from collections import deque

# Store data for each section
binance_trades = deque(maxlen=50)
bitmex_trades = deque(maxlen=50)
trollbox_messages = deque(maxlen=50)
bitfinex_trades = deque(maxlen=50)
coinbase_trades = deque(maxlen=50)

# Order book state (for incremental updates)
order_book = {'bids': {}, 'asks': {}}

# WebSocket connections
binance_ws = None
bitmex_ws = None
bitfinex_ws = None
coinbase_ws = None

# Connection status
binance_status = "Connecting..."
bitmex_status = "Connecting..."
bitfinex_status = "Connecting..."
coinbase_status = "Connecting..."

# Reconnection settings
binance_reconnect_delay = 5
bitmex_reconnect_delay = 5
bitfinex_reconnect_delay = 5
coinbase_reconnect_delay = 5
max_reconnect_delay = 60


# ============== BINANCE HANDLERS ==============

def binance_on_message(ws, message):
    """Handle Binance WebSocket messages"""
    global binance_status
    try:
        data = json.loads(message)
        
        if 'e' in data and data['e'] == 'trade':
            timestamp = datetime.fromtimestamp(data['T'] / 1000, tz=timezone.utc).strftime('%H:%M:%S')
            side = 'Sell' if data['m'] else 'Buy'
            price = float(data['p'])
            quantity = float(data['q'])
            
            # Single line with padding
            trade_info = {
                'text': f"{timestamp}  {side:4}  ${price:>11,.2f}  {quantity:>10.4f}",
                'side': side
            }
            binance_trades.append(trade_info)
            binance_status = f"Live - {len(binance_trades)} trades"
    except Exception as e:
        binance_trades.append({
            'text': f"Error: {str(e)}",
            'side': 'Error'
        })


def binance_on_error(ws, error):
    """Handle Binance WebSocket errors"""
    global binance_status
    binance_status = f"Error: {str(error)}"


def binance_on_close(ws, close_status_code, close_msg):
    """Handle Binance WebSocket close"""
    global binance_status
    binance_status = "Disconnected"


def binance_on_open(ws):
    """Binance connection opened"""
    global binance_status, binance_reconnect_delay
    binance_status = "Connected"
    binance_reconnect_delay = 5
    binance_trades.append({
        'text': "Connected to Binance",
        'side': 'Info'
    })


def binance_websocket_thread():
    """Run Binance WebSocket in a separate thread"""
    global binance_ws, binance_status, binance_reconnect_delay
    
    consecutive_failures = 0
    
    while True:
        try:
            binance_status = "Connecting to Binance..."
            binance_ws = websocket.WebSocketApp(
                "wss://stream.binance.com:9443/ws/btcusdt@trade",
                on_message=binance_on_message,
                on_error=binance_on_error,
                on_close=binance_on_close,
                on_open=binance_on_open
            )
            binance_ws.run_forever()
            
            consecutive_failures += 1
            binance_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            binance_status = f"Reconnecting in {binance_reconnect_delay}s..."
            time.sleep(binance_reconnect_delay)
            
        except Exception as e:
            consecutive_failures += 1
            binance_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            binance_status = f"Error. Retry in {binance_reconnect_delay}s"
            time.sleep(binance_reconnect_delay)


# ============== BITMEX HANDLERS ==============

def bitmex_on_message(ws, message):
    """Handle BitMEX WebSocket messages"""
    global bitmex_status
    try:
        data = json.loads(message)
        
        # Handle subscription confirmation
        if 'success' in data and data['success']:
            bitmex_status = "Connected & Subscribed"
            bitmex_trades.append({
                'text': f"Subscribed: {data.get('subscribe', 'unknown')}",
                'side': 'Info'
            })
            # Also log to trollbox
            trollbox_messages.append({
                'text': f"✓ Subscribed: {data.get('subscribe', 'N/A')}"
            })
            return
        
        # Handle subscription errors
        if 'error' in data:
            error_msg = data.get('error', 'Unknown error')
            trollbox_messages.append({
                'text': f"✗ Error: {error_msg}"
            })
            return
            
        # Handle trade data
        if 'table' in data and data['table'] == 'trade':
            if 'data' in data:
                for trade in data['data']:
                    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
                    side = trade.get('side', 'Unknown')
                    price = trade.get('price', 0)
                    size = trade.get('size', 0)
                    
                    # Single line with padding
                    trade_info = {
                        'text': f"{timestamp}  {side:4}  ${price:>11,.2f}  {size:>10,}",
                        'side': side
                    }
                    bitmex_trades.append(trade_info)
                    
        # Handle trollbox/chat data
        elif 'table' in data and data['table'] == 'chat':
            if 'data' in data:
                trollbox_messages.append({
                    'text': f"✓ Chat data received!"
                })
                for msg in data['data']:
                    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
                    user = msg.get('user', msg.get('username', 'Anonymous'))
                    message_text = msg.get('message', msg.get('text', ''))
                    channel = msg.get('channelID', 'N/A')
                    
                    # Truncate long usernames
                    if len(user) > 12:
                        user = user[:12]
                    
                    # Single line format
                    chat_info = {
                        'text': f"{timestamp}  {user}:  {message_text}"
                    }
                    trollbox_messages.append(chat_info)
        
        # Handle order book data (orderBookL2_25 format)
        elif 'table' in data and 'orderBookL2' in data['table']:
            global order_book
            
            if 'action' in data:
                action = data['action']
                
                # Process updates
                if 'data' in data:
                    for item in data['data']:
                        price = item.get('price')
                        size = item.get('size', 0)
                        side = item.get('side')
                        order_id = item.get('id')
                        
                        if action == 'partial' or action == 'insert':
                            # Add or initialize
                            if side == 'Sell':
                                order_book['asks'][price] = size
                            elif side == 'Buy':
                                order_book['bids'][price] = size
                        elif action == 'update':
                            # Update existing
                            if side == 'Sell' and price in order_book['asks']:
                                order_book['asks'][price] = size
                            elif side == 'Buy' and price in order_book['bids']:
                                order_book['bids'][price] = size
                        elif action == 'delete':
                            # Remove
                            if side == 'Sell' and price in order_book['asks']:
                                del order_book['asks'][price]
                            elif side == 'Buy' and price in order_book['bids']:
                                del order_book['bids'][price]
                
                # Rebuild display
                trollbox_messages.clear()
                
                # Header
                trollbox_messages.append({
                    'text': "ORDER BOOK - XBTUSD"
                })
                trollbox_messages.append({
                    'text': "=" * 30
                })
                
                # Asks (sell orders) - sorted lowest to highest, display highest first
                asks_sorted = sorted(order_book['asks'].items(), key=lambda x: x[0])
                asks_display = asks_sorted[-15:][::-1]  # Get top 15 and reverse
                
                trollbox_messages.append({
                    'text': "ASKS (Sell)"
                })
                for price, size in asks_display:
                    trollbox_messages.append({
                        'text': f"${price:>9,.2f} | {size:>8,}"
                    })
                
                trollbox_messages.append({
                    'text': "=" * 30
                })
                
                # Bids (buy orders) - sorted highest to lowest
                bids_sorted = sorted(order_book['bids'].items(), key=lambda x: x[0], reverse=True)
                bids_display = bids_sorted[:15]  # Get top 15
                
                trollbox_messages.append({
                    'text': "BIDS (Buy)"
                })
                for price, size in bids_display:
                    trollbox_messages.append({
                        'text': f"${price:>9,.2f} | {size:>8,}"
                    })
        
        else:
            # Debug: log other message types
            if 'table' in data:
                trollbox_messages.append({
                    'text': f"Table: {data['table']}"
                })
            elif 'info' in data:
                trollbox_messages.append({
                    'text': f"Info: {data['info']}"
                })
            elif not ('success' in data or 'error' in data):
                # Log other message types we don't recognize
                keys = list(data.keys())[:3]  # Show first 3 keys
                trollbox_messages.append({
                    'text': f"Msg keys: {', '.join(keys)}"
                })
                    
        bitmex_status = f"Live - {len(bitmex_trades)}T/{len(trollbox_messages)}C"
    except Exception as e:
        bitmex_trades.append({
            'text': f"Error: {str(e)}",
            'side': 'Error'
        })
        trollbox_messages.append({
            'text': f"Error: {str(e)}"
        })


def bitmex_on_error(ws, error):
    """Handle BitMEX WebSocket errors"""
    global bitmex_status
    bitmex_status = f"Error: {str(error)}"


def bitmex_on_close(ws, close_status_code, close_msg):
    """Handle BitMEX WebSocket close"""
    global bitmex_status
    bitmex_status = "Disconnected"


def bitmex_on_open(ws):
    """Subscribe to BitMEX trades and order book"""
    global bitmex_status, bitmex_reconnect_delay
    bitmex_status = "Subscribing..."
    bitmex_reconnect_delay = 5
    bitmex_trades.append({
        'text': "Connected to BitMEX",
        'side': 'Info'
    })
    
    # Add info message to order book
    trollbox_messages.append({
        'text': "Loading Order Book..."
    })
    
    # Subscribe to trades and order book (top 25 levels to show 15)
    subscribe_msg = {
        "op": "subscribe",
        "args": ["trade:XBTUSD", "orderBookL2_25:XBTUSD"]
    }
    ws.send(json.dumps(subscribe_msg))


def bitmex_websocket_thread():
    """Run BitMEX WebSocket in a separate thread"""
    global bitmex_ws, bitmex_status, bitmex_reconnect_delay
    
    consecutive_failures = 0
    
    while True:
        try:
            bitmex_status = "Connecting to BitMEX..."
            bitmex_ws = websocket.WebSocketApp(
                "wss://ws.bitmex.com/realtime",
                on_message=bitmex_on_message,
                on_error=bitmex_on_error,
                on_close=bitmex_on_close,
                on_open=bitmex_on_open
            )
            bitmex_ws.run_forever(ping_interval=30, ping_timeout=20)
            
            consecutive_failures += 1
            bitmex_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            bitmex_status = f"Reconnecting in {bitmex_reconnect_delay}s..."
            time.sleep(bitmex_reconnect_delay)
            
        except Exception as e:
            consecutive_failures += 1
            bitmex_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            bitmex_status = f"Error. Retry in {bitmex_reconnect_delay}s"
            time.sleep(bitmex_reconnect_delay)


# ============== BITFINEX HANDLERS ==============

def bitfinex_on_message(ws, message):
    """Handle Bitfinex WebSocket messages"""
    global bitfinex_status
    try:
        data = json.loads(message)
        
        # Handle subscription confirmation
        if isinstance(data, dict) and data.get('event') == 'subscribed':
            bitfinex_status = "Connected & Subscribed"
            return
        
        # Handle trade data (comes as array)
        if isinstance(data, list) and len(data) > 1:
            # Check if it's a trade update [CHANNEL_ID, 'te', [ID, MTS, AMOUNT, PRICE]]
            if data[1] == 'te' and isinstance(data[2], list):
                trade_data = data[2]
                timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
                amount = float(trade_data[2])
                price = float(trade_data[3])
                
                # Positive amount = buy, negative = sell
                side = 'Buy' if amount > 0 else 'Sell'
                amount_abs = abs(amount)
                
                trade_info = {
                    'text': f"{timestamp}  {side:4}  ${price:>11,.2f}  {amount_abs:>10.4f}",
                    'side': side
                }
                bitfinex_trades.append(trade_info)
                bitfinex_status = f"Live - {len(bitfinex_trades)} trades"
                
    except Exception as e:
        bitfinex_trades.append({
            'text': f"Error: {str(e)}",
            'side': 'Error'
        })


def bitfinex_on_error(ws, error):
    """Handle Bitfinex WebSocket errors"""
    global bitfinex_status
    bitfinex_status = f"Error: {str(error)}"


def bitfinex_on_close(ws, close_status_code, close_msg):
    """Handle Bitfinex WebSocket close"""
    global bitfinex_status
    bitfinex_status = "Disconnected"


def bitfinex_on_open(ws):
    """Subscribe to Bitfinex trades"""
    global bitfinex_status, bitfinex_reconnect_delay
    bitfinex_status = "Subscribing..."
    bitfinex_reconnect_delay = 5
    bitfinex_trades.append({
        'text': "Connected to Bitfinex",
        'side': 'Info'
    })
    
    # Subscribe to BTCUSD trades
    subscribe_msg = {
        "event": "subscribe",
        "channel": "trades",
        "symbol": "tBTCUSD"
    }
    ws.send(json.dumps(subscribe_msg))


def bitfinex_websocket_thread():
    """Run Bitfinex WebSocket in a separate thread"""
    global bitfinex_ws, bitfinex_status, bitfinex_reconnect_delay
    
    consecutive_failures = 0
    
    while True:
        try:
            bitfinex_status = "Connecting to Bitfinex..."
            bitfinex_ws = websocket.WebSocketApp(
                "wss://api-pub.bitfinex.com/ws/2",
                on_message=bitfinex_on_message,
                on_error=bitfinex_on_error,
                on_close=bitfinex_on_close,
                on_open=bitfinex_on_open
            )
            bitfinex_ws.run_forever()
            
            consecutive_failures += 1
            bitfinex_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            bitfinex_status = f"Reconnecting in {bitfinex_reconnect_delay}s..."
            time.sleep(bitfinex_reconnect_delay)
            
        except Exception as e:
            consecutive_failures += 1
            bitfinex_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            bitfinex_status = f"Error. Retry in {bitfinex_reconnect_delay}s"
            time.sleep(bitfinex_reconnect_delay)


# ============== COINBASE HANDLERS ==============

def coinbase_on_message(ws, message):
    """Handle Coinbase WebSocket messages"""
    global coinbase_status
    try:
        data = json.loads(message)
        
        # Handle subscription confirmation
        if data.get('type') == 'subscriptions':
            coinbase_status = "Connected & Subscribed"
            return
        
        # Handle match/trade data
        if data.get('type') == 'match':
            timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
            side = data.get('side', 'unknown').capitalize()
            price = float(data.get('price', 0))
            size = float(data.get('size', 0))
            
            trade_info = {
                'text': f"{timestamp}  {side:4}  ${price:>11,.2f}  {size:>10.4f}",
                'side': 'Buy' if side == 'Buy' else 'Sell'
            }
            coinbase_trades.append(trade_info)
            coinbase_status = f"Live - {len(coinbase_trades)} trades"
                
    except Exception as e:
        coinbase_trades.append({
            'text': f"Error: {str(e)}",
            'side': 'Error'
        })


def coinbase_on_error(ws, error):
    """Handle Coinbase WebSocket errors"""
    global coinbase_status
    coinbase_status = f"Error: {str(error)}"


def coinbase_on_close(ws, close_status_code, close_msg):
    """Handle Coinbase WebSocket close"""
    global coinbase_status
    coinbase_status = "Disconnected"


def coinbase_on_open(ws):
    """Subscribe to Coinbase trades"""
    global coinbase_status, coinbase_reconnect_delay
    coinbase_status = "Subscribing..."
    coinbase_reconnect_delay = 5
    coinbase_trades.append({
        'text': "Connected to Coinbase",
        'side': 'Info'
    })
    
    # Subscribe to BTC-USD matches (trades)
    subscribe_msg = {
        "type": "subscribe",
        "product_ids": ["BTC-USD"],
        "channels": ["matches"]
    }
    ws.send(json.dumps(subscribe_msg))


def coinbase_websocket_thread():
    """Run Coinbase WebSocket in a separate thread"""
    global coinbase_ws, coinbase_status, coinbase_reconnect_delay
    
    consecutive_failures = 0
    
    while True:
        try:
            coinbase_status = "Connecting to Coinbase..."
            coinbase_ws = websocket.WebSocketApp(
                "wss://ws-feed.exchange.coinbase.com",
                on_message=coinbase_on_message,
                on_error=coinbase_on_error,
                on_close=coinbase_on_close,
                on_open=coinbase_on_open
            )
            coinbase_ws.run_forever()
            
            consecutive_failures += 1
            coinbase_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            coinbase_status = f"Reconnecting in {coinbase_reconnect_delay}s..."
            time.sleep(coinbase_reconnect_delay)
            
        except Exception as e:
            consecutive_failures += 1
            coinbase_reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            coinbase_status = f"Error. Retry in {coinbase_reconnect_delay}s"
            time.sleep(coinbase_reconnect_delay)


# ============== UI FUNCTIONS ==============

def draw_rectangle(stdscr, y, x, height, width):
    """Draw a rectangle border"""
    # Top border
    stdscr.addch(y, x, curses.ACS_ULCORNER)
    stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
    for i in range(1, width - 1):
        stdscr.addch(y, x + i, curses.ACS_HLINE)
    
    # Bottom border
    stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
    stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
    for i in range(1, width - 1):
        stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE)
    
    # Side borders
    for i in range(1, height - 1):
        stdscr.addch(y + i, x, curses.ACS_VLINE)
        stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE)


def main(stdscr):
    """Main terminal UI function"""
    # Initial setup
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(1)  # Non-blocking input
    
    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # Buy - Green
    curses.init_pair(2, curses.COLOR_RED, -1)     # Sell - Red
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Info - Yellow
    curses.init_pair(4, curses.COLOR_CYAN, -1)    # Header - Cyan
    curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Chat - Magenta
    
    # Start WebSocket threads
    binance_thread = threading.Thread(target=binance_websocket_thread, daemon=True)
    bitmex_thread = threading.Thread(target=bitmex_websocket_thread, daemon=True)
    bitfinex_thread = threading.Thread(target=bitfinex_websocket_thread, daemon=True)
    coinbase_thread = threading.Thread(target=coinbase_websocket_thread, daemon=True)
    binance_thread.start()
    bitmex_thread.start()
    bitfinex_thread.start()
    coinbase_thread.start()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Calculate rectangle dimensions
    rect_height = height - 4
    rect_width = width - 4
    rect_y = 2
    rect_x = 2
    
    # Calculate split points (divide into 5 equal sections)
    section_width = rect_width // 5
    split1_x = rect_x + section_width
    split2_x = rect_x + 2 * section_width
    split3_x = rect_x + 3 * section_width
    split4_x = rect_x + 4 * section_width
    
    # Draw static elements
    title = "Crypto Terminal - Binance | BitMEX | Order Book | Bitfinex | Coinbase"
    stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
    
    # Draw rectangle border
    draw_rectangle(stdscr, rect_y, rect_x, rect_height, rect_width)
    
    # Draw vertical separators
    for i in range(1, rect_height - 1):
        stdscr.addch(rect_y + i, split1_x, curses.ACS_VLINE)
        stdscr.addch(rect_y + i, split2_x, curses.ACS_VLINE)
        stdscr.addch(rect_y + i, split3_x, curses.ACS_VLINE)
        stdscr.addch(rect_y + i, split4_x, curses.ACS_VLINE)
    stdscr.addch(rect_y, split1_x, curses.ACS_TTEE)
    stdscr.addch(rect_y + rect_height - 1, split1_x, curses.ACS_BTEE)
    stdscr.addch(rect_y, split2_x, curses.ACS_TTEE)
    stdscr.addch(rect_y + rect_height - 1, split2_x, curses.ACS_BTEE)
    stdscr.addch(rect_y, split3_x, curses.ACS_TTEE)
    stdscr.addch(rect_y + rect_height - 1, split3_x, curses.ACS_BTEE)
    stdscr.addch(rect_y, split4_x, curses.ACS_TTEE)
    stdscr.addch(rect_y + rect_height - 1, split4_x, curses.ACS_BTEE)
    
    # Section headers
    col1_header = "BINANCE"
    col2_header = "BITMEX"
    col3_header = "ORDER BOOK"
    col4_header = "BITFINEX"
    col5_header = "COINBASE"
    
    col_width = section_width - 2
    
    stdscr.addstr(rect_y + 1, rect_x + max(0, (col_width - len(col1_header)) // 2) + 2, 
                  col1_header, curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(rect_y + 1, split1_x + max(0, (col_width - len(col2_header)) // 2) + 2, 
                  col2_header, curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(rect_y + 1, split2_x + max(0, (col_width - len(col3_header)) // 2) + 2, 
                  col3_header, curses.color_pair(5) | curses.A_BOLD)
    stdscr.addstr(rect_y + 1, split3_x + max(0, (col_width - len(col4_header)) // 2) + 2, 
                  col4_header, curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(rect_y + 1, split4_x + max(0, (col_width - len(col5_header)) // 2) + 2, 
                  col5_header, curses.color_pair(4) | curses.A_BOLD)
    
    # Instructions
    instructions = "Press 'q' to quit"
    stdscr.addstr(height - 1, max(0, (width - len(instructions)) // 2), instructions)
    
    display_height = rect_height - 4
    start_line = rect_y + 3
    
    last_binance_count = 0
    last_bitmex_count = 0
    last_trollbox_count = 0
    last_bitfinex_count = 0
    last_coinbase_count = 0
    
    while True:
        try:
            # Update status line
            status = f"Binance: {binance_status} | BitMEX: {bitmex_status} | Bitfinex: {bitfinex_status} | Coinbase: {coinbase_status}"
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            if len(status) <= width:
                stdscr.addstr(1, max(0, (width - len(status)) // 2), status, curses.color_pair(3))
            else:
                stdscr.addstr(1, 0, status[:width], curses.color_pair(3))
            
            # Update Binance trades (column 1)
            current_binance = len(binance_trades)
            if current_binance != last_binance_count or current_binance > 0:
                for i in range(display_height):
                    stdscr.move(start_line + i, rect_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                
                trades_to_show = list(binance_trades)[-display_height:]
                for i, trade_info in enumerate(trades_to_show):
                    if i < display_height:
                        display_text = trade_info['text'][:col_width - 2]
                        color = curses.color_pair(1) if trade_info.get('side') == 'Buy' else curses.color_pair(2)
                        if trade_info.get('side') not in ['Buy', 'Sell']:
                            color = curses.color_pair(3)
                        try:
                            stdscr.addstr(start_line + i, rect_x + 2, display_text, color)
                        except:
                            pass
                last_binance_count = current_binance
            
            # Update BitMEX trades (column 2)
            current_bitmex = len(bitmex_trades)
            if current_bitmex != last_bitmex_count or current_bitmex > 0:
                for i in range(display_height):
                    stdscr.move(start_line + i, split1_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                
                trades_to_show = list(bitmex_trades)[-display_height:]
                for i, trade_info in enumerate(trades_to_show):
                    if i < display_height:
                        display_text = trade_info['text'][:col_width - 2]
                        color = curses.color_pair(1) if trade_info.get('side') == 'Buy' else curses.color_pair(2)
                        if trade_info.get('side') not in ['Buy', 'Sell']:
                            color = curses.color_pair(3)
                        try:
                            stdscr.addstr(start_line + i, split1_x + 2, display_text, color)
                        except:
                            pass
                last_bitmex_count = current_bitmex
            
            # Update Trollbox messages (column 3)
            current_trollbox = len(trollbox_messages)
            if current_trollbox != last_trollbox_count or current_trollbox > 0:
                for i in range(display_height):
                    stdscr.move(start_line + i, split2_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                
                messages_to_show = list(trollbox_messages)[-display_height:]
                for i, msg_info in enumerate(messages_to_show):
                    if i < display_height:
                        display_text = msg_info['text'][:col_width - 2]
                        try:
                            stdscr.addstr(start_line + i, split2_x + 2, display_text, curses.color_pair(5))
                        except:
                            pass
                last_trollbox_count = current_trollbox
            
            # Update Bitfinex trades (column 4)
            current_bitfinex = len(bitfinex_trades)
            if current_bitfinex != last_bitfinex_count or current_bitfinex > 0:
                for i in range(display_height):
                    stdscr.move(start_line + i, split3_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                
                trades_to_show = list(bitfinex_trades)[-display_height:]
                for i, trade_info in enumerate(trades_to_show):
                    if i < display_height:
                        display_text = trade_info['text'][:col_width - 2]
                        color = curses.color_pair(1) if trade_info.get('side') == 'Buy' else curses.color_pair(2)
                        if trade_info.get('side') not in ['Buy', 'Sell']:
                            color = curses.color_pair(3)
                        try:
                            stdscr.addstr(start_line + i, split3_x + 2, display_text, color)
                        except:
                            pass
                last_bitfinex_count = current_bitfinex
            
            # Update Coinbase trades (column 5)
            current_coinbase = len(coinbase_trades)
            if current_coinbase != last_coinbase_count or current_coinbase > 0:
                for i in range(display_height):
                    stdscr.move(start_line + i, split4_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                
                trades_to_show = list(coinbase_trades)[-display_height:]
                for i, trade_info in enumerate(trades_to_show):
                    if i < display_height:
                        display_text = trade_info['text'][:col_width - 2]
                        color = curses.color_pair(1) if trade_info.get('side') == 'Buy' else curses.color_pair(2)
                        if trade_info.get('side') not in ['Buy', 'Sell']:
                            color = curses.color_pair(3)
                        try:
                            stdscr.addstr(start_line + i, split4_x + 2, display_text, color)
                        except:
                            pass
                last_coinbase_count = current_coinbase
            
            stdscr.refresh()
            
            # Check for quit key
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                if binance_ws:
                    binance_ws.close()
                if bitmex_ws:
                    bitmex_ws.close()
                if bitfinex_ws:
                    bitfinex_ws.close()
                if coinbase_ws:
                    coinbase_ws.close()
                break
            
            # Refresh rate
            curses.napms(200)
            
        except KeyboardInterrupt:
            if binance_ws:
                binance_ws.close()
            if bitmex_ws:
                bitmex_ws.close()
            if bitfinex_ws:
                bitfinex_ws.close()
            if coinbase_ws:
                coinbase_ws.close()
            break
        except Exception as e:
            pass


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nApplication closed")
