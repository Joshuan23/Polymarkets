import signal
import sys
import time
from datetime import datetime
from typing import Dict

from .exchange_client import ExchangeClient
from .executor import TradeExecutor
from .scanner import ArbitrageScanner
from .tracker import PerformanceTracker
from . import config


class ArbitrageBot:
    def __init__(self):
        self.running = False
        self.clients: Dict[str, ExchangeClient] = {}
        self.tracker = PerformanceTracker()
        self._connect_exchanges()
        self.scanner = ArbitrageScanner(self.clients)
        self.executor = TradeExecutor(self.clients)

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _connect_exchanges(self):
        print("Connecting to exchanges...")
        for exchange_id, cfg in config.EXCHANGES.items():
            try:
                client = ExchangeClient(
                    exchange_id=exchange_id,
                    api_key=cfg['api_key'],
                    api_secret=cfg['api_secret'],
                    taker_fee=cfg['taker_fee'],
                )
                self.clients[exchange_id] = client
                print(f"  [OK] {exchange_id} (taker fee: {cfg['taker_fee'] * 100:.2f}%)")
            except Exception as e:
                print(f"  [FAIL] {exchange_id}: {e}")

        if len(self.clients) < 2:
            print("\nERROR: Need at least 2 exchanges connected. Check your config.")
            sys.exit(1)

    def _shutdown(self, signum, frame):
        print("\n\nShutting down...")
        self.running = False
        self.tracker.print_summary()
        sys.exit(0)

    def run(self):
        mode = "PAPER TRADING" if config.PAPER_TRADING else "*** LIVE TRADING ***"
        print(f"\n{'=' * 55}")
        print(f"  CRYPTO ARBITRAGE BOT  [{mode}]")
        print(f"  Symbols:    {', '.join(config.SYMBOLS)}")
        print(f"  Min Profit: {config.MIN_PROFIT_PCT * 100:.2f}% after fees")
        print(f"  Max Trade:  ${config.MAX_TRADE_USDT} USDT per leg")
        print(f"  Exchanges:  {', '.join(self.clients.keys())}")
        print(f"{'=' * 55}")
        print("  Press Ctrl+C to stop\n")

        self.running = True
        scan_count = 0

        while self.running:
            scan_count += 1
            ts = datetime.now().strftime('%H:%M:%S')

            opportunities = self.scanner.scan()

            if opportunities:
                print(f"[{ts}] Scan #{scan_count} — {len(opportunities)} opportunity(s):")
                for opp in opportunities[:3]:
                    print(f"  >> {opp}")
                    result = self.executor.execute(opp)
                    self.tracker.record(result)
                    status = "OK" if result.success else "FAIL"
                    print(f"     [{status}] Actual profit: ${result.actual_profit:.4f} USDT")
            else:
                if scan_count % 10 == 0:
                    print(f"[{ts}] Scan #{scan_count} — no opportunities (threshold: "
                          f"{config.MIN_PROFIT_PCT * 100:.2f}%)")

            time.sleep(config.SCAN_INTERVAL)
