from datetime import datetime
from typing import Dict

from .exchange_client import ExchangeClient
from .opportunity import ArbitrageOpportunity
from . import config


class TradeResult:
    def __init__(self, opportunity: ArbitrageOpportunity, success: bool,
                 actual_profit: float = 0.0, note: str = ''):
        self.opportunity = opportunity
        self.success = success
        self.actual_profit = actual_profit
        self.note = note
        self.timestamp = datetime.now()


class TradeExecutor:
    def __init__(self, clients: Dict[str, ExchangeClient]):
        self.clients = clients

    def execute(self, opp: ArbitrageOpportunity) -> TradeResult:
        if config.PAPER_TRADING:
            return self._paper_trade(opp)
        return self._live_trade(opp)

    def _paper_trade(self, opp: ArbitrageOpportunity) -> TradeResult:
        coin_amount = opp.trade_size_usdt / opp.buy_price
        print(f"    [PAPER] BUY  {coin_amount:.6f} {opp.symbol.split('/')[0]} "
              f"on {opp.buy_exchange} @ ${opp.buy_price:,.4f}")
        print(f"    [PAPER] SELL {coin_amount:.6f} {opp.symbol.split('/')[0]} "
              f"on {opp.sell_exchange} @ ${opp.sell_price:,.4f}")
        return TradeResult(opp, success=True, actual_profit=opp.estimated_profit_usdt, note='paper')

    def _live_trade(self, opp: ArbitrageOpportunity) -> TradeResult:
        buy_client = self.clients[opp.buy_exchange]
        sell_client = self.clients[opp.sell_exchange]

        coin_amount = opp.trade_size_usdt / opp.buy_price

        buy_order = buy_client.place_market_order(opp.symbol, 'buy', coin_amount)
        if not buy_order:
            return TradeResult(opp, success=False, note='buy order failed')

        sell_order = sell_client.place_market_order(opp.symbol, 'sell', coin_amount)
        if not sell_order:
            # Critical: we bought but failed to sell. Log loudly.
            print(f"    [CRITICAL] Bought on {opp.buy_exchange} but sell on "
                  f"{opp.sell_exchange} failed — manual intervention required!")
            return TradeResult(opp, success=False, note='sell order failed — unhedged position!')

        actual_buy = float(buy_order.get('average', opp.buy_price))
        actual_sell = float(sell_order.get('average', opp.sell_price))
        buy_cost = coin_amount * actual_buy * (1 + opp.buy_fee)
        sell_proceeds = coin_amount * actual_sell * (1 - opp.sell_fee)
        actual_profit = sell_proceeds - buy_cost

        return TradeResult(opp, success=True, actual_profit=actual_profit, note='live')
