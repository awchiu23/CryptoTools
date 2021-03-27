import CryptoLib as cl
import pandas as pd
import numpy as np
import datetime
import sys
import time
from retrying import retry
import termcolor

########
# Params
########
isRunNow=False  # If true--run once and stop; otherwise loop continuously and run one minute before every reset
usdLoanRatio=1
btcLoanRatio=.9
ethLoanRatio=.9

###########
# Functions
###########
@retry(wait_fixed=1000)
def ftxLend(ftx,ccy,loanSize):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':loanSize,'rate':1e-6})

def ftxProcessLoan(ftx,ftxWallet,ccy,loanRatio):
  loanSize = float(np.max([0, ftxWallet.loc[ccy]['availableWithoutBorrow'] * loanRatio]))
  estLoanRate=cl.ftxGetEstLending(ftx,ccy)
  print(cl.getCurrentTime() + ': Estimated '+ccy+' loan rate: ' + termcolor.colored(str(round(estLoanRate * 100,1)) + '% p.a.','red'))
  if ccy=='USD':
    z='$' + str(round(loanSize))
  else:
    z=str(round(loanSize,4))+' coins (~USD$'+str(round(loanSize*(ftxWallet.loc[ccy,'usdValue'] / ftxWallet.loc[ccy,'total'])))+')'
  print(cl.getCurrentTime() + ': New '+ccy+' loan size:       '+termcolor.colored(z+' ('+str(round(loanRatio*100,1))+'% of available)','blue'))
  result = ftxLend(ftx, ccy, loanSize)
  print()
  if not result['success']:
    sys.exit(1)

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

  print('Clearing existing loans ....')
  ftxLend(ftx, 'USD', 0)
  ftxLend(ftx, 'BTC', 0)
  ftxLend(ftx, 'ETH', 0)
  print('Waiting 10 seconds ....')
  time.sleep(10)

  ftxWallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  ftxProcessLoan(ftx,ftxWallet,'USD',usdLoanRatio)
  ftxProcessLoan(ftx,ftxWallet,'BTC',btcLoanRatio)
  ftxProcessLoan(ftx,ftxWallet,'ETH',ethLoanRatio)

  if isRunNow:
    break