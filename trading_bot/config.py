import os
from dotenv import load_dotenv

load_dotenv()

SYMBOLS = os.getenv('SYMBOLS', 'BTC/USDT,ETH/USDT,SOL/USDT').split(',')
MIN_PROFIT_PCT = float(os.getenv('MIN_PROFIT_PCT', '0.003'))  # 0.3% minimum after fees
MAX_TRADE_USDT = float(os.getenv('MAX_TRADE_USDT', '100'))
PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
SCAN_INTERVAL = float(os.getenv('SCAN_INTERVAL', '1.0'))

EXCHANGES = {
    'binance': {
        'api_key': os.getenv('BINANCE_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_API_SECRET', ''),
        'taker_fee': 0.001,
    },
    'kraken': {
        'api_key': os.getenv('KRAKEN_API_KEY', ''),
        'api_secret': os.getenv('KRAKEN_API_SECRET', ''),
        'taker_fee': 0.0026,
    },
    'coinbase': {
        'api_key': os.getenv('COINBASE_API_KEY', ''),
        'api_secret': os.getenv('COINBASE_API_SECRET', ''),
        'taker_fee': 0.006,
    },
}
