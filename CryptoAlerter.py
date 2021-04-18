import CryptoLib as cl
import time
import termcolor
import datetime

###########
# Functions
###########
# Get current time
def getCurrentTimeCondensed():
  return datetime.datetime.today().strftime('%H:%M:%S')

def process(config,smartBasisDict,color,funding,funding2=None):
  tmp=config.split('_')
  prefix=tmp[0].lower()+tmp[1]
  smartBasisBps = smartBasisDict[prefix+'SmartBasis'] * 10000
  basisBps = smartBasisDict[prefix + 'Basis'] * 10000
  z=tmp[0]+': ' + str(round(smartBasisBps)) + '/' +str(round(basisBps)) +'bps('+str(round(funding*100))
  if funding2 is None:
    n=20
  else:
    z=z+'/'+str(round(funding2*100))
    n=24
  z+=')'
  print(termcolor.colored(z.ljust(n), color), end='')

######
# Main
######
cl.printHeader('CryptoAlerter')
print('Column 1:'.ljust(22)+'USD marginal rate / USDT marginal rate / Average coin lending rates (BTC, ETH)')
print('Body:'.ljust(22)+'Smart basis / raw basis (est. funding rate)')
print('Sections:'.ljust(22)+'Left = BTC, Right = ETH')
print()

ftx=cl.ftxCCXTInit()
bb=cl.bbCCXTInit()
bn=cl.bnCCXTInit()
kf=cl.kfInit()

while True:
  fundingDict = cl.getFundingDict(ftx,bb,bn,kf)
  smartBasisDict = cl.getSmartBasisDict(ftx, bb, bn, kf, fundingDict, isSkipAdj=True)
  print(getCurrentTimeCondensed().ljust(10),end='')
  avgCoinRate=(fundingDict['ftxEstLendingBTC']+fundingDict['ftxEstLendingETH'])/2
  print(termcolor.colored((str(round(fundingDict['ftxEstMarginalUSD'] * 100))+'/'+str(round(fundingDict['ftxEstMarginalUSDT'] * 100)) + '/'+ \
    str(round(avgCoinRate * 100))).ljust(12),'red'),end='')
  process('FTX_BTC', smartBasisDict, 'blue', fundingDict['ftxEstFundingBTC'])
  process('BB_BTC', smartBasisDict, 'blue', fundingDict['bbEstFunding1BTC'], fundingDict['bbEstFunding2BTC'])
  process('BN_BTC', smartBasisDict, 'blue', fundingDict['bnEstFundingBTC'])
  process('KF_BTC', smartBasisDict, 'blue', fundingDict['kfEstFunding1BTC'], fundingDict['kfEstFunding2BTC'])
  process('FTX_ETH', smartBasisDict, 'magenta', fundingDict['ftxEstFundingETH'])
  process('BB_ETH', smartBasisDict, 'magenta', fundingDict['bbEstFunding1ETH'], fundingDict['bbEstFunding2ETH'])
  process('BN_ETH', smartBasisDict, 'magenta', fundingDict['bnEstFundingETH'])
  process('KF_ETH', smartBasisDict, 'magenta', fundingDict['kfEstFunding1ETH'], fundingDict['kfEstFunding2ETH'])
  print()
  time.sleep(cl.CT_SLEEP)
