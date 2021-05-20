import CryptoLib as cl
from CryptoParams import *
import pandas as pd
import datetime
import termcolor

########
# Params
########
isRunNow=False            # Run once and stop? Otherwise loop continuously and run one minute before every reset
isManageCoins=True        # Also manage coins in addition to USD?

minRate=0.05              # Minimum rate for all loans
usdLendingRatio=1/2       # Percentage of USD to lend out
coinLendingRatio=1/2      # Percentage of coins to lend out

coinsList=CR_FTX_FLOWS_CCYS.copy()
coinsList.remove('USD')
coinsList.remove('USDT')

###########
# Functions
###########
def ftxLend(ftx,ccy,lendingSize,minRate):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':lendingSize,'rate':minRate/365/24})

def ftxProcessLoan(ftx,ccy,lendingRatio,minRate):
  lendable = float(pd.DataFrame(ftx.private_get_spot_margin_lending_info()['result']).set_index('coin')['lendable'][ccy])
  lendingSize = max(0, lendable * lendingRatio)
  if lendable == 0:
    lendingRatio = 0
  else:
    lendingRatio = max(0, lendingSize / lendable)
  estLending = cl.ftxGetEstLending(ftx, ccy)
  print(cl.getCurrentTime() + ': ' + ccy + ' lending rate:    ' + termcolor.colored(str(round(estLending * 100, 1)) + '% p.a.', 'red'))
  if estLending < minRate or lendingSize==0:
    print(cl.getCurrentTime() + ': ' + ccy + ' lending size:    ' + termcolor.colored('*** Not lending ***', 'blue'))
    print()
    ftxLend(ftx, ccy, 0, 0)
  else:
    if ccy=='USD':
      z='$' + str(round(lendingSize))
    else:
      z=str(round(lendingSize,1))+' coins (~$'+str(round(lendingSize*cl.ftxGetMid(ftx,ccy+'/USD')))+')'
    print(cl.getCurrentTime() + ': '+ccy+' lending size:    '+termcolor.colored(z+' ('+str(round(lendingRatio*100))+'% of lendable)','blue'))
    ftxLend(ftx, ccy, lendingSize, minRate)
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

  ftxProcessLoan(ftx, 'USD', usdLendingRatio, minRate)
  if isManageCoins:
    for coin in coinsList:
      ftxProcessLoan(ftx, coin, coinLendingRatio, minRate)

  if isRunNow:
    break
