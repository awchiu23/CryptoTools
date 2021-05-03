import CryptoLib as cl
import numpy as np
import time

########
# Params
########
nPrograms=10
targetUSD=1000

ticker='MATIC'
isSpot=True
isPerp=True
sideSpot='BUY'
sidePerp='SELL'

######
# Init
######
ftx = cl.ftxCCXTInit()
tickerSpot=ticker+'/USD'
tickerPerp=ticker+'-PERP'
spot=cl.ftxGetMid(ftx,tickerSpot)
qty=np.min([targetUSD, cl.CT_MAX_NOTIONAL]) / spot

######
# Main
######
cl.printHeader('FTXTrader')
for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  if isSpot:
    fill=cl.ftxRelOrder(sideSpot,ftx,tickerSpot, qty, maxChases=888)
  if isPerp:
    fill=cl.ftxRelOrder(sidePerp,ftx,tickerPerp, qty, maxChases=888)
  time.sleep(2)
