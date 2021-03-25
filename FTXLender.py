import CryptoLib as cl
import pandas as pd
import numpy as np
import datetime
import sys
from retrying import retry

########
# Params
########
isRunNow=False  # If true--run once and stop; otherwise loop continuously and run one minute before every reset
usdLoanRatio=.99
ethLoanRatio=.99

###########
# Functions
###########
@retry(wait_fixed=1000)
def ftxLend(ftx,ccy,loanSize):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':loanSize,'rate':1e-6})

def ftxProcessLoan(ftx,ccy,loanRatio):
  if loanRatio>0:
    wallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
    loanSize = float(np.max([0, round(wallet.loc[ccy]['total'] * loanRatio)]))
    print(cl.getCurrentTime() + ': Estimated '+ccy+' loan rate: ' + str(round(cl.ftxGetEstLending(ftx) * 100)) + '% p.a.')
    z=str(round(loanSize))
    if ccy=='USD':
      z='$' + z
    else:
      z+=' coins'
    print(cl.getCurrentTime() + ': Modifying '+ccy+' loan size to '+z+' ('+str(round(loanRatio*100,1))+'% of balance)')
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
  ftxProcessLoan(ftx,'USD',usdLoanRatio)
  ftxProcessLoan(ftx,'ETH',ethLoanRatio)

  if isRunNow:
    break