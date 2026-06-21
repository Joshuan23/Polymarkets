import ccxt
from typing import Dict, Optional


class ExchangeClient:
    def __init__(self, exchange_id: str, api_key: str = '', api_secret: str = '', taker_fee: float = 0.001):
        self.exchange_id = exchange_id
        self.taker_fee = taker_fee

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            if not ticker['bid'] or not ticker['ask']:
                return None
            return {
                'bid': float(ticker['bid']),
                'ask': float(ticker['ask']),
            }
        except Exception:
            return None

    def get_balance(self, currency: str) -> float:
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['free'].get(currency, 0.0))
        except Exception:
            return 0.0

    def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        try:
            return self.exchange.create_market_order(symbol, side, amount)
        except Exception as e:
            print(f"    Order failed on {self.exchange_id}: {e}")
            return None
