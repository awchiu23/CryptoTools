# CryptoTools
I created these tools for my crypto arbitrage trading activities.  Enjoy!

---

## CryptoLib
- Library for all other tools

## CryptoParams
- Params for all other tools (e.g., API infos)

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

## CryptoReporter
- This tool is for monitoring your NAVs, positions and risks across:
	- FTX
	- Bybit
	- Binance
	- Deribit
    - Kraken Futures
	- Kraken
	- Coinbase
- For this tool to work without modification, you will need to prepare all of the following:
    - FTX: BTC/ETH/FTT spots; BTC/ETH/FTT perps
    - Bybit: BTC/ETH collaterals and inverse perps
    - Binance: BTC/ETH collaterals and Coin-M perps
    - Deribit: BTC/ETH collaterals and inverse perps
    - Kraken Futures: BTC/ETH collaterals and inverse perps
    - Kraken: BTC spot and BTC margined spot
	- Coinbase: empty is ok
	- For all accounts you will also need to set up APIs
- For a simplified version, there is an **IS_ADVANCED** flag that you can set to False.  Once set, the universe becomes FTX, Bybit and Coinbase only.

## CryptoTrader
- Automated trading of spot and futures
- Whatsapp me if interested

## FTXLender
- This tools runs on a loop and automatically modifies your loan sizes one minute before every reset
- Universe: USD, BTC, ETH

## KrakenTrader
- Execution tool for Kraken to trade BTC margined spot
- Work hedge off other exchanges
