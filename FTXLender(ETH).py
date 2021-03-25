import CryptoLib as cl
import pandas as pd
import numpy as np
import datetime
import sys
from retrying import retry

########
# Params
########
isRunNow=False   # If true--run once and stop; otherwise loop continuously and run one minute before every reset
loanRatio=.95    # Percentage of positive ETH balance to lend out
minRate=0.05     # Minimum rate p.a. to lend out at

###########
# Functions
###########
@retry(wait_fixed=1000)
def ftxLendETH(ftx,loanSize):
  return ftx.private_post_spot_margin_offers({'coin':'ETH','size':loanSize,'rate':minRate/365/24})

######
# Main
######
cl.printHeader('FTXLender(ETH)')
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
  wallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  loanSize = float(np.max([0,round(wallet.loc['ETH']['total']*loanRatio)]))

  print(cl.getCurrentTime()+': Estimated ETH loan rate: '+str(round(cl.ftxGetEstLending(ftx)*100))+'% p.a.')
  print(cl.getCurrentTime()+': Modifying loan size to '+str(loanSize)+' coins .... ',end='')
  result=ftxLendETH(ftx,loanSize)
  if result['success']:
    print('Success')
  else:
    print('Failed')
    sys.exit(1)
  print()
  if isRunNow:
    break