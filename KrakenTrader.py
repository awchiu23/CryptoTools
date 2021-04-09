import CryptoLib as cl
import numpy as np
import sys

########
# Params
########
side='BUY'          # 'BUY', 'SELL'
targetUSD=3000
hedgeExchange='kf'  # 'ftxspot', 'bb', 'kf', 'none'
nPrograms=10

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
kf=cl.kfInit()
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
  cl.printHeader('KrakenTrader Program '+str(n+1))
  fill=cl.krRelOrder(side,kr,'BTC',trade_btc,maxChases=888)
  if hedgeExchange=='ftxspot':
    fill=cl.ftxRelOrder(oppSide,ftx,'BTC/USD',trade_btc,maxChases=888)
  elif hedgeExchange=='bb':
    fill=cl.bbRelOrder(oppSide, bb, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='kf':
    fill=cl.kfRelOrder(oppSide, kf, 'BTC', trade_btc_notional, maxChases=888)

cl.speak('KrakenTrader has completed')