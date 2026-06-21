from dataclasses import dataclass
from datetime import datetime


@dataclass
class ArbitrageOpportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    buy_fee: float
    sell_fee: float
    profit_pct: float
    trade_size_usdt: float
    estimated_profit_usdt: float
    timestamp: datetime

    def __str__(self):
        return (
            f"[{self.symbol}] Buy {self.buy_exchange} @ ${self.buy_price:,.4f} | "
            f"Sell {self.sell_exchange} @ ${self.sell_price:,.4f} | "
            f"Profit: {self.profit_pct * 100:.3f}% (~${self.estimated_profit_usdt:.4f})"
        )
