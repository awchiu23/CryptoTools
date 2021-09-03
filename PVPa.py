import CryptoLib as cl
from CryptoParams import *
import time
import termcolor

########
# Params
########
ccys=SHARED_ETC_DICT['FTX_SPOTLESS']
thresholdH = 15+6
thresholdL = 0
interval = 60*5

######
# Main
######
cl.printHeader('PVPa')
ftx=cl.ftxCCXTInit()
bb=cl.bbCCXTInit()
bn = None
db = None
kf = None
while True:
  print(cl.getCurrentTime(isCondensed=True).ljust(10),end='')
  for i in range(len(ccys)):
    ccy=ccys[i]
    SHARED_CCY_DICT[ccy] = {'futExch': ['ftx','bbt']}
    fundingDict = cl.getFundingDict(ftx, bb, bn, db, kf, ccy, isRateLimit=False)
    smartBasisDict = cl.getSmartBasisDict(ftx, bb, bn, db, kf, ccy, fundingDict, isSkipAdj=True)
    smartBasisBps = (smartBasisDict['bbtSmartBasis'] - smartBasisDict['ftxSmartBasis']) * 10000
    if smartBasisBps >= thresholdH:
      color = 'red'
    elif smartBasisBps <= thresholdL:
      color = 'cyan'
    else:
      color = 'grey'
    est1=fundingDict['bbtEstFunding1']
    est2=fundingDict['bbtEstFunding2']
    estFTX=fundingDict['ftxEstFunding']
    z = ccy + ':' + str(round(smartBasisBps)) + '(' + str(round(est1 * 100)) + '/' + str(round(est2 * 100))+ '/-' + str(round(estFTX*100)) + ')'
    print(termcolor.colored(z.ljust(20+len(ccy)),color), end='')
  time.sleep(interval)
  print()

