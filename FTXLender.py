import CryptoLib as cl
import pandas as pd
import datetime
import termcolor

########
# Params
########
isRunNow=False            # Run once and stop? Otherwise loop continuously and run one minute before every reset
isManageCoins=True        # Also manage coins (BTC and ETH) in addition to USD?

minRate=0.05              # Minimum rate for all loans
usdLendingRatio=0.9       # Percentage of USD to lend out
coinLendingRatio=0.9      # Percentage of coins (BTC and ETH) to lend out

###########
# Functions
###########
def ftxLend(ftx,ccy,lendingSize,minRate):
  return ftx.private_post_spot_margin_offers({'coin':ccy,'size':lendingSize,'rate':minRate/365/24})

def ftxProcessLoan(ftx,ftxWallet,ccy,lendingRatio,minRate):
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
      z=str(round(lendingSize,1))+' coins (~$'+str(round(lendingSize*(ftxWallet.loc[ccy,'spot'])))+')'
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

  ftxWallet=cl.ftxGetWallet(ftx)
  ftxProcessLoan(ftx, ftxWallet, 'USD', usdLendingRatio, minRate)
  if isManageCoins:
    ftxProcessLoan(ftx, ftxWallet,'BTC', coinLendingRatio, minRate)
    ftxProcessLoan(ftx, ftxWallet,'ETH', coinLendingRatio, minRate)

  if isRunNow:
    break
