import CryptoLib as cl
import time
import termcolor

########
# Params
########
BASE_L=-10
BASE_H=10

FTX_BTC_L=BASE_L
FTX_BTC_H=BASE_H

FTX_ETH_L=BASE_L
FTX_ETH_H=BASE_H

FTX_FTT_L= BASE_L - 10
FTX_FTT_H= BASE_H + 10

BN_BTC_L=BASE_L
BN_BTC_H=BASE_H

BN_ETH_L=BASE_L
BN_ETH_H=BASE_H

BB_BTC_L=BASE_L
BB_BTC_H=BASE_H

BB_ETH_L=BASE_L
BB_ETH_H=BASE_H

NOBS=5 # Number of observations through target before triggering

###########
# Functions
###########
def process(ccy,prem,tgt_L,tgt_H,status,color,funding,funding2=None):
  premBps = prem * 10000
  z=ccy+': ' + str(round(premBps)) + 'bps('+str(round(funding*100))+'%'
  if funding2 is None:
    n=20
  else:
    z=z+'/'+str(round(funding2*100))+'%'
    n=25
  z+=')'
  z=z.ljust(n)
  if premBps<=tgt_L:
    status-=1
  elif premBps>=tgt_H:
    status+=1
  else:
    status=0
  if status>=NOBS:
    print('*' + termcolor.colored(z, color), end='')
    cl.speak('High')
    status=0
  elif status<=(-NOBS):
    print('*' + termcolor.colored(z, color), end='')
    cl.speak('Low')
    status=0
  else:
    print(' ' + termcolor.colored(z, color), end='')
  return status

######
# Main
######
cl.printHeader('CryptoAlerter')
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

  ftxBTCStatus=process('FTX_BTC', premDict['ftxBTCPrem'], FTX_BTC_L, FTX_BTC_H, ftxBTCStatus, 'blue', fundingDict['ftxEstFundingBTC'])
  bnBTCStatus = process('BN_BTC', premDict['bnBTCPrem'], BN_BTC_L, BN_BTC_H, bnBTCStatus, 'blue', fundingDict['bnEstFundingBTC'])
  bbBTCStatus = process('BB_BTC', premDict['bbBTCPrem'], BB_BTC_L, BB_BTC_H, bbBTCStatus, 'blue', fundingDict['bbEstFunding1BTC'], fundingDict['bbEstFunding2BTC'])
  
  ftxETHStatus=process('FTX_ETH', premDict['ftxETHPrem'], FTX_ETH_L, FTX_ETH_H, ftxETHStatus, 'red', fundingDict['ftxEstFundingETH'])
  bnETHStatus = process('BN_ETH', premDict['bnETHPrem'], BN_ETH_L, BN_ETH_H, bnETHStatus, 'red', fundingDict['bnEstFundingETH'])
  bbETHStatus = process('BB_ETH', premDict['bbETHPrem'], BB_ETH_L, BB_ETH_H, bbETHStatus, 'red', fundingDict['bbEstFunding1ETH'], fundingDict['bbEstFunding2ETH'])
  
  ftxFTTStatus=process('FTX_FTT', premDict['ftxFTTPrem'], FTX_FTT_L, FTX_FTT_H, ftxFTTStatus, 'magenta', fundingDict['ftxEstFundingFTT'])
  print()

  time.sleep(5)
