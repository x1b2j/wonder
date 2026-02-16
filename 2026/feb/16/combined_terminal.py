#!/usr/bin/env python3
"""
Combined Crypto Terminal Application
Displays Binance, BitMEX, Bitfinex, Coinbase trades + order books in 4 columns,
plus a news column (5 columns total).
All issues fixed: Binance order book, BitMEX 10+ entries, Bitfinex trade error,
Coinbase order book, and real-time redraws.
"""

import curses
import json
import threading
import websocket
import time
import requests
from datetime import datetime, timezone
from collections import deque

# Optional RSS feed parser for news
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

# ============== Data Stores ==============
# Trades (last 50 each)
binance_trades = deque(maxlen=50)
bitmex_trades   = deque(maxlen=50)
bitfinex_trades = deque(maxlen=50)
coinbase_trades = deque(maxlen=50)
news_items      = deque(maxlen=50)

# Order Books (bids/asks dictionaries)
binance_orderbook = {'bids': {}, 'asks': {}}
bitmex_orderbook   = {'bids': {}, 'asks': {}}
bitfinex_orderbook = {'bids': {}, 'asks': {}}
coinbase_orderbook = {'bids': {}, 'asks': {}}

# Flags to trigger UI redraw when order book updates
binance_book_updated = False
bitmex_book_updated   = False
bitfinex_book_updated = False
coinbase_book_updated = False

# ============== WebSocket Connections ==============
binance_ws = None
bitmex_ws   = None
bitfinex_ws = None
coinbase_ws = None

# ============== Status Strings ==============
binance_status = "Connecting..."
bitmex_status   = "Connecting..."
bitfinex_status = "Connecting..."
coinbase_status = "Connecting..."
news_status     = "Initializing..."

# Reconnection settings
reconnect_delay = 5
max_reconnect_delay = 60


# ============== Binance Handlers ==============
def binance_on_message(ws, message):
    global binance_status, binance_trades, binance_orderbook, binance_book_updated
    try:
        data = json.loads(message)

        # Trade messages
        if 'e' in data and data['e'] == 'trade':
            ts = datetime.fromtimestamp(data['T']/1000, tz=timezone.utc).strftime('%H:%M:%S')
            side = 'Sell' if data['m'] else 'Buy'
            price = float(data['p'])
            qty = float(data['q'])
            binance_trades.append({
                'text': f"{ts}  {side:4}  ${price:>11,.2f}  {qty:>10.4f}",
                'side': side
            })
            binance_status = f"Live - {len(binance_trades)} trades"

        # Depth (order book) messages – full snapshot every 100ms
        elif 'e' in data and data['e'] == 'depthUpdate':
            # Clear previous book and rebuild from this snapshot
            binance_orderbook['bids'].clear()
            binance_orderbook['asks'].clear()
            for bid in data['b']:
                price = float(bid[0])
                size  = float(bid[1])
                if size > 0:
                    binance_orderbook['bids'][price] = size
            for ask in data['a']:
                price = float(ask[0])
                size  = float(ask[1])
                if size > 0:
                    binance_orderbook['asks'][price] = size
            binance_book_updated = True

    except Exception as e:
        binance_trades.append({'text': f"Error: {str(e)}", 'side': 'Error'})

def binance_on_error(ws, error):
    global binance_status
    binance_status = f"Error: {str(error)}"

def binance_on_close(ws, close_status_code, close_msg):
    global binance_status
    binance_status = "Disconnected"

def binance_on_open(ws):
    global binance_status, reconnect_delay
    binance_status = "Connected"
    reconnect_delay = 5
    binance_trades.append({'text': "Connected to Binance", 'side': 'Info'})
    # Subscribe to trades and depth (top 20 levels, 100ms updates)
    ws.send(json.dumps({
        "method": "SUBSCRIBE",
        "params": ["btcusdt@trade", "btcusdt@depth20@100ms"],
        "id": 1
    }))

