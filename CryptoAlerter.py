import CryptoLib as cl
import time
import termcolor

###########
# Functions
###########
def process(config,premDict,status,color,funding,funding2=None):
  def printStar():
    print('*' + termcolor.colored(z, color), end='')
  #####
  _, _, buyTgtBps, sellTgtBps = cl.CT_CONFIGS_DICT[config]
  tmp=config.split('_')
  prefix=tmp[0].lower()+tmp[1]
  premBps = premDict[prefix+'Prem'] * 10000
  basisBps = premDict[prefix + 'Basis'] * 10000
  z=config+': ' + str(round(premBps)) + '/' +str(round(basisBps)) +'bps('+str(round(funding*100))+'%'
  if funding2 is None:
    n=25
  else:
    z=z+'/'+str(round(funding2*100))+'%'
    n=30
  z+=')'
  z=z.ljust(n)
  if premBps<=buyTgtBps:
    status-=1
  elif premBps>=sellTgtBps:
    status+=1
  else:
    status=0
  if status>=cl.CT_NOBS:
    printStar()
    cl.speak('High')
    status=0
  elif status<=(-cl.CT_NOBS):
    printStar()
    cl.speak('Low')
    status=0
  else:
    print(' ' + termcolor.colored(z, color), end='')
  return status

######
# Main
######
cl.printHeader('CryptoAlerter')
print(' Item 1:           Premium (i.e., smart basis)')
print(' Item 2:           Raw basis')
print(' Inside brackets:  Estimated funding rate')
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
  premDict = cl.getPremDict(ftx,bn,bb,fundingDict)
  ftxBTCStatus=process('FTX_BTC', premDict, ftxBTCStatus, 'blue', fundingDict['ftxEstFundingBTC'])
  bnBTCStatus = process('BN_BTC', premDict, bnBTCStatus, 'blue', fundingDict['bnEstFundingBTC'])
  bbBTCStatus = process('BB_BTC', premDict, bbBTCStatus, 'blue', fundingDict['bbEstFunding1BTC'], fundingDict['bbEstFunding2BTC'])
  ftxETHStatus=process('FTX_ETH', premDict, ftxETHStatus, 'red', fundingDict['ftxEstFundingETH'])
  bnETHStatus = process('BN_ETH', premDict, bnETHStatus, 'red', fundingDict['bnEstFundingETH'])
  bbETHStatus = process('BB_ETH', premDict, bbETHStatus, 'red', fundingDict['bbEstFunding1ETH'], fundingDict['bbEstFunding2ETH'])
  ftxFTTStatus=process('FTX_FTT', premDict, ftxFTTStatus, 'magenta', fundingDict['ftxEstFundingFTT'])
  print()
  time.sleep(cl.CT_SLEEP)
