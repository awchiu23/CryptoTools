import CryptoLib as cl
import time
import termcolor

###########
# Functions
###########
def process(config,smartBasisDict,status,color,funding,funding2=None):
  _, _, buyTgtBps, sellTgtBps = cl.CT_CONFIGS_DICT[config]
  tmp=config.split('_')
  prefix=tmp[0].lower()+tmp[1]
  smartBasisBps = smartBasisDict[prefix+'SmartBasis'] * 10000
  basisBps = smartBasisDict[prefix + 'Basis'] * 10000
  z=config+': ' + str(round(smartBasisBps)) + '/' +str(round(basisBps)) +'bps('+str(round(funding*100))+'%'
  if funding2 is None:
    n=25
  else:
    z=z+'/'+str(round(funding2*100))+'%'
    n=29
  z+=')'
  z=z.ljust(n)
  if smartBasisBps<=buyTgtBps:
    status-=1
    symbol = str(status).rjust(2)
  elif smartBasisBps>=sellTgtBps:
    status+=1
    symbol = str(status).rjust(2)
  else:
    status = 0
    symbol = '  '
  if status>=cl.CT_NOBS:
    status = 0
    symbol=' H'
  elif status<=(-cl.CT_NOBS):
    status = 0
    symbol=' L'

  print(termcolor.colored(symbol,'red')+' ' + termcolor.colored(z, color), end='')
  if symbol==' H':
    cl.speak('High')
  elif symbol==' L':
    cl.speak('Low')
  return status

######
# Main
######
cl.printHeader('CryptoAlerter')
print('Column 1: (FTX USD borrow rate % / FTX USD lending rate %)')
print('Body:     Smart basis / Raw basis (Est. funding rate %)')
print()
cl.printDict(cl.CT_CONFIGS_DICT)
print()

ftx=cl.ftxCCXTInit()
bn=cl.bnCCXTInit()
bb=cl.bbCCXTInit()
ftxBTCStatus=0
ftxETHStatus=0
ftxFTTStatus=0
bnBTCStatus=0
bnETHStatus=0
bbBTCStatus=0
bbETHStatus=0

while True:
  fundingDict = cl.getFundingDict(ftx,bn,bb)
  smartBasisDict = cl.getSmartBasisDict(ftx, bn, bb, fundingDict)
  print(('(' + str(round(fundingDict['ftxEstBorrow'] * 100)) + '/' + str(round(fundingDict['ftxEstLending'] * 100)) + '%)').ljust(16),end='')
  ftxBTCStatus=process('FTX_BTC', smartBasisDict, ftxBTCStatus, 'blue', fundingDict['ftxEstFundingBTC'])
  bnBTCStatus = process('BN_BTC', smartBasisDict, bnBTCStatus, 'blue', fundingDict['bnEstFundingBTC'])
  bbBTCStatus = process('BB_BTC', smartBasisDict, bbBTCStatus, 'blue', fundingDict['bbEstFunding1BTC'], fundingDict['bbEstFunding2BTC'])
  ftxETHStatus=process('FTX_ETH', smartBasisDict, ftxETHStatus, 'magenta', fundingDict['ftxEstFundingETH'])
  bnETHStatus = process('BN_ETH', smartBasisDict, bnETHStatus, 'magenta', fundingDict['bnEstFundingETH'])
  bbETHStatus = process('BB_ETH', smartBasisDict, bbETHStatus, 'magenta', fundingDict['bbEstFunding1ETH'], fundingDict['bbEstFunding2ETH'])
  ftxFTTStatus=process('FTX_FTT', smartBasisDict, ftxFTTStatus, 'blue', fundingDict['ftxEstFundingFTT'])
  print()
  time.sleep(cl.CT_SLEEP)
