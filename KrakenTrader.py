import CryptoLib as cl
import numpy as np

side='BUY'
trade_btc_notional=3000
maxChases=888

######
# Main
######
ftx = cl.ftxCCXTInit()
kr=cl.krCCXTInit()
ftxWallet=cl.ftxGetWallet(ftx)
spotBTC=ftxWallet.loc['BTC','spot']
trade_btc = np.min([np.min([trade_btc_notional, cl.CT_MAX_NOTIONAL]) / spotBTC, cl.CT_MAX_BTC])
cl.krRelOrder(side,kr,'BTC',trade_btc,maxChases=maxChases)