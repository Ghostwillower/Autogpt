"""Simple passive trading agent example.

This module provides a minimal demonstration of how a trading agent might
fetch historical price data and compute a very basic moving‑average
signal.  The example is intentionally simple and meant as a placeholder
for more sophisticated strategies.
"""

from typing import List

import yfinance as yf


class PassiveTradingAgent:
    """Retrieve pricing data and generate a naive trading signal."""

    def __init__(self, symbol: str = "SPY") -> None:
        self.symbol = symbol

    def fetch_prices(self, period: str = "1mo") -> List[float]:
        """Return a list of closing prices for ``symbol``."""

        print(f"[TRADER] Fetching prices for {self.symbol} ({period})")
        data = yf.download(self.symbol, period=period, progress=False)
        closes = data["Close"].tolist()
        return closes

    def moving_average(self, prices: List[float], window: int = 5) -> List[float]:
        """Compute a simple moving average series."""

        if window <= 0:
            raise ValueError("window must be > 0")
        avgs = []
        for i in range(len(prices)):
            if i + 1 < window:
                avgs.append(sum(prices[: i + 1]) / (i + 1))
            else:
                avgs.append(sum(prices[i + 1 - window : i + 1]) / window)
        return avgs

    def run(self) -> None:
        """Fetch prices and print a very naive buy/hold decision."""

        prices = self.fetch_prices()
        ma = self.moving_average(prices, window=5)
        if prices[-1] > ma[-1]:
            action = "BUY"
        else:
            action = "HOLD"
        print(
            f"[TRADER] Latest close: {prices[-1]:.2f}, 5-day MA: {ma[-1]:.2f} -> {action}"
        )


def main():
    agent = PassiveTradingAgent()
    agent.run()


if __name__ == "__main__":
    main()
