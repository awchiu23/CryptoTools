import CryptoLib as cl
import pandas as pd
import ccxt
import time
import termcolor
import winsound

########
# Params
########
BASE_L=-10
BASE_H=20

ftxBTC_L=BASE_L
ftxBTC_H=BASE_H

ftxETH_L=BASE_L
ftxETH_H=BASE_H

ftxFTT_L=BASE_L-5
ftxFTT_H=BASE_H+5

bnBTC_L=BASE_L
bnBTC_H=BASE_H

bnETH_L=BASE_L
bnETH_H=BASE_H

bbBTC_L=BASE_L
bbBTC_H=BASE_H

bbETH_L=BASE_L
bbETH_H=BASE_H

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
  if (premBps<=tgt_L) or (premBps>=tgt_H):
    status+=1
  else:
    status=0
  if status>=3:
    print('*' + termcolor.colored(z, color), end='')
    if premBps>=tgt_H:
      winsound.Beep(2888,888)
    else:
      winsound.Beep(888, 888)
    status-=1
  else:
    print(' ' + termcolor.colored(z, color), end='')
  return status

######
# Init
######
ftx=ccxt.ftx({'apiKey': cl.API_KEY_FTX, 'secret': cl.API_SECRET_FTX, 'enableRateLimit': True})
bn=ccxt.binance({'apiKey': cl.API_KEY_BINANCE, 'secret': cl.API_SECRET_BINANCE, 'enableRateLimit': True})
bb=ccxt.bybit({'apiKey': cl.API_KEY_BYBIT, 'secret': cl.API_SECRET_BYBIT, 'enableRateLimit': True})

######
# Main
######
cl.printHeader('CryptoAlerter')

ftxBTCStatus=0
ftxETHStatus=0
ftxFTTStatus=0
bnBTCStatus=0
bnETHStatus=0
bbBTCStatus=0
bbETHStatus=0

while True:
  ftxMarkets=pd.DataFrame(ftx.public_get_markets()['result'])
  spotBTC=cl.ftxGetMid(ftxMarkets,'BTC/USD')
  spotETH=cl.ftxGetMid(ftxMarkets,'ETH/USD')
  spotFTT=cl.ftxGetMid(ftxMarkets,'FTT/USD')
  ftxFutBTC=cl.ftxGetMid(ftxMarkets,'BTC-PERP')
  ftxFutETH=cl.ftxGetMid(ftxMarkets,'ETH-PERP')
  ftxFutFTT=cl.ftxGetMid(ftxMarkets,'FTT-PERP')
  ftxBTCPrem=ftxFutBTC/spotBTC-1
  ftxETHPrem=ftxFutETH/spotETH-1
  ftxFTTPrem=ftxFutFTT/spotFTT-1
  ftxEstFundingBTC = cl.ftxGetEstFunding(ftx,'BTC')
  ftxEstFundingETH = cl.ftxGetEstFunding(ftx,'ETH')
  ftxEstFundingFTT = cl.ftxGetEstFunding(ftx,'FTT')
  ftxEstBorrow = cl.ftxGetEstBorrow(ftx)

  bnFutBTC=cl.bnGetFut(bn,'BTC')
  bnFutETH=cl.bnGetFut(bn,'ETH')
  bnBTCPrem=bnFutBTC/spotBTC-1
  bnETHPrem=bnFutETH/spotETH-1
  bnEstFundingBTC = cl.bnGetEstFunding(bn,'BTC')
  bnEstFundingETH = cl.bnGetEstFunding(bn,'ETH')

  bbFutBTC=cl.bbGetFut(bb,'BTC')
  bbFutETH=cl.bbGetFut(bb,'ETH')
  bbBTCPrem = bbFutBTC / spotBTC - 1
  bbETHPrem = bbFutETH / spotETH - 1
  bbEstFunding1BTC = cl.bbGetEstFunding1(bb,'BTC')
  bbEstFunding1ETH = cl.bbGetEstFunding1(bb,'ETH')
  bbEstFunding2BTC = cl.bbGetEstFunding2(bb,'BTC')
  bbEstFunding2ETH = cl.bbGetEstFunding2(bb,'ETH')

  print('FTX_USD: (' + str(round(ftxEstBorrow * 100)) + '%)  ',end='')
  ftxBTCStatus=process('FTX_BTC',ftxBTCPrem,ftxBTC_L,ftxBTC_H,ftxBTCStatus,'blue',ftxEstFundingBTC)
  bnBTCStatus = process('BN_BTC', bnBTCPrem, bnBTC_L, bnBTC_H, bnBTCStatus,'blue',bnEstFundingBTC)
  bbBTCStatus = process('BB_BTC', bbBTCPrem, bbBTC_L, bbBTC_H, bbBTCStatus,'blue',bbEstFunding1BTC,bbEstFunding2BTC)
  
  ftxETHStatus=process('FTX_ETH',ftxETHPrem,ftxETH_L,ftxETH_H,ftxETHStatus,'red',ftxEstFundingETH)
  bnETHStatus = process('BN_ETH', bnETHPrem, bnETH_L, bnETH_H, bnETHStatus,'red',bnEstFundingETH)
  bbETHStatus = process('BB_ETH', bbETHPrem, bbETH_L, bbETH_H, bbETHStatus,'red',bbEstFunding1ETH,bbEstFunding2ETH)
  
  ftxFTTStatus=process('FTX_FTT',ftxFTTPrem,ftxFTT_L,ftxFTT_H,ftxFTTStatus,'magenta',ftxEstFundingFTT)
  print()

  time.sleep(5)
