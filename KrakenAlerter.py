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
  spotEUR = ftxGetMid(ftxMarkets, 'EUR/USD')
  spot_xxbtzusd = float(kr.public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
  spot_xxbtzeur = float(kr.public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
  basisUSD=spot_xxbtzusd/spotBTC-1
  basisEUR=spot_xxbtzeur*spotEUR/spotBTC-1
  z='XXBTZUSD:'+str(round(basisUSD*10000))
  z2='XXBTZEUR: '+str(round(basisEUR*10000))+' (f/x='+str(round(spotEUR,4))+')'
  print(cl.getCurrentTime().ljust(30)+termcolor.colored(z.ljust(25),'blue')+termcolor.colored(z2,'magenta'))
  time.sleep(2)