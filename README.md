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
- This tool is for monitoring your NAVs, positions and risks across:
	- FTX
	- Bybit
	- Binance
	- Deribit
	- Kraken
	- Coinbase
- For this tool to work without modification, you will need to set up accounts in all of the above and have the following prepared:
	- For all accounts except Kraken and Coinbase: positions in BTC and ETH perps
	- For Kraken: a position in BTC spot and a position in BTC margined spot  
	- For FTX: positions in BTC, ETH and FTT spots; a position in FTT perp
	- For all accounts: APIs set up
	- Time for at least one funding payment to have been paid

## CryptoStats
- This tool provides some historical stats sourced through APIs.

## CryptoTrader
- Automated trading of spot and futures.
- Talk to me if you are interested.

## FTXLender
- This tools runs on a loop and automatically modifies your loan sizes one minute before every reset.
- Universe: USD, BTC, ETH

## KrakenTrader
- Execution tool for Kraken to trade BTC margined spot