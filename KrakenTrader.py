import CryptoLib as cl
import numpy as np
import sys
import os

########
# Params
########
nPrograms=30
side='BUY'          # 'BUY', 'SELL'
targetUSD=3000
hedgeExchange='bb'  # 'ftxspot', 'bb', 'bn', 'kf', 'none'

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
if os.environ.get('USERNAME')=='Simon':
  import SimonLib as sl
  import ccxt
  kr=ccxt.kraken({'apiKey': sl.jLoad('API_KEY_KR2'), 'secret': sl.jLoad('API_SECRET_KR2'), 'enableRateLimit': False})
else:
  kr=cl.krCCXTInit()
ftxWallet=cl.ftxGetWallet(ftx)
spotBTC=ftxWallet.loc['BTC','spot']
trade_btc = np.min([np.min([targetUSD, cl.CT_MAX_NOTIONAL]) / spotBTC, cl.CT_MAX_BTC])
trade_btc_notional = trade_btc * spotBTC

######
# Main
######
cl.printHeader('KrakenTrader')
print('Note that this tool only handles BTC ....')

for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  fill=cl.krRelOrder(side,kr,'BTC',trade_btc,maxChases=888)
  if hedgeExchange=='ftxspot':
    fill=cl.ftxRelOrder(oppSide,ftx,'BTC/USD',trade_btc,maxChases=888)
  elif hedgeExchange=='bb':
    fill=cl.bbRelOrder(oppSide, bb, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='bn':
    fill=cl.bnRelOrder(oppSide, bn, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='kf':
    fill=cl.kfRelOrder(oppSide, kf, 'BTC', trade_btc_notional, maxChases=888)

cl.speak('KrakenTrader has completed')