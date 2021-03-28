import CryptoLib as cl
import time
import termcolor

###########
# Functions
###########
def process(config,smartBasisDict,color,funding,funding2=None):
  tmp=config.split('_')
  prefix=tmp[0].lower()+tmp[1]
  smartBasisBps = smartBasisDict[prefix+'SmartBasis'] * 10000
  basisBps = smartBasisDict[prefix + 'Basis'] * 10000
  z=config+': ' + str(round(smartBasisBps)) + '/' +str(round(basisBps)) +'bps('+str(round(funding*100))+'%'
  if funding2 is None:
    n=27
  else:
    z=z+'/'+str(round(funding2*100))+'%'
    n=31
  z+=')'
  print(termcolor.colored(z.ljust(n), color), end='')

######
# Main
######
cl.printHeader('CryptoAlerter')
print('Column 1:'.ljust(20)+'USD marginal rate / BTC lending rate / ETH lending rate / spot rate')
print(''.ljust(20)+'Spot rate = USD marginal rate - average(BTC lending rate, ETH lending rate)')
print('Body:'.ljust(20)+'Smart basis / raw basis (est. funding rate %)')
print()

ftx=cl.ftxCCXTInit()
bn=cl.bnCCXTInit()
bb=cl.bbCCXTInit()

while True:
  fundingDict = cl.getFundingDict(ftx,bn,bb)
  smartBasisDict = cl.getSmartBasisDict(ftx, bn, bb, fundingDict, isSkipAdj=True)
  print((str(round(fundingDict['ftxEstMarginalUSD'] * 100))+'%/'+str(round(fundingDict['ftxEstLendingBTC'] * 100)) + '%/'+ \
         str(round(fundingDict['ftxEstLendingETH'] * 100)) + '%/' + str(round(fundingDict['ftxEstSpot'] * 100)) + '%').ljust(20),end='')
  process('FTX_BTC', smartBasisDict, 'blue', fundingDict['ftxEstFundingBTC'])
  process('BN_BTC', smartBasisDict, 'blue', fundingDict['bnEstFundingBTC'])
  process('BB_BTC', smartBasisDict, 'blue', fundingDict['bbEstFunding1BTC'], fundingDict['bbEstFunding2BTC'])
  process('FTX_ETH', smartBasisDict, 'magenta', fundingDict['ftxEstFundingETH'])
  process('BN_ETH', smartBasisDict, 'magenta', fundingDict['bnEstFundingETH'])
  process('BB_ETH', smartBasisDict, 'magenta', fundingDict['bbEstFunding1ETH'], fundingDict['bbEstFunding2ETH'])
  process('FTX_FTT', smartBasisDict, 'blue', fundingDict['ftxEstFundingFTT'])
  print()
  time.sleep(cl.CT_SLEEP)
