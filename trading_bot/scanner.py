from datetime import datetime
from typing import Dict, List

from .exchange_client import ExchangeClient
from .opportunity import ArbitrageOpportunity
from . import config


class ArbitrageScanner:
    def __init__(self, clients: Dict[str, ExchangeClient]):
        self.clients = clients

    def scan(self) -> List[ArbitrageOpportunity]:
        opportunities = []
        exchange_names = list(self.clients.keys())

        for symbol in config.SYMBOLS:
            tickers: Dict[str, Dict] = {}
            for name, client in self.clients.items():
                ticker = client.get_ticker(symbol)
                if ticker:
                    tickers[name] = ticker

            if len(tickers) < 2:
                continue

            for buy_exch in exchange_names:
                for sell_exch in exchange_names:
                    if buy_exch == sell_exch:
                        continue
                    if buy_exch not in tickers or sell_exch not in tickers:
                        continue

                    # Buy at the ask on buy_exch, sell at the bid on sell_exch
                    buy_price = tickers[buy_exch]['ask']
                    sell_price = tickers[sell_exch]['bid']

                    buy_fee = self.clients[buy_exch].taker_fee
                    sell_fee = self.clients[sell_exch].taker_fee

                    # Net profit percentage after both legs' fees
                    profit_pct = (sell_price / buy_price) - 1.0 - buy_fee - sell_fee

                    if profit_pct >= config.MIN_PROFIT_PCT:
                        trade_usdt = config.MAX_TRADE_USDT
                        estimated_profit = trade_usdt * profit_pct

                        opportunities.append(ArbitrageOpportunity(
                            symbol=symbol,
                            buy_exchange=buy_exch,
                            sell_exchange=sell_exch,
                            buy_price=buy_price,
                            sell_price=sell_price,
                            buy_fee=buy_fee,
                            sell_fee=sell_fee,
                            profit_pct=profit_pct,
                            trade_size_usdt=trade_usdt,
                            estimated_profit_usdt=estimated_profit,
                            timestamp=datetime.now(),
                        ))

        return sorted(opportunities, key=lambda x: x.profit_pct, reverse=True)
