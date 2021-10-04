import CryptoLib as cl
from CryptoParams import *
import time
import termcolor

########
# Params
########
ccys=['VET','ADA','DOT']
thresholdH = 15+6
thresholdL = 0
interval = 60*5

######
# Main
######
cl.printHeader('PVP2a')
ftx=cl.ftxCCXTInit()
bb= None
bn = None
db = None
kf = None
ku = cl.kuCCXTInit()
while True:
  print(cl.getCurrentTime(isCondensed=True).ljust(10),end='')
  for i in range(len(ccys)):
    ccy=ccys[i]
    SHARED_CCY_DICT[ccy] = {'futExch': ['ftx','kut']}
    fundingDict = cl.getFundingDict(ftx, bb, bn, db, kf, ku, ccy, isRateLimit=False)
    smartBasisDict = cl.getSmartBasisDict(ftx, bb, bn, db, kf, ku, ccy, fundingDict, isSkipAdj=True)
    smartBasisBps = (smartBasisDict['kutSmartBasis'] - smartBasisDict['ftxSmartBasis']) * 10000
    if smartBasisBps >= thresholdH:
      color = 'red'
    elif smartBasisBps <= thresholdL:
      color = 'cyan'
    else:
      color = 'grey'
    est1=fundingDict['kutEstFunding1']
    est2=fundingDict['kutEstFunding2']
    estFTX=fundingDict['ftxEstFunding']
    z = ccy + ':' + str(round(smartBasisBps)) + '(' + str(round(est1 * 100)) + '/' + str(round(est2 * 100))+ '||' + str(round(estFTX*100)) + ')'
    print(termcolor.colored(z.ljust(18+len(ccy)),color), end='')
  time.sleep(interval)
  print()