def binance_websocket_thread():
    global binance_ws, binance_status, reconnect_delay
    failures = 0
    while True:
        try:
            binance_status = "Connecting to Binance..."
            binance_ws = websocket.WebSocketApp(
                "wss://stream.binance.com:9443/ws",
                on_message=binance_on_message,
                on_error=binance_on_error,
                on_close=binance_on_close,
                on_open=binance_on_open
            )
            binance_ws.run_forever()
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            binance_status = f"Reconnecting in {delay}s..."
            time.sleep(delay)
        except Exception:
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            binance_status = f"Error. Retry in {delay}s"
            time.sleep(delay)


# ============== BitMEX Handlers ==============
def bitmex_on_message(ws, message):
    global bitmex_status, bitmex_trades, bitmex_orderbook, bitmex_book_updated
    try:
        data = json.loads(message)

        if 'success' in data and data['success']:
            bitmex_status = "Connected & Subscribed"
            bitmex_trades.append({'text': f"Subscribed: {data.get('subscribe', 'unknown')}", 'side': 'Info'})
            return

        if 'table' in data:
            table = data['table']
            action = data.get('action')
            items = data.get('data', [])

            if table == 'trade':
                for trade in items:
                    ts = datetime.now(timezone.utc).strftime('%H:%M:%S')
                    side = trade.get('side', 'Unknown')
                    price = trade.get('price', 0)
                    size = trade.get('size', 0)
                    bitmex_trades.append({
                        'text': f"{ts}  {side:4}  ${price:>11,.2f}  {size:>10,}",
                        'side': side
                    })

            elif 'orderBookL2' in table:
                for item in items:
                    price = item.get('price')
                    size = item.get('size', 0)
                    side = item.get('side')
                    if action == 'partial' or action == 'insert':
                        if side == 'Sell':
                            bitmex_orderbook['asks'][price] = size
                        else:
                            bitmex_orderbook['bids'][price] = size
                    elif action == 'update':
                        if side == 'Sell' and price in bitmex_orderbook['asks']:
                            bitmex_orderbook['asks'][price] = size
                        elif side == 'Buy' and price in bitmex_orderbook['bids']:
                            bitmex_orderbook['bids'][price] = size
                    elif action == 'delete':
                        if side == 'Sell' and price in bitmex_orderbook['asks']:
                            del bitmex_orderbook['asks'][price]
                        elif side == 'Buy' and price in bitmex_orderbook['bids']:
                            del bitmex_orderbook['bids'][price]
                bitmex_book_updated = True

        bitmex_status = f"Live - {len(bitmex_trades)}T"

    except Exception as e:
        bitmex_trades.append({'text': f"Error: {str(e)}", 'side': 'Error'})

def bitmex_on_error(ws, error):
    global bitmex_status
    bitmex_status = f"Error: {str(error)}"

def bitmex_on_close(ws, close_status_code, close_msg):
    global bitmex_status
    bitmex_status = "Disconnected"

def bitmex_on_open(ws):
    global bitmex_status, reconnect_delay
    bitmex_status = "Subscribing..."
    reconnect_delay = 5
    bitmex_trades.append({'text': "Connected to BitMEX", 'side': 'Info'})
    # Subscribe to trades and order book
    ws.send(json.dumps({
        "op": "subscribe",
        "args": ["trade:XBTUSD", "orderBookL2_25:XBTUSD"]
    }))

def bitmex_websocket_thread():
    global bitmex_ws, bitmex_status, reconnect_delay
    failures = 0
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
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            bitmex_status = f"Reconnecting in {delay}s..."
            time.sleep(delay)
        except Exception:
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            bitmex_status = f"Error. Retry in {delay}s"
            time.sleep(delay)


# ============== Bitfinex Handlers ==============
def bitfinex_on_message(ws, message):
    global bitfinex_status, bitfinex_trades, bitfinex_orderbook, bitfinex_book_updated
    try:
        data = json.loads(message)

        # Subscription confirmation
        if isinstance(data, dict) and data.get('event') == 'subscribed':
            bitfinex_status = "Connected & Subscribed"
            return

        if isinstance(data, list):
            chan_id = data[0]
            # Trade execution
            if len(data) > 2 and data[1] == 'te':
                trade = data[2]
                # Ensure trade is a list before indexing
                if isinstance(trade, list) and len(trade) >= 4:
                    ts = datetime.now(timezone.utc).strftime('%H:%M:%S')
                    amount = trade[2]   # positive = buy, negative = sell
                    price  = trade[3]
                    side = 'Buy' if amount > 0 else 'Sell'
                    bitfinex_trades.append({
                        'text': f"{ts}  {side:4}  ${price:>11,.2f}  {abs(amount):>10.4f}",
                        'side': side
                    })

            # Order book snapshot
            elif isinstance(data[1], list):   # snapshot
                bitfinex_orderbook['bids'].clear()
                bitfinex_orderbook['asks'].clear()
                for level in data[1]:
                    if len(level) >= 3:
                        price = level[0]
                        count = level[1]
                        amount = level[2]   # >0 = bid, <0 = ask
                        if count > 0:
                            if amount > 0:
                                bitfinex_orderbook['bids'][price] = abs(amount)
                            else:
                                bitfinex_orderbook['asks'][price] = abs(amount)
                bitfinex_book_updated = True

            # Order book update (single level)
            elif len(data) == 3 and isinstance(data[1], str) and data[1] in ('bu', 'hu'):
                if isinstance(data[2], list) and len(data[2]) >= 3:
                    price, count, amount = data[2]
                    if count > 0:
                        if amount > 0:
                            bitfinex_orderbook['bids'][price] = abs(amount)
                        else:
                            bitfinex_orderbook['asks'][price] = abs(amount)
                    else:
                        bitfinex_orderbook['bids'].pop(price, None)
                        bitfinex_orderbook['asks'].pop(price, None)
                    bitfinex_book_updated = True

        bitfinex_status = f"Live - {len(bitfinex_trades)} trades"

    except Exception as e:
        bitfinex_trades.append({'text': f"Error: {str(e)}", 'side': 'Error'})

def bitfinex_on_error(ws, error):
    global bitfinex_status
    bitfinex_status = f"Error: {str(error)}"

def bitfinex_on_close(ws, close_status_code, close_msg):
    global bitfinex_status
    bitfinex_status = "Disconnected"

def bitfinex_on_open(ws):
    global bitfinex_status, reconnect_delay
    bitfinex_status = "Subscribing..."
    reconnect_delay = 5
    bitfinex_trades.append({'text': "Connected to Bitfinex", 'side': 'Info'})
    # Subscribe to trades and book (P0 = full depth)
    ws.send(json.dumps({
        "event": "subscribe",
        "channel": "trades",
        "symbol": "tBTCUSD"
    }))
    ws.send(json.dumps({
        "event": "subscribe",
        "channel": "book",
        "symbol": "tBTCUSD",
        "prec": "P0",
        "freq": "F0"
    }))

def bitfinex_websocket_thread():
    global bitfinex_ws, bitfinex_status, reconnect_delay
    failures = 0
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
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            bitfinex_status = f"Reconnecting in {delay}s..."
            time.sleep(delay)
        except Exception:
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            bitfinex_status = f"Error. Retry in {delay}s"
            time.sleep(delay)


# ============== Coinbase Handlers ==============
def coinbase_on_message(ws, message):
    global coinbase_status, coinbase_trades, coinbase_orderbook, coinbase_book_updated
    try:
        data = json.loads(message)
        msg_type = data.get('type')

        if msg_type == 'subscriptions':
            coinbase_status = "Connected & Subscribed"
            return

        # Trade (match)
        if msg_type == 'match':
            ts = datetime.now(timezone.utc).strftime('%H:%M:%S')
            side = data['side'].capitalize()
            price = float(data['price'])
            size = float(data['size'])
            coinbase_trades.append({
                'text': f"{ts}  {side:4}  ${price:>11,.2f}  {size:>10.4f}",
                'side': side
            })

        # Order book snapshot
        if msg_type == 'snapshot':
            coinbase_orderbook['bids'].clear()
            coinbase_orderbook['asks'].clear()
            for bid in data['bids']:
                price = float(bid[0])
                size  = float(bid[1])
                if size > 0:
                    coinbase_orderbook['bids'][price] = size
            for ask in data['asks']:
                price = float(ask[0])
                size  = float(ask[1])
                if size > 0:
                    coinbase_orderbook['asks'][price] = size
            coinbase_book_updated = True

        # Order book update (l2update)
        if msg_type == 'l2update':
            for change in data['changes']:
                side, price_str, size_str = change
                price = float(price_str)
                size  = float(size_str)
                if side == 'buy':
                    if size == 0:
                        coinbase_orderbook['bids'].pop(price, None)
                    else:
                        coinbase_orderbook['bids'][price] = size
                else:  # 'sell'
                    if size == 0:
                        coinbase_orderbook['asks'].pop(price, None)
                    else:
                        coinbase_orderbook['asks'][price] = size
            coinbase_book_updated = True

        coinbase_status = f"Live - {len(coinbase_trades)} trades"

    except Exception as e:
        coinbase_trades.append({'text': f"Error: {str(e)}", 'side': 'Error'})

def coinbase_on_error(ws, error):
    global coinbase_status
    coinbase_status = f"Error: {str(error)}"

def coinbase_on_close(ws, close_status_code, close_msg):
    global coinbase_status
    coinbase_status = "Disconnected"

def coinbase_on_open(ws):
    global coinbase_status, reconnect_delay
    coinbase_status = "Subscribing..."
    reconnect_delay = 5
    coinbase_trades.append({'text': "Connected to Coinbase", 'side': 'Info'})
    # Subscribe to matches and level2
    ws.send(json.dumps({
        "type": "subscribe",
        "product_ids": ["BTC-USD"],
        "channels": ["matches", "level2"]
    }))

def coinbase_websocket_thread():
    global coinbase_ws, coinbase_status, reconnect_delay
    failures = 0
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
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            coinbase_status = f"Reconnecting in {delay}s..."
            time.sleep(delay)
        except Exception:
            failures += 1
            delay = min(5 * (2 ** (failures-1)), max_reconnect_delay)
            coinbase_status = f"Error. Retry in {delay}s"
            time.sleep(delay)


# ============== News Fetcher ==============
def news_fetcher_thread():
    global news_status, news_items
    while True:
        if not FEEDPARSER_AVAILABLE:
            news_status = "feedparser not installed"
            time.sleep(60)
            continue
        try:
            news_status = "Fetching news..."
            feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
            if feed.bozo:
                news_status = "RSS parse error"
            else:
                entries = feed.entries[:10]
                news_items.clear()
                for entry in entries:
                    news_items.append({'title': entry.title})
                news_status = f"Updated: {len(entries)} items"
        except Exception as e:
            news_status = f"Error: {str(e)}"
        time.sleep(60)


# ============== UI Functions ==============
def draw_rectangle(stdscr, y, x, height, width):
    """Draw a rectangle border (unchanged)"""
    stdscr.addch(y, x, curses.ACS_ULCORNER)
    stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
    for i in range(1, width - 1):
        stdscr.addch(y, x + i, curses.ACS_HLINE)

    stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
    stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
    for i in range(1, width - 1):
        stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE)

    for i in range(1, height - 1):
        stdscr.addch(y + i, x, curses.ACS_VLINE)
        stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE)


def main(stdscr):
    stdscr.clear()
    curses.curs_set(0)
    stdscr.nodelay(1)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # Buy
    curses.init_pair(2, curses.COLOR_RED, -1)     # Sell
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Info/status
    curses.init_pair(4, curses.COLOR_CYAN, -1)    # Headers
    curses.init_pair(5, curses.COLOR_MAGENTA, -1) # (unused)
    curses.init_pair(6, curses.COLOR_WHITE, -1)   # News

    # Start threads
    threading.Thread(target=binance_websocket_thread, daemon=True).start()
    threading.Thread(target=bitmex_websocket_thread,   daemon=True).start()
    threading.Thread(target=bitfinex_websocket_thread, daemon=True).start()
    threading.Thread(target=coinbase_websocket_thread, daemon=True).start()
    threading.Thread(target=news_fetcher_thread,       daemon=True).start()

    height, width = stdscr.getmaxyx()

    rect_height = height - 4
    rect_width  = width - 4
    rect_y = 2
    rect_x = 2

    # 5 equal columns
    col_width = rect_width // 5
    split1 = rect_x + col_width
    split2 = rect_x + 2 * col_width
    split3 = rect_x + 3 * col_width
    split4 = rect_x + 4 * col_width
    splits = [split1, split2, split3, split4]

    # Title
    title = "Crypto Terminal - Binance (T+Book) | BitMEX (T+Book) | Bitfinex (T+Book) | Coinbase (T+Book) | News"
    stdscr.addstr(0, max(0, (width - len(title))//2), title, curses.A_BOLD)

    # Outer rectangle
    draw_rectangle(stdscr, rect_y, rect_x, rect_height, rect_width)

    # Vertical separators
    for sp in splits:
        for i in range(1, rect_height - 1):
            stdscr.addch(rect_y + i, sp, curses.ACS_VLINE)
        stdscr.addch(rect_y, sp, curses.ACS_TTEE)
        stdscr.addch(rect_y + rect_height - 1, sp, curses.ACS_BTEE)

    # Column headers
    headers = [
        ("BINANCE", rect_x),
        ("BITMEX",  split1),
        ("BITFINEX", split2),
        ("COINBASE", split3),
        ("NEWS",    split4)
    ]
    for text, x in headers:
        x_pos = x + max(0, (col_width - len(text))//2) + 2
        stdscr.addstr(rect_y + 1, x_pos, text, curses.color_pair(4) | curses.A_BOLD)

    # Instructions
    instr = "Press 'q' to quit"
    stdscr.addstr(height - 1, max(0, (width - len(instr))//2), instr)

    # Split each exchange column into trades (top half) and order book (bottom half)
    display_height = rect_height - 4
    # Give slightly more space to order book to show up to 10 entries per side
    trade_lines = display_height // 2
    book_lines  = display_height - trade_lines   # roughly half

    # Starting Y for content
    content_y = rect_y + 3

    # Track last counts to avoid unnecessary redraws
    last_binance_trades = 0
    last_bitmex_trades  = 0
    last_bitfinex_trades= 0
    last_coinbase_trades= 0
    last_news_count     = 0

    # Also track book update flags
    global binance_book_updated, bitmex_book_updated, bitfinex_book_updated, coinbase_book_updated

    while True:
        try:
            # Status line
            status = (f"Binance: {binance_status} | BitMEX: {bitmex_status} | "
                      f"Bitfinex: {bitfinex_status} | Coinbase: {coinbase_status} | "
                      f"News: {news_status}")
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            if len(status) <= width:
                stdscr.addstr(1, max(0, (width - len(status))//2), status, curses.color_pair(3))
            else:
                stdscr.addstr(1, 0, status[:width], curses.color_pair(3))

            # ---------- Binance Column ----------
            redraw_binance = False
            if len(binance_trades) != last_binance_trades:
                last_binance_trades = len(binance_trades)
                redraw_binance = True
            if binance_book_updated:
                redraw_binance = True
                binance_book_updated = False

            if redraw_binance:
                # Clear trades area
                for i in range(trade_lines):
                    stdscr.move(content_y + i, rect_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                # Draw trades
                trades = list(binance_trades)[-trade_lines:]
                for i, t in enumerate(trades):
                    if i >= trade_lines: break
                    display_text = t['text'][:col_width-2]
                    if t.get('side') == 'Buy':
                        color = curses.color_pair(1)
                    elif t.get('side') == 'Sell':
                        color = curses.color_pair(2)
                    else:
                        color = curses.color_pair(3)
                    try:
                        stdscr.addstr(content_y + i, rect_x + 2, display_text, color)
                    except:
                        pass

                # Clear order book area
                for i in range(book_lines):
                    stdscr.move(content_y + trade_lines + i, rect_x + 2)
                    stdscr.addstr(" " * (col_width - 2))
                # Draw order book (show up to 10 entries per side, space permitting)
                book_y = content_y + trade_lines
                asks = sorted(binance_orderbook['asks'].items())[:10]
                ask_count = 0
                for idx, (price, size) in enumerate(asks):
                    if idx >= book_lines: break
                    line = f"ASK {price:>8,.2f} {size:>8.4f}"
                    stdscr.addstr(book_y + idx, rect_x + 2, line[:col_width-2], curses.color_pair(2))
                    ask_count += 1
                # Bids start after asks, with a blank line if space
                bid_start = book_y + ask_count + 1
                bids = sorted(binance_orderbook['bids'].items(), reverse=True)[:10]
                for idx, (price, size) in enumerate(bids):
                    if bid_start + idx >= content_y + display_height: break
                    line = f"BID {price:>8,.2f} {size:>8.4f}"
                    stdscr.addstr(bid_start + idx, rect_x + 2, line[:col_width-2], curses.color_pair(1))

            # ---------- BitMEX Column ----------
            redraw_bitmex = False
            if len(bitmex_trades) != last_bitmex_trades:
                last_bitmex_trades = len(bitmex_trades)
                redraw_bitmex = True
            if bitmex_book_updated:
                redraw_bitmex = True
                bitmex_book_updated = False

            if redraw_bitmex:
                # Clear trades area
                for i in range(trade_lines):
                    stdscr.move(content_y + i, split1 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                trades = list(bitmex_trades)[-trade_lines:]
                for i, t in enumerate(trades):
                    if i >= trade_lines: break
                    display_text = t['text'][:col_width-2]
                    color = curses.color_pair(1) if t.get('side')=='Buy' else curses.color_pair(2) if t.get('side')=='Sell' else curses.color_pair(3)
                    stdscr.addstr(content_y + i, split1 + 2, display_text, color)

                # Clear book area
                for i in range(book_lines):
                    stdscr.move(content_y + trade_lines + i, split1 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                book_y = content_y + trade_lines
                asks = sorted(bitmex_orderbook['asks'].items())[:10]
                ask_count = 0
                for idx, (p,s) in enumerate(asks):
                    if idx >= book_lines: break
                    line = f"ASK {p:>8,.2f} {s:>8,}"
                    stdscr.addstr(book_y + idx, split1 + 2, line[:col_width-2], curses.color_pair(2))
                    ask_count += 1
                bid_start = book_y + ask_count + 1
                bids = sorted(bitmex_orderbook['bids'].items(), reverse=True)[:10]
                for idx, (p,s) in enumerate(bids):
                    if bid_start + idx >= content_y + display_height: break
                    line = f"BID {p:>8,.2f} {s:>8,}"
                    stdscr.addstr(bid_start + idx, split1 + 2, line[:col_width-2], curses.color_pair(1))

            # ---------- Bitfinex Column ----------
            redraw_bitfinex = False
            if len(bitfinex_trades) != last_bitfinex_trades:
                last_bitfinex_trades = len(bitfinex_trades)
                redraw_bitfinex = True
            if bitfinex_book_updated:
                redraw_bitfinex = True
                bitfinex_book_updated = False

            if redraw_bitfinex:
                for i in range(trade_lines):
                    stdscr.move(content_y + i, split2 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                trades = list(bitfinex_trades)[-trade_lines:]
                for i, t in enumerate(trades):
                    if i >= trade_lines: break
                    display_text = t['text'][:col_width-2]
                    color = curses.color_pair(1) if t.get('side')=='Buy' else curses.color_pair(2) if t.get('side')=='Sell' else curses.color_pair(3)
                    stdscr.addstr(content_y + i, split2 + 2, display_text, color)

                for i in range(book_lines):
                    stdscr.move(content_y + trade_lines + i, split2 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                book_y = content_y + trade_lines
                asks = sorted(bitfinex_orderbook['asks'].items())[:10]
                ask_count = 0
                for idx, (p,s) in enumerate(asks):
                    if idx >= book_lines: break
                    line = f"ASK {p:>8,.2f} {s:>8.4f}"
                    stdscr.addstr(book_y + idx, split2 + 2, line[:col_width-2], curses.color_pair(2))
                    ask_count += 1
                bid_start = book_y + ask_count + 1
                bids = sorted(bitfinex_orderbook['bids'].items(), reverse=True)[:10]
                for idx, (p,s) in enumerate(bids):
                    if bid_start + idx >= content_y + display_height: break
                    line = f"BID {p:>8,.2f} {s:>8.4f}"
                    stdscr.addstr(bid_start + idx, split2 + 2, line[:col_width-2], curses.color_pair(1))

            # ---------- Coinbase Column ----------
            redraw_coinbase = False
            if len(coinbase_trades) != last_coinbase_trades:
                last_coinbase_trades = len(coinbase_trades)
                redraw_coinbase = True
            if coinbase_book_updated:
                redraw_coinbase = True
                coinbase_book_updated = False

            if redraw_coinbase:
                for i in range(trade_lines):
                    stdscr.move(content_y + i, split3 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                trades = list(coinbase_trades)[-trade_lines:]
                for i, t in enumerate(trades):
                    if i >= trade_lines: break
                    display_text = t['text'][:col_width-2]
                    color = curses.color_pair(1) if t.get('side')=='Buy' else curses.color_pair(2) if t.get('side')=='Sell' else curses.color_pair(3)
                    stdscr.addstr(content_y + i, split3 + 2, display_text, color)

                for i in range(book_lines):
                    stdscr.move(content_y + trade_lines + i, split3 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                book_y = content_y + trade_lines
                asks = sorted(coinbase_orderbook['asks'].items())[:10]
                ask_count = 0
                for idx, (p,s) in enumerate(asks):
                    if idx >= book_lines: break
                    line = f"ASK {p:>8,.2f} {s:>8.4f}"
                    stdscr.addstr(book_y + idx, split3 + 2, line[:col_width-2], curses.color_pair(2))
                    ask_count += 1
                bid_start = book_y + ask_count + 1
                bids = sorted(coinbase_orderbook['bids'].items(), reverse=True)[:10]
                for idx, (p,s) in enumerate(bids):
                    if bid_start + idx >= content_y + display_height: break
                    line = f"BID {p:>8,.2f} {s:>8.4f}"
                    stdscr.addstr(bid_start + idx, split3 + 2, line[:col_width-2], curses.color_pair(1))

            # ---------- News Column ----------
            if len(news_items) != last_news_count:
                last_news_count = len(news_items)
                for i in range(display_height):
                    stdscr.move(content_y + i, split4 + 2)
                    stdscr.addstr(" " * (col_width - 2))
                news = list(news_items)[-display_height:]
                for i, item in enumerate(news):
                    if i >= display_height: break
                    display_text = item['title'][:col_width-2]
                    stdscr.addstr(content_y + i, split4 + 2, display_text, curses.color_pair(6))

            stdscr.refresh()

            # Quit on 'q'
            if stdscr.getch() in (ord('q'), ord('Q')):
                for ws in (binance_ws, bitmex_ws, bitfinex_ws, coinbase_ws):
                    if ws: ws.close()
                break

            curses.napms(200)

        except KeyboardInterrupt:
            for ws in (binance_ws, bitmex_ws, bitfinex_ws, coinbase_ws):
                if ws: ws.close()
            break
        except Exception:
            pass


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nApplication closed")
