import CryptoLib as cl
import numpy as np
import sys

side='BUY'
trade_btc_notional=5000 # In USD
isHedgeWithFTX=True

######
# Main
######
ftx = cl.ftxCCXTInit()
kr=cl.krCCXTInit()
ftxWallet=cl.ftxGetWallet(ftx)
spotBTC=ftxWallet.loc['BTC','spot']
trade_btc = np.min([np.min([trade_btc_notional, cl.CT_MAX_NOTIONAL]) / spotBTC, cl.CT_MAX_BTC])
fill=cl.krRelOrder(side,kr,'BTC',trade_btc,maxChases=888)

if isHedgeWithFTX:
  if side=='BUY':
    oppSide='SELL'
  elif side=='SELL':
    oppSide='BUY'
  else:
    sys.exit(1)
fill=cl.ftxRelOrder(oppSide,ftx,'BTC',trade_btc,maxChases=888)