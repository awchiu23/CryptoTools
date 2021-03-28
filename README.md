# CryptoTools
I created these tools for my own crypto arbitrage trading activities.  Enjoy!

## CryptoLib
- Library for all other tools.
- Replace the defaults with your own API keys.

## CryptoAlerter
- This tool is for monitoring smart basis (as well as raw basis) for various futures.
- Raw basis: premium of future vs. FTX spot
- Smart basis: similar to above but adjusted for these extra factors:
	- Spot rates
	- Basis mean reversion
	- Accrued funding payments
	- Future funding payments

## CryptoReporter
- This tool is for monitoring your NAVs, positions and deltas across:
	- FTX
	- Binance
	- Bybit
	- Coinbase

## CryptoStats
- This tool provides some historical stats sourced through APIs.

## CryptoTrader
- Automated trading of spot and futures.
- Talk to me if you are interested.

## FTXLender
- This tools runs on a loop and automatically modifies your loan sizes one minute before every reset.
- Current universe: USD, BTC, ETH