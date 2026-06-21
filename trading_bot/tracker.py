import json
import os
from typing import List

from .executor import TradeResult


class PerformanceTracker:
    def __init__(self, log_file: str = 'trades.json'):
        self.log_file = log_file
        self.trades: List[dict] = []
        self.total_profit = 0.0
        self.total_trades = 0
        self.successful_trades = 0
        self._load()

    def _load(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            self.trades = data.get('trades', [])
            self.total_profit = data.get('total_profit', 0.0)
            self.total_trades = data.get('total_trades', 0)
            self.successful_trades = data.get('successful_trades', 0)

    def record(self, result: TradeResult):
        self.total_trades += 1
        if result.success:
            self.successful_trades += 1
            self.total_profit += result.actual_profit

        self.trades.append({
            'timestamp': result.timestamp.isoformat(),
            'symbol': result.opportunity.symbol,
            'buy_exchange': result.opportunity.buy_exchange,
            'sell_exchange': result.opportunity.sell_exchange,
            'buy_price': result.opportunity.buy_price,
            'sell_price': result.opportunity.sell_price,
            'profit_pct': result.opportunity.profit_pct,
            'estimated_profit': result.opportunity.estimated_profit_usdt,
            'actual_profit': result.actual_profit,
            'success': result.success,
            'note': result.note,
        })
        self._save()

    def _save(self):
        with open(self.log_file, 'w') as f:
            json.dump({
                'trades': self.trades[-1000:],  # keep last 1000 trades
                'total_profit': self.total_profit,
                'total_trades': self.total_trades,
                'successful_trades': self.successful_trades,
            }, f, indent=2)

    def print_summary(self):
        win_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        print(f"\n{'=' * 50}")
        print(f"  PERFORMANCE SUMMARY")
        print(f"{'=' * 50}")
        print(f"  Total Trades:    {self.total_trades}")
        print(f"  Successful:      {self.successful_trades} ({win_rate:.1f}%)")
        print(f"  Total P&L:       ${self.total_profit:.4f} USDT")
        print(f"{'=' * 50}\n")
