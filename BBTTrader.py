import CryptoLib as cl
import time

########
# Params
########
nPrograms=5
notional=10000               # USD notional

ccy='MATIC'
current_bbt_buy=3
current_bbt_sell=2
leg1_distance=-3
leg2_distance=0

######
# Init
######
ftx,_,_,_,_,_,qty,notional,spot = cl.ctInit(ccy,notional,0)

######
# Main
######
cl.printHeader('BBTTrader')
bb_buy = cl.bbCCXTInit(current_bbt_buy)
bb_sell = cl.bbCCXTInit(current_bbt_sell)
for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  cl.bbtRelOrder('SELL', bb_sell, ccy, qty, maxChases=888, distance=leg1_distance)
  cl.bbtRelOrder('BUY', bb_buy, ccy, qty, maxChases=888, distance=leg2_distance)
  time.sleep(2)
cl.speak('BBTTrader has completed')