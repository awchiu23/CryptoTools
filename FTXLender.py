import CryptoLib as cl
import pandas as pd
import numpy as np
import datetime
import sys

########
# Params
########
isRunNow=False  # If true--run once and stop; otherwise loop continuously and run one minute before every reset
loanRatio=.99   # Percentage of positive USD balance to lend out

######
# Main
######
cl.printHeader('FTXLender')
while True:
  if not isRunNow:
    now=datetime.datetime.now()
    tgtTime=now-pd.DateOffset(hours=-1,minutes=now.minute+1,seconds=now.second,microseconds=now.microsecond)
    cl.sleepUntil(tgtTime.hour,tgtTime.minute,tgtTime.second)
  ftx=cl.ftxCCXTInit()
  wallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  tgtLendSize = np.max(0,round(wallet.loc['USD']['total']*loanRatio))
  print(cl.getCurrentTime()+': Modifying loan size to $'+str(tgtLendSize)+' ....')
  result=ftx.private_post_spot_margin_offers({'coin':'USD','size':tgtLendSize,'rate':1e-6})
  if result['success']:
    print(cl.getCurrentTime()+': Success!')
  else:
    print(cl.getCurrentTime()+': Failed!')
    sys.stop(1)
  print()
  if isRunNow:
    break