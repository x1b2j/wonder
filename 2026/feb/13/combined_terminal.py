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

# WebSocket connections
binance_ws = None
bitmex_ws = None

# Connection status
binance_status = "Connecting..."
bitmex_status = "Connecting..."

# Reconnection settings
binance_reconnect_delay = 5
bitmex_reconnect_delay = 5
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
                for msg in data['data']:
                    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
                    user = msg.get('user', 'Anonymous')
                    message_text = msg.get('message', '')
                    
                    # Truncate long usernames
                    if len(user) > 12:
                        user = user[:12]
                    
                    # Single line format
                    chat_info = {
                        'text': f"{timestamp}  {user}:  {message_text}"
                    }
                    trollbox_messages.append(chat_info)
                    
        bitmex_status = f"Live - {len(bitmex_trades)}T/{len(trollbox_messages)}C"
    except Exception as e:
        bitmex_trades.append({
            'text': f"Error: {str(e)}",
            'side': 'Error'
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
    """Subscribe to BitMEX trades and trollbox"""
    global bitmex_status, bitmex_reconnect_delay
    bitmex_status = "Subscribing..."
    bitmex_reconnect_delay = 5
    bitmex_trades.append({
        'text': "Connected to BitMEX",
        'side': 'Info'
    })
    
    # Subscribe to XBTUSD trades and trollbox chat
    subscribe_msg = {
        "op": "subscribe",
        "args": ["trade:XBTUSD", "chat"]
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
    binance_thread.start()
    bitmex_thread.start()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Calculate rectangle dimensions
    rect_height = height - 4
    rect_width = width - 4
    rect_y = 2
    rect_x = 2
    
    # Calculate split points (divide into 3 equal sections)
    section_width = rect_width // 3
    split1_x = rect_x + section_width
    split2_x = rect_x + 2 * section_width
    
    # Draw static elements
    title = "Crypto Terminal - Binance | BitMEX | Trollbox"
    stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
    
    # Draw rectangle border
    draw_rectangle(stdscr, rect_y, rect_x, rect_height, rect_width)
    
    # Draw vertical separators
    for i in range(1, rect_height - 1):
        stdscr.addch(rect_y + i, split1_x, curses.ACS_VLINE)
        stdscr.addch(rect_y + i, split2_x, curses.ACS_VLINE)
    stdscr.addch(rect_y, split1_x, curses.ACS_TTEE)
    stdscr.addch(rect_y + rect_height - 1, split1_x, curses.ACS_BTEE)
    stdscr.addch(rect_y, split2_x, curses.ACS_TTEE)
    stdscr.addch(rect_y + rect_height - 1, split2_x, curses.ACS_BTEE)
    
    # Section headers
    left_header = "BINANCE BTCUSDT"
    middle_header = "BITMEX XBTUSD"
    right_header = "TROLLBOX"
    
    left_col_width = section_width - 2
    middle_col_width = section_width - 2
    right_col_width = rect_width - 2 * section_width - 2
    
    stdscr.addstr(rect_y + 1, rect_x + max(0, (left_col_width - len(left_header)) // 2) + 2, 
                  left_header, curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(rect_y + 1, split1_x + max(0, (middle_col_width - len(middle_header)) // 2) + 2, 
                  middle_header, curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(rect_y + 1, split2_x + max(0, (right_col_width - len(right_header)) // 2) + 2, 
                  right_header, curses.color_pair(5) | curses.A_BOLD)
    
    # Instructions
    instructions = "Press 'q' to quit"
    stdscr.addstr(height - 1, max(0, (width - len(instructions)) // 2), instructions)
    
    display_height = rect_height - 4
    start_line = rect_y + 3
    
    last_binance_count = 0
    last_bitmex_count = 0
    last_trollbox_count = 0
    
    while True:
        try:
            # Update status line
            status = f"Binance: {binance_status} | BitMEX: {bitmex_status}"
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            stdscr.addstr(1, max(0, (width - len(status)) // 2), status, curses.color_pair(3))
            
            # Update Binance trades (left section) - with spacing
            current_binance = len(binance_trades)
            if current_binance != last_binance_count or current_binance > 0:
                # Clear the section
                for i in range(display_height):
                    stdscr.move(start_line + i, rect_x + 2)
                    stdscr.addstr(" " * (left_col_width - 2))
                
                # Show trades - one per line
                trades_to_show = list(binance_trades)[-display_height:]
                
                for i, trade_info in enumerate(trades_to_show):
                    if i < display_height:
                        display_text = trade_info['text'][:left_col_width - 2]
                        color = curses.color_pair(1) if trade_info.get('side') == 'Buy' else curses.color_pair(2)
                        if trade_info.get('side') not in ['Buy', 'Sell']:
                            color = curses.color_pair(3)
                        try:
                            stdscr.addstr(start_line + i, rect_x + 2, display_text, color)
                        except:
                            pass
                
                last_binance_count = current_binance
            
            # Update BitMEX trades (middle section) - with spacing
            current_bitmex = len(bitmex_trades)
            if current_bitmex != last_bitmex_count or current_bitmex > 0:
                # Clear the section
                for i in range(display_height):
                    stdscr.move(start_line + i, split1_x + 2)
                    stdscr.addstr(" " * (middle_col_width - 2))
                
                # Show trades - one per line
                trades_to_show = list(bitmex_trades)[-display_height:]
                
                for i, trade_info in enumerate(trades_to_show):
                    if i < display_height:
                        display_text = trade_info['text'][:middle_col_width - 2]
                        color = curses.color_pair(1) if trade_info.get('side') == 'Buy' else curses.color_pair(2)
                        if trade_info.get('side') not in ['Buy', 'Sell']:
                            color = curses.color_pair(3)
                        try:
                            stdscr.addstr(start_line + i, split1_x + 2, display_text, color)
                        except:
                            pass
                
                last_bitmex_count = current_bitmex
            
            # Update Trollbox messages (right section) - with spacing
            current_trollbox = len(trollbox_messages)
            if current_trollbox != last_trollbox_count or current_trollbox > 0:
                # Clear the section
                for i in range(display_height):
                    stdscr.move(start_line + i, split2_x + 2)
                    stdscr.addstr(" " * (right_col_width - 2))
                
                # Show messages - one per line
                messages_to_show = list(trollbox_messages)[-display_height:]
                
                for i, msg_info in enumerate(messages_to_show):
                    if i < display_height:
                        display_text = msg_info['text'][:right_col_width - 2]
                        try:
                            stdscr.addstr(start_line + i, split2_x + 2, display_text, curses.color_pair(5))
                        except:
                            pass
                
                last_trollbox_count = current_trollbox
            
            stdscr.refresh()
            
            # Check for quit key
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                if binance_ws:
                    binance_ws.close()
                if bitmex_ws:
                    bitmex_ws.close()
                break
            
            # Refresh rate
            curses.napms(200)
            
        except KeyboardInterrupt:
            if binance_ws:
                binance_ws.close()
            if bitmex_ws:
                bitmex_ws.close()
            break
        except Exception as e:
            pass


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nApplication closed")
