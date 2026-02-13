#!/usr/bin/env python3
"""
BitMEX Live Trades Terminal Application
Displays real-time trades from BitMEX in a terminal rectangle
"""

import curses
import json
import threading
import websocket
import time
from datetime import datetime, timezone
from collections import deque

# Store recent trades with side info for coloring
trades_buffer = deque(maxlen=50)
# Store recent trollbox messages
trollbox_buffer = deque(maxlen=50)
ws = None
connection_status = "Connecting..."
reconnect_delay = 5  # Start with 5 seconds
max_reconnect_delay = 60  # Cap at 60 seconds


def on_message(ws, message):
    """Handle incoming WebSocket messages"""
    global connection_status
    try:
        data = json.loads(message)
        
        # Handle subscription confirmation
        if 'success' in data and data['success']:
            connection_status = "Connected & Subscribed"
            return
            
        # Handle trade data
        if 'table' in data and data['table'] == 'trade':
            if 'data' in data:
                for trade in data['data']:
                    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
                    side = trade.get('side', 'Unknown')
                    price = trade.get('price', 0)
                    size = trade.get('size', 0)
                    
                    # Store trade with side info for coloring
                    trade_info = {
                        'text': f"{timestamp} {side:4} ${price:>9,.2f} {size:>8,}",
                        'side': side
                    }
                    trades_buffer.append(trade_info)
                    
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
                    
                    # Store chat message
                    chat_info = {
                        'text': f"{timestamp} {user}: {message_text}",
                        'user': user
                    }
                    trollbox_buffer.append(chat_info)
                    
        connection_status = f"Live - {len(trades_buffer)} trades, {len(trollbox_buffer)} msgs"
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
    trades_buffer.append({
        'text': "WebSocket connection closed",
        'side': 'Info'
    })


def on_open(ws):
    """Subscribe to trades and trollbox when connection opens"""
    global connection_status, reconnect_delay
    connection_status = "Connected - Subscribing..."
    reconnect_delay = 5  # Reset delay on successful connection
    trades_buffer.append({
        'text': "Connected to BitMEX",
        'side': 'Info'
    })
    # Subscribe to XBTUSD trades and trollbox chat
    subscribe_msg = {
        "op": "subscribe",
        "args": ["trade:XBTUSD", "chat"]
    }
    ws.send(json.dumps(subscribe_msg))
    trades_buffer.append({
        'text': "Subscribed to trades & chat",
        'side': 'Info'
    })


def websocket_thread():
    """Run WebSocket in a separate thread with auto-reconnect and rate limiting"""
    global ws, connection_status, reconnect_delay
    
    consecutive_failures = 0
    
    while True:
        try:
            connection_status = "Connecting to BitMEX..."
            ws = websocket.WebSocketApp(
                "wss://ws.bitmex.com/realtime",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            # Run with longer ping/pong intervals to avoid timeouts
            ws.run_forever(ping_interval=30, ping_timeout=20)
            
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
    curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Chat - Magenta
    
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
    
    # Calculate split point (middle of rectangle)
    split_x = rect_x + rect_width // 2
    
    # Draw static elements once
    title = "BitMEX Live - XBTUSD Trades & Trollbox"
    stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
    
    # Draw rectangle border
    draw_rectangle(stdscr, rect_y, rect_x, rect_height, rect_width)
    
    # Draw vertical separator in middle
    for i in range(1, rect_height - 1):
        stdscr.addch(rect_y + i, split_x, curses.ACS_VLINE)
    stdscr.addch(rect_y, split_x, curses.ACS_TTEE)  # Top T junction
    stdscr.addch(rect_y + rect_height - 1, split_x, curses.ACS_BTEE)  # Bottom T junction
    
    # Left side: Trades
    left_header = "TRADES"
    left_width = split_x - rect_x - 2
    if left_width > len(left_header):
        stdscr.addstr(rect_y + 1, rect_x + (left_width - len(left_header)) // 2 + 2, left_header, curses.color_pair(4) | curses.A_BOLD)
    
    # Right side: Trollbox
    right_header = "TROLLBOX CHAT"
    right_width = rect_x + rect_width - split_x - 2
    if right_width > len(right_header):
        stdscr.addstr(rect_y + 1, split_x + (right_width - len(right_header)) // 2 + 2, right_header, curses.color_pair(5) | curses.A_BOLD)
    
    # Instructions at bottom
    instructions = "Press 'q' to quit"
    if width > len(instructions):
        stdscr.addstr(height - 1, max(0, (width - len(instructions)) // 2), instructions)
    
    display_height = rect_height - 4  # Space for header and borders
    trades_start_line = rect_y + 3
    chat_start_line = rect_y + 3
    
    last_trade_count = 0
    last_chat_count = 0
    
    while True:
        try:
            # Update connection status
            status = f"Status: {connection_status}"
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            stdscr.addstr(1, max(0, (width - len(status)) // 2), status, curses.color_pair(3))
            
            # Update trades (left side)
            current_trade_count = len(trades_buffer)
            if current_trade_count != last_trade_count or current_trade_count > 0:
                # Clear only the trade area
                for i in range(display_height):
                    stdscr.move(trades_start_line + i, rect_x + 2)
                    stdscr.addstr(" " * (left_width - 2))
                
                # Show most recent trades
                trades_to_show = list(trades_buffer)[-display_height:]
                for i, trade_info in enumerate(trades_to_show):
                    if trades_start_line + i < rect_y + rect_height - 1:
                        display_trade = trade_info['text'][:left_width - 2]
                        
                        # Color based on side
                        if trade_info['side'] == 'Buy':
                            color = curses.color_pair(1)  # Green
                        elif trade_info['side'] == 'Sell':
                            color = curses.color_pair(2)  # Red
                        else:
                            color = curses.color_pair(3)  # Yellow for info/errors
                        
                        try:
                            stdscr.addstr(trades_start_line + i, rect_x + 2, display_trade, color)
                        except:
                            pass
                
                last_trade_count = current_trade_count
            
            # Update trollbox messages (right side)
            current_chat_count = len(trollbox_buffer)
            if current_chat_count != last_chat_count or current_chat_count > 0:
                # Clear only the chat area
                for i in range(display_height):
                    stdscr.move(chat_start_line + i, split_x + 2)
                    stdscr.addstr(" " * (right_width - 2))
                
                # Show most recent chat messages
                chat_to_show = list(trollbox_buffer)[-display_height:]
                for i, chat_info in enumerate(chat_to_show):
                    if chat_start_line + i < rect_y + rect_height - 1:
                        display_chat = chat_info['text'][:right_width - 2]
                        
                        try:
                            stdscr.addstr(chat_start_line + i, split_x + 2, display_chat, curses.color_pair(5))
                        except:
                            pass
                
                last_chat_count = current_chat_count
            
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
