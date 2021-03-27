import CryptoLib as cl
import pandas as pd
import datetime
import termcolor

########
# Params
########
isRunNow=False           # Run once and stop? Otherwise loop continuously and run one minute before every reset
isManageCoins=True       # Also manage coins (BTC and ETH) in addition to USD?

usdLendingRatio=.95      # Percentage of USD to lend out
coinLendingRatio=.95     # Percentage of coins (BTC and ETH) to lend out

###########
# Functions
###########
def ftxLend(ftx,ccy,lendingSize):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':lendingSize,'rate':1e-6})

def ftxProcessLoan(ftx,ftxWallet,ccy,lendingRatio):
  lendable=pd.DataFrame(ftx.private_get_spot_margin_lending_info()['result']).set_index('coin')['lendable'][ccy]
  lendingSize = max(0,lendable * lendingRatio)
  if lendable==0:
    lendingRatio=0
  else:
    lendingRatio = max(0,lendingSize/lendable)
  print(cl.getCurrentTime() + ': Estimated '+ccy+' lending rate: ' + termcolor.colored(str(round(cl.ftxGetEstLending(ftx, ccy) * 100,1)) + '% p.a.','red'))
  if ccy=='USD':
    z='$' + str(round(lendingSize))
  else:
    z=str(round(lendingSize,4))+' coins (~USD$'+str(round(lendingSize*(ftxWallet.loc[ccy,'usdValue'] / ftxWallet.loc[ccy,'total'])))+')'
  print(cl.getCurrentTime() + ': New '+ccy+' lending size:       '+termcolor.colored(z+' ('+str(round(lendingRatio*100))+'% of lendable)','blue'))
  ftxLend(ftx, ccy, lendingSize)
  print()

######
# Main
######
ftx=cl.ftxCCXTInit()
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

  ftxWallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  ftxProcessLoan(ftx, ftxWallet, 'USD', usdLendingRatio)
  if isManageCoins:
    ftxProcessLoan(ftx, ftxWallet,'BTC', coinLendingRatio)
    ftxProcessLoan(ftx, ftxWallet,'ETH', coinLendingRatio)

  if isRunNow:
    break
