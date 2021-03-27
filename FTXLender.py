import CryptoLib as cl
import pandas as pd
import numpy as np
import datetime
import termcolor

########
# Params
########
isRunNow=False           # Run once and stop? Otherwise loop continuously and run one minute before every reset
isManageCoins=True       # Also manage coins (BTC and ETH) in addition to USD?

usdLendingRatio=1        # Percentage of USD to lend out
extraCushion=0           # Extra cushion (quoted in $) to bar from lending when managing coins

###########
# Functions
###########
def ftxLend(ftx,ccy,lendingSize):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':lendingSize,'rate':1e-6})

def ftxProcessLoan(ftx,ftxWallet,ccy,lendingRatio):
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
    ftxInfo = ftx.private_get_account()['result']
    collateralUsed=pd.DataFrame(ftxInfo['positions'])['collateralUsed'].sum()
    cushion =collateralUsed*5+extraCushion
    #####
    if cl.ftxGetEstLending(ftx, 'BTC') > cl.ftxGetEstLending(ftx, 'ETH'):
      ccyHigh='BTC'
      ccyLow='ETH'
    else:
      ccyHigh='ETH'
      ccyLow='BTC'
    usdValueHigh=ftxWallet.loc[ccyHigh,'usdValue']
    usdValueLow = ftxWallet.loc[ccyLow, 'usdValue']
    if usdValueLow < cushion:
      lendRatioHigh = 1 - (cushion - usdValueLow) / usdValueHigh
      lendRatioLow = 0
    else:
      lendRatioHigh = 1
      lendRatioLow = 1 - cushion / usdValueLow
    ftxProcessLoan(ftx, ftxWallet, ccyHigh, lendRatioHigh)
    ftxProcessLoan(ftx, ftxWallet, ccyLow, lendRatioLow)

  if isRunNow:
    break
