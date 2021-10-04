import CryptoLib as cl
from CryptoParams import *
import time
import termcolor

########
# Params
########
ccys=['BTC','ETH','FTT','XRP','DOGE','BCH','BNB','LINK','LTC','AAVE','COMP','FTM','MATIC','SOL','SUSHI']
thresholdH = 15
thresholdL = 0
interval = 60*5

######
# Main
######
cl.printHeader('FTXa')
ftx=cl.ftxCCXTInit()
bb= None
bn = None
db = None
kf = None
ku = None
while True:
  print(cl.getCurrentTime(isCondensed=True).ljust(10),end='')
  for i in range(len(ccys)):
    ccy=ccys[i]
    SHARED_CCY_DICT[ccy] = {'futExch': ['ftx']}
    fundingDict = cl.getFundingDict(ftx, bb, bn, db, kf, ku, ccy, isRateLimit=False)
    smartBasisDict = cl.getSmartBasisDict(ftx, bb, bn, db, kf, ku, ccy, fundingDict, isSkipAdj=True)
    smartBasisBps = smartBasisDict['ftxSmartBasis'] * 10000
    if smartBasisBps >= thresholdH:
      color = 'red'
    elif smartBasisBps <= thresholdL:
      color = 'cyan'
    else:
      color = 'grey'
    est1=fundingDict['ftxEstFunding']
    z = ccy + ':' + str(round(smartBasisBps)) + '(' + str(round(est1 * 100)) + ')'
    print(termcolor.colored(z.ljust(10+len(ccy)),color), end='')
  time.sleep(interval)
  print()

