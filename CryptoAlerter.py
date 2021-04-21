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
  z=tmp[0]+':' + str(round(smartBasisBps)) + '/' +str(round(basisBps)) +'bps('+str(round(funding*100))
  if funding2 is None:
    n=19
  else:
    z=z+'/'+str(round(funding2*100))
    n=23
  z+=')'
  print(termcolor.colored(z.ljust(n), color), end='')

######
# Main
######
cl.printHeader('CryptoAlerter')
col1N = 21
print('Column 1:'.ljust(col1N)+'USD marginal rate / USDT marginal rate / Average coin lending rates (BTC, ETH)')
print('Body:'.ljust(col1N)+'Smart basis / raw basis (est. funding rate)')
print('Sections:'.ljust(col1N)+'Left = BTC, Right = ETH')
print()

ftx=cl.ftxCCXTInit()
bb=cl.bbCCXTInit()
bn=cl.bnCCXTInit()
db=cl.dbCCXTInit()
kf=cl.kfInit()

while True:
  fundingDict = cl.getFundingDict(ftx,bb,bn,db,kf)
  smartBasisDict = cl.getSmartBasisDict(ftx, bb, bn,db,kf, fundingDict, isSkipAdj=True)
  print(getCurrentTimeCondensed().ljust(10),end='')
  avgCoinRate=(fundingDict['ftxEstLendingBTC']+fundingDict['ftxEstLendingETH'])/2
  print(termcolor.colored((str(round(fundingDict['ftxEstMarginalUSD'] * 100))+'/'+str(round(fundingDict['ftxEstMarginalUSDT'] * 100)) + '/'+ \
    str(round(avgCoinRate * 100))).ljust(col1N-10),'red'),end='')
  process('FTX_BTC', smartBasisDict, 'blue', fundingDict['ftxEstFundingBTC'])
  process('BB_BTC', smartBasisDict, 'blue', fundingDict['bbEstFunding1BTC'], fundingDict['bbEstFunding2BTC'])
  process('BN_BTC', smartBasisDict, 'blue', fundingDict['bnEstFundingBTC'])
  process('DB_BTC', smartBasisDict, 'blue', fundingDict['dbEstFundingBTC'])
  process('KF_BTC', smartBasisDict, 'blue', fundingDict['kfEstFunding1BTC'], fundingDict['kfEstFunding2BTC'])
  process('FTX_ETH', smartBasisDict, 'magenta', fundingDict['ftxEstFundingETH'])
  process('BB_ETH', smartBasisDict, 'magenta', fundingDict['bbEstFunding1ETH'], fundingDict['bbEstFunding2ETH'])
  process('BN_ETH', smartBasisDict, 'magenta', fundingDict['bnEstFundingETH'])
  process('DB_ETH', smartBasisDict, 'magenta', fundingDict['dbEstFundingETH'])
  process('KF_ETH', smartBasisDict, 'magenta', fundingDict['kfEstFunding1ETH'], fundingDict['kfEstFunding2ETH'])
  print()
  time.sleep(cl.CT_SLEEP)
