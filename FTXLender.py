import CryptoLib as cl
import pandas as pd
import numpy as np
import datetime
import time
import termcolor

########
# Params
########
isRunNow=False          # If true--run once and stop; otherwise loop continuously and run one minute before every reset
usdLendingRatio=.99     # Percentage of USD to lend out
richerLendingRatio=.99  # Percentage of coin (BTC or ETH) with the richer lending rate to lend out
cheaperLendingRatio=.5  # Percentage of coin (BTC or ETH) with the cheaper lending rate to lend out

###########
# Functions
###########
def ftxLend(ftx,ccy,lendingSize):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':lendingSize,'rate':1e-6})

def ftxClearLoans(ftx):
  ftxLend(ftx, 'USD', 0)
  ftxLend(ftx, 'BTC', 0)
  ftxLend(ftx, 'ETH', 0)

def ftxProcessLoan(ftx,ftxWallet,ccy,lendingRatio,estLending=None):
  if estLending is None:
    estLending = cl.ftxGetEstLending(ftx, ccy)
  lendingSize = float(np.max([0, ftxWallet.loc[ccy]['total'] * lendingRatio]))
  print(cl.getCurrentTime() + ': Estimated '+ccy+' lending rate: ' + termcolor.colored(str(round(estLending * 100,1)) + '% p.a.','red'))
  if ccy=='USD':
    z='$' + str(round(lendingSize))
  else:
    z=str(round(lendingSize,4))+' coins (~USD$'+str(round(lendingSize*(ftxWallet.loc[ccy,'usdValue'] / ftxWallet.loc[ccy,'total'])))+')'
  print(cl.getCurrentTime() + ': New '+ccy+' lending size:       '+termcolor.colored(z+' ('+str(round(lendingRatio*100))+'% of balance)','blue'))
  ftxLend(ftx, ccy, lendingSize)
  print()

######
# Main
######
cl.printHeader('FTXLender')
while True:
  if not isRunNow:
    now=datetime.datetime.now()
    if now.minute==59:
      hoursShift=2
    else:
      hoursShift=1
    tgtTime = now - pd.DateOffset(hours=-hoursShift, minutes=now.minute + 1, seconds=now.second, microseconds=now.microsecond)
    cl.sleepUntil(tgtTime.hour,tgtTime.minute,tgtTime.second)

  ftx=cl.ftxCCXTInit()
  print(cl.getCurrentTime() +': Clearing existing loans and sleeping for 5 seconds ....')
  print()
  ftxClearLoans(ftx)
  time.sleep(5)

  ftxWallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  btcEstLending = cl.ftxGetEstLending(ftx, 'BTC')
  ethEstLending = cl.ftxGetEstLending(ftx, 'ETH')
  if btcEstLending > ethEstLending:
    btcLendingRatio = richerLendingRatio
    ethLendingRatio = cheaperLendingRatio
  else:
    btcLendingRatio = cheaperLendingRatio
    ethLendingRatio = richerLendingRatio
  ftxProcessLoan(ftx,ftxWallet,'USD',usdLendingRatio)
  ftxProcessLoan(ftx,ftxWallet,'BTC',btcLendingRatio,estLending=btcEstLending)
  ftxProcessLoan(ftx,ftxWallet,'ETH',ethLendingRatio,estLending=ethEstLending)

  if isRunNow:
    break
  #else:
    #print(cl.getCurrentTime() + ': Sleeping for two minutes ....')
    #time.sleep(120)
    #print(cl.getCurrentTime() + ': Clearing existing loans ....')
    #ftxClearLoans(ftx)
