import os
import requests
import yfinance as yf
try:
    import alpaca_trade_api as tradeapi
except ImportError:
    tradeapi = None

class PassiveTradingAgent:
    """Trading agent that looks for trending tickers and applies a
    simple moving average crossover strategy.

    This example is for educational purposes only and does not guarantee profits.
    You must supply valid Alpaca API credentials via environment variables.
    """

    def __init__(self):
        self.key_id = os.getenv('ALPACA_KEY_ID')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_API_BASE', 'https://paper-api.alpaca.markets')
        self.symbols = self.get_trending_tickers()
        if tradeapi:
            self.api = tradeapi.REST(self.key_id, self.secret_key, base_url=self.base_url)
        else:
            self.api = None

    def get_trending_tickers(self, region: str = 'US', limit: int = 5):
        """Fetch trending tickers from Yahoo Finance."""
        url = f'https://query1.finance.yahoo.com/v1/finance/trending/{region}'
        try:
            resp = requests.get(url, timeout=10)
            quotes = resp.json()['finance']['result'][0]['quotes']
            tickers = [q['symbol'] for q in quotes]
        except Exception:
            tickers = ['SPY']
        return tickers[:limit]

    def get_signal(self, symbol: str):
        data = yf.download(symbol, period='1y', interval='1d')
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        data['SMA200'] = data['Close'].rolling(window=200).mean()
        if data['SMA50'].iloc[-1] > data['SMA200'].iloc[-1]:
            return 'buy'
        return 'sell'

    def rebalance(self):
        if self.api is None:
            raise RuntimeError('alpaca_trade_api is required for trading operations')
        for symbol in self.symbols:
            signal = self.get_signal(symbol)
            try:
                position = self.api.get_position(symbol)
                qty = float(position.qty)
            except Exception:
                qty = 0.0
            if signal == 'buy' and qty <= 0:
                self.api.submit_order(symbol=symbol, qty=1, side='buy', type='market', time_in_force='gtc')
            elif signal == 'sell' and qty > 0:
                self.api.submit_order(symbol=symbol, qty=qty, side='sell', type='market', time_in_force='gtc')


def main():
    agent = PassiveTradingAgent()
    agent.rebalance()


if __name__ == '__main__':
    main()
