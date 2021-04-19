# CryptoTools
I created these tools for my crypto arbitrage trading activities.  Enjoy!

---

## CryptoLib
- Library for all other tools

## CryptoParams
- Params for all other tools (e.g., API keys)

## apophis.py
- Library for accessing Kraken futures
---

## CryptoAlerter
- This tool is for monitoring smart basis (as well as raw basis) of various futures
- Raw basis: premium of future vs. FTX spot
- Smart basis: same but adjusted for these extras:
	- Spot rates
	- Basis mean reversion
	- Accrued funding payments
	- Future funding payments
- To get this to work, you will first need API keys set up properly in CryptoParams for the following: FTX, Bybit, Binance and Kraken Futures

## CryptoReporter
- This tool is for monitoring NAVs, positions and risks across multiple exchanges
- Please set **CR_IS_ADVANCED** to **False** in CryptoParams.  The tool will then work across FTX, Bybit and Coinbase
- For more advanced users, please speak with me directly
  
## CryptoTrader
- Automated trading of spot and futures
- If interested, please speak with me directly

## DeribitAlerter
- This tool is for monitoring smart basis (as well as raw basis) of Deribit futures

## FTXLender
- This tools runs on a loop and automatically modifies your loan sizes one minute before every reset
- Universe: USD, BTC, ETH

## KrakenAlerter
- This tool is for monitoring differences of Kraken spots to FTX spots

## KrakenUtil
- This tool provides the following information from your Kraken accounts:
  1. 24H borrow fees
  2. Auto liquidation dates (365-day windows)

## KrakenTrader
- Execution tool for Kraken to trade BTC margined spot
- Has ability to work hedges off other exchanges
