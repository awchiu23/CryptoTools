import CryptoLib as cl
import time
import numpy as np
import termcolor

########
# Params
########
nPrograms=5
notional=10000               # USD notional

ccy='BTC'
current_bbt_buy=2
current_bbt_sell=1
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
fills_sell = []
fills_buy = []
for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  fills_sell.append(cl.bbtRelOrder('SELL', bb_sell, ccy, qty, maxChases=888, distance=leg1_distance))
  fills_buy.append(cl.bbtRelOrder('BUY', bb_buy, ccy, qty, maxChases=888, distance=leg2_distance))
  time.sleep(2)
avg_fill_sell=np.average(fills_sell)
avg_fill_buy=np.average(fills_buy)
avg_slippage_bps=10000*(avg_fill_buy-avg_fill_sell)/((avg_fill_buy+avg_fill_sell)/2)
print()
print(cl.getCurrentTime() + ': ' + termcolor.colored('Avg realized slippage = ' + str(round(avg_slippage_bps)) + 'bps', 'red'))
cl.speak('BBTTrader has completed')