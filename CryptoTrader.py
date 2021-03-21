import CryptoLib as cl
import time
import termcolor
import winsound

########
# Params
########
isActivated=True       # Turn on at your own risk!
config='FTX_BTC_SELL'  # Chosen config in CryptoLib

######
# Main
######
if isActivated:
  ftx, bn, bb, futExch, ccy, isSellPrem, premTgtBps, trade_qty, trade_notional = cl.cryptoTraderInit(config)
  for i in range(cl.CT_NPROGRAMS):
    status=0
    while True:
      d = cl.getPremDict(ftx, bn, bb)
      premBps = d[futExch + ccy + 'Prem']*10000
      z=('Program '+str(i+1)+': ').rjust(15)
      if (isSellPrem and premBps>premTgtBps) or (not isSellPrem and premBps<premTgtBps):
        status+=1
        z+=('('+str(status)+') ').rjust(10)
      else:
        status=0
        z+=''.rjust(10)
      z+=termcolor.colored(ccy + ' Premium (' + futExch + '): ' + str(round(premBps)) + 'bps', 'blue')
      print(z.ljust(30).rjust(40).ljust(70) + termcolor.colored('Target: ' + str(round(premTgtBps)) + 'bps', 'red'))
      if status>=cl.CT_NOBS:
        winsound.Beep(3888, 888)
        print()
        if isSellPrem: # i.e., selling premium
          cl.ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty)  # FTX Spot Buy (Maker)
          if futExch=='ftx':
            cl.ftxRelOrder('SELL', ftx, ccy+'-PERP', trade_qty) # FTX Fut Sell (Maker)
          elif futExch=='bn':
            cl.bnMarketOrder('SELL', bn, ccy, trade_notional)  # Binance Fut Sell (Taker)
          else:
            cl.bbRelOrder('SELL', bb, ccy, trade_notional)  # Bybit Fut Sell (Maker)
        else: # i.e., buying premium
          cl.ftxRelOrder('SELL', ftx, ccy+'/USD', trade_qty) # FTX Spot Sell (Maker)
          if futExch=='ftx':
            cl.ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_qty)  # FTX Fut Buy (Maker)
          elif futExch=='bn':
            cl.bnMarketOrder('BUY', bn, ccy, trade_notional) # Binance Fut Buy (Taker)
          else:
            cl.bbRelOrder('BUY', bb, ccy, trade_notional) # Bybit Fut Buy (Maker)
        print(cl.getCurrentTime()+': Done')
        print()
        break
      time.sleep(5)