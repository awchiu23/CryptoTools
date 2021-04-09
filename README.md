# CryptoTools
I created these tools for my crypto arbitrage trading activities.  Enjoy!

## CryptoLib
- Library for all other tools
- Replace the defaults with your own API keys
- Set parameters for CryptoTrader

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
	- Kraken
	- Coinbase
- For this tool to work without modification, you will need to set up accounts in all of the above and have the following prepared:
	- For all accounts except Kraken and Coinbase: positions in BTC and ETH perps
	- For Kraken main: a position in BTC spot and a position in BTC margined spot
    - For Kraken futures: positions in BTC and ETH perps 
	- For FTX: positions in BTC, ETH and FTT spots; a position in FTT perp
	- For all accounts: APIs set up
	- Time for at least one funding payment to have been paid
- For a simplified version, there is an **IS_ADVANCED** flag that you can set to False.  Once set, the universe becomes FTX, Bybit and Coinbase only.

## CryptoStats
- This tool provides some historical stats sourced through APIs

## CryptoTrader
- Automated trading of spot and futures
- Whatsapp me if interested

## FTXLender
- This tools runs on a loop and automatically modifies your loan sizes one minute before every reset
- Universe: USD, BTC, ETH

## KrakenTrader
- Execution tool for Kraken to trade BTC margined spot