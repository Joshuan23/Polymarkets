#!/usr/bin/env python3
"""
Crypto Cross-Exchange Arbitrage Bot
------------------------------------
Monitors price differences across Binance, Kraken, and Coinbase.
Executes both legs (buy low / sell high) when net profit exceeds MIN_PROFIT_PCT.

Usage:
    python run_trading_bot.py

Config via .env:
    PAPER_TRADING=true        # Set to false for real orders
    MIN_PROFIT_PCT=0.003      # 0.3% minimum profit after fees
    MAX_TRADE_USDT=100        # Max USDT per trade
    SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
    SCAN_INTERVAL=1.0         # Seconds between scans
"""
from trading_bot.bot import ArbitrageBot

if __name__ == '__main__':
    bot = ArbitrageBot()
    bot.run()
