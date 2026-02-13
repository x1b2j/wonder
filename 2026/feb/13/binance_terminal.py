#!/usr/bin/env python3
"""
Binance Live Trades Terminal Application (Alternative)
Displays real-time trades from Binance in a terminal rectangle
More reliable than BitMEX - no authentication required
"""

import curses
import json
import threading
import websocket
import time
from datetime import datetime
from collections import deque

# Store recent trades with side info for coloring
trades_buffer = deque(maxlen=50)
ws = None
connection_status = "Connecting..."
reconnect_delay = 5  # Start with 5 seconds
max_reconnect_delay = 60  # Cap at 60 seconds


def on_message(ws, message):
    """Handle incoming WebSocket messages"""
    global connection_status
    try:
        data = json.loads(message)
        
        # Binance trade format
        if 'e' in data and data['e'] == 'trade':
            timestamp = datetime.fromtimestamp(data['T'] / 1000).strftime('%H:%M:%S')
            # Determine side based on whether buyer was maker
            side = 'Sell' if data['m'] else 'Buy'
            price = float(data['p'])
            quantity = float(data['q'])
            
            # Store trade with side info for coloring
            trade_info = {
                'text': f"{timestamp} | {side:4} | ${price:>11,.2f} | {quantity:>12,.4f} BTC",
                'side': side
            }
            trades_buffer.append(trade_info)
            connection_status = f"Live - {len(trades_buffer)} trades received"
    except Exception as e:
        trades_buffer.append({
            'text': f"Error: {str(e)}",
            'side': 'Error'
        })


def on_error(ws, error):
    """Handle WebSocket errors"""
    global connection_status
    connection_status = f"Error: {str(error)}"
    trades_buffer.append({
        'text': f"WebSocket Error: {error}",
        'side': 'Error'
    })


def on_close(ws, close_status_code, close_msg):
    """Handle WebSocket close"""
    global connection_status
    connection_status = "Disconnected"


def on_open(ws):
    """Connection opened"""
    global connection_status, reconnect_delay
    connection_status = "Connected - Receiving trades..."
    reconnect_delay = 5  # Reset delay on successful connection
    trades_buffer.append({
        'text': "Connected to Binance WebSocket",
        'side': 'Info'
    })


def websocket_thread():
    """Run WebSocket in a separate thread with auto-reconnect and rate limiting"""
    global ws, connection_status, reconnect_delay
    
    consecutive_failures = 0
    
    while True:
        try:
            connection_status = "Connecting to Binance..."
            
            # Binance WebSocket for BTCUSDT trades (no subscription needed)
            ws = websocket.WebSocketApp(
                "wss://stream.binance.com:9443/ws/btcusdt@trade",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Run with ping/pong to keep connection alive
            ws.run_forever(ping_interval=20, ping_timeout=10)
            
            # If we get here, connection closed
            consecutive_failures += 1
            
            # Exponential backoff: increase delay with each failure
            reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            
            connection_status = f"Reconnecting in {reconnect_delay} seconds... (attempt {consecutive_failures})"
            time.sleep(reconnect_delay)
            
        except Exception as e:
            consecutive_failures += 1
            reconnect_delay = min(5 * (2 ** (consecutive_failures - 1)), max_reconnect_delay)
            connection_status = f"Connection failed. Retry in {reconnect_delay}s (attempt {consecutive_failures})"
            time.sleep(reconnect_delay)


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
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # Buy - Green
    curses.init_pair(2, curses.COLOR_RED, -1)    # Sell - Red
    curses.init_pair(3, curses.COLOR_YELLOW, -1) # Info - Yellow
    curses.init_pair(4, curses.COLOR_CYAN, -1)   # Header - Cyan
    
    # Start WebSocket in background thread
    ws_thread = threading.Thread(target=websocket_thread, daemon=True)
    ws_thread.start()
    
    # Get terminal dimensions (assume they don't change)
    height, width = stdscr.getmaxyx()
    
    # Calculate rectangle dimensions (leave some margin)
    rect_height = height - 4
    rect_width = width - 4
    rect_y = 2
    rect_x = 2
    
    # Draw static elements once
    title = "Binance Live Trades - BTCUSDT"
    stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
    
    # Draw rectangle border
    draw_rectangle(stdscr, rect_y, rect_x, rect_height, rect_width)
    
    # Draw header inside rectangle
    header = "TIME     | SIDE | PRICE           | QUANTITY"
    if rect_width > len(header) + 4:
        stdscr.addstr(rect_y + 1, rect_x + 2, header, curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(rect_y + 2, rect_x + 2, "-" * min(rect_width - 4, len(header)))
    
    # Instructions at bottom
    instructions = "Press 'q' to quit"
    if width > len(instructions):
        stdscr.addstr(height - 1, max(0, (width - len(instructions)) // 2), instructions)
    
    display_height = rect_height - 5  # Space for header and borders
    start_line = rect_y + 3
    last_trade_count = 0
    
    while True:
        try:
            # Only update dynamic content
            
            # Update connection status
            status = f"Status: {connection_status}"
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            stdscr.addstr(1, max(0, (width - len(status)) // 2), status, curses.color_pair(3))
            
            # Only redraw trades if buffer has changed
            current_trade_count = len(trades_buffer)
            if current_trade_count != last_trade_count or current_trade_count > 0:
                # Clear only the trade area
                for i in range(display_height):
                    stdscr.move(start_line + i, rect_x + 2)
                    stdscr.clrtoeol()
                    # Redraw right border that got cleared
                    try:
                        stdscr.addch(start_line + i, rect_x + rect_width - 1, curses.ACS_VLINE)
                    except:
                        pass
                
                # Show most recent trades
                trades_to_show = list(trades_buffer)[-display_height:]
                for i, trade_info in enumerate(trades_to_show):
                    if start_line + i < rect_y + rect_height - 1:
                        # Truncate if too long
                        display_trade = trade_info['text'][:rect_width - 5]
                        
                        # Color based on side
                        if trade_info['side'] == 'Buy':
                            color = curses.color_pair(1)  # Green
                        elif trade_info['side'] == 'Sell':
                            color = curses.color_pair(2)  # Red
                        else:
                            color = curses.color_pair(3)  # Yellow for info/errors
                        
                        try:
                            stdscr.addstr(start_line + i, rect_x + 2, display_trade, color)
                        except:
                            pass  # Ignore if we can't write to that position
                
                last_trade_count = current_trade_count
            
            stdscr.refresh()
            
            # Check for quit key
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                if ws:
                    ws.close()
                break
            
            # Reasonable refresh rate (200ms)
            curses.napms(200)
            
        except KeyboardInterrupt:
            if ws:
                ws.close()
            break
        except Exception as e:
            # Handle any drawing errors gracefully
            pass


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nApplication closed")
