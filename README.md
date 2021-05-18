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

## BTCAlerter / ETHAlerter / XRPAlerter / FTXAlerter
- These tools are for monitoring smart basis (as well as raw basis) of various futures
- Raw basis: premium of future vs. FTX spot
- Smart basis: same but adjusted for these extras:
	- Spot rates
	- Basis mean reversion
	- Accrued funding payments
	- Future funding payments
- To get this to work, you will first need API keys set up properly in CryptoParams for the following: FTX, Bybit, Binance, Deribit and Kraken Futures

## BTCTrader / ETHTrader / XRPTrader / FTXTrader
- Automated trading of spot and futures
- If interested, please speak with me directly

## CryptoReporter
- This tool is for monitoring NAVs, positions and risks across multiple exchanges
- Please set **CRYPTOTOOLS_MODE** to 0 in CryptoParams.  The tool will then work across FTX and Bybit
- For more advanced users, please speak with me directly

---

## BBTUtil
- This tool lets you drill down into BBT's risk numbers

## BNTUtil
- This tool lets you drill down into BNT's risk numbers

## FTXLender
- This tools runs on a loop and automatically modifies your loan sizes one minute before every reset
- Universe: USD, BTC, ETH, XRP

## KrakenAlerter
- This tool is for monitoring differences of Kraken spots to FTX spots

## KrakenUtil
- This tool provides the following information from your Kraken accounts:
  1. 24H borrow fees
  2. Auto liquidation dates (365-day windows)
  3. Cash balances

## KrakenTrader
- This tool allows you to execute BTC margined spot in Kraken
- Has ability to work hedges off other exchanges
