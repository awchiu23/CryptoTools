import CryptoLib as cl
import numpy as np
import sys
import os

########
# Params
########
nPrograms=10
side='BUY'
targetUSD=3000
hedgeExchange='none'     # 'ftxspot', 'bb', 'bn', 'kf', 'none'

######
# Init
######
if side == 'BUY':
  oppSide = 'SELL'
elif side == 'SELL':
  oppSide = 'BUY'
else:
  sys.exit(1)

ftx = cl.ftxCCXTInit()
bb = cl.bbCCXTInit()
bn = cl.bnCCXTInit()
kf=cl.kfInit()

ftxWallet=cl.ftxGetWallet(ftx)
spotBTC=ftxWallet.loc['BTC','spot']
trade_btc = np.min([np.min([targetUSD, cl.CT_MAX_NOTIONAL]) / spotBTC, cl.CT_MAX_BTC])
trade_btc_notional = trade_btc * spotBTC

##########################################################
# Simon's mod -- use API2 to not clash with CryptoReporter
##########################################################
if os.environ.get('USERNAME')=='Simon':
  import ccxt
  kr=ccxt.kraken({'apiKey': cl.API_KEY_KR2, 'secret': cl.API_SECRET_KR2, 'enableRateLimit': False})
else:
  kr=cl.krCCXTInit()

######
# Main
######
cl.printHeader('KrakenTrader')

for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  fill=cl.krRelOrder(side,kr,'XXBTZUSD',trade_btc,maxChases=888)
  if hedgeExchange=='ftxspot':
    fill=cl.ftxRelOrder(oppSide,ftx,'BTC/USD',trade_btc,maxChases=888)
  elif hedgeExchange=='bb':
    fill=cl.bbRelOrder(oppSide, bb, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='bn':
    fill=cl.bnRelOrder(oppSide, bn, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='kf':
    fill=cl.kfRelOrder(oppSide, kf, 'BTC', trade_btc_notional, maxChases=888)

cl.speak('KrakenTrader has completed')