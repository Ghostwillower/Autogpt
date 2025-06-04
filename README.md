# Autogpt
Autogpt with memory and self determination.

## PassiveTradingAgent

`passive_agent.py` provides a basic example of an autonomous trading bot. It
implements a simple moving average crossover strategy using
[yfinance](https://github.com/ranaroussi/yfinance) for market data and
`alpaca_trade_api` for order execution. The agent also retrieves trending
tickers from Yahoo Finance so it can react to current market interest. API
credentials must be supplied through environment variables. Install the `yfinance`,
`alpaca_trade_api`, and `requests` packages to run the example.
