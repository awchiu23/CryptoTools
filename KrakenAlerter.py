import CryptoLib as cl
import pandas as pd
import time
import termcolor

###########
# Functions
###########
def ftxGetMarkets(ftx):
  return pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')

def ftxGetMid(ftxMarkets, name):
  return (float(ftxMarkets.loc[name, 'bid']) + float(ftxMarkets.loc[name, 'ask'])) / 2

######
# Main
######
cl.printHeader('KrakenAlerter')
ftx=cl.ftxCCXTInit()
kr=cl.krCCXTInit()
while True:
  ftxMarkets = ftxGetMarkets(ftx)
  spotBTC = ftxGetMid(ftxMarkets, 'BTC/USD')
  spot_xxbtzusd = float(kr.public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
  spot_xxbtzeur = float(kr.public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
  spotEUR=float(ftx.public_get_markets_market_name({'market_name':'EUR/USD'})['result']['price'])
  basisUSD=spot_xxbtzusd/spotBTC-1
  basisEUR=spot_xxbtzeur*spotEUR/spotBTC-1
  z='XXBTZUSD:'+str(round(basisUSD*10000)).ljust(10)+'XXBTZEUR: '+str(round(basisEUR*10000))
  print(cl.getCurrentTime().ljust(30)+termcolor.colored(z,'blue'))
  time.sleep(3)