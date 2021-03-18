import SimonLib as sl
import pandas as pd
import ccxt
import time
import termcolor
import winsound

########
# Params
########
API_KEY_FTX = sl.jLoad('API_KEY_FTX')
API_SECRET_FTX = sl.jLoad('API_SECRET_FTX')
API_KEY_BINANCE = sl.jLoad('API_KEY_BINANCE')
API_SECRET_BINANCE = sl.jLoad('API_SECRET_BINANCE')
API_KEY_BYBIT = sl.jLoad('API_KEY_BYBIT')
API_SECRET_BYBIT = sl.jLoad('API_SECRET_BYBIT')

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
def ftxGetMid(ftxMarkets, name):
  df = ftxMarkets[ftxMarkets['name'] == name]
  return float((df['bid'] + df['ask']) / 2)

def bnGetFut(bn,ccy):
  bnBookTicker = bn.dapiPublicGetTickerBookTicker({'symbol': ccy + 'USD_PERP'})[0]
  return (float(bnBookTicker['bidPrice']) + float(bnBookTicker['askPrice'])) / 2

def bbGetFut(bb,ccy):
  while True:
    try:
      bbTickers=bb.v2PublicGetTickers({'symbol':ccy+'USD'})['result'][0]
    except:
      continue
    else:
      break
  return (float(bbTickers['bid_price'])+float(bbTickers['ask_price']))/2

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
ftx=ccxt.ftx({'apiKey': API_KEY_FTX, 'secret': API_SECRET_FTX, 'enableRateLimit': True})
bn = ccxt.binance({'apiKey': API_KEY_BINANCE, 'secret': API_SECRET_BINANCE, 'enableRateLimit': True})
bb = ccxt.bybit({'apiKey': API_KEY_BYBIT, 'secret': API_SECRET_BYBIT, 'enableRateLimit': True})

######
# Main
######
sl.printHeader('CryptoAlerter')

ftxBTCStatus=0
ftxETHStatus=0
ftxFTTStatus=0
bnBTCStatus=0
bnETHStatus=0
bbBTCStatus=0
bbETHStatus=0

while True:
  ftxMarkets=pd.DataFrame(ftx.public_get_markets()['result'])
  spotBTC=ftxGetMid(ftxMarkets,'BTC/USD')
  spotETH=ftxGetMid(ftxMarkets,'ETH/USD')
  spotFTT=ftxGetMid(ftxMarkets,'FTT/USD')
  ftxFutBTC=ftxGetMid(ftxMarkets,'BTC-PERP')
  ftxFutETH=ftxGetMid(ftxMarkets,'ETH-PERP')
  ftxFutFTT=ftxGetMid(ftxMarkets,'FTT-PERP')
  ftxBTCPrem=ftxFutBTC/spotBTC-1
  ftxETHPrem=ftxFutETH/spotETH-1
  ftxFTTPrem=ftxFutFTT/spotFTT-1
  ftxEstFundingBTC = ftx.public_get_futures_future_name_stats({'future_name': 'BTC-PERP'})['result']['nextFundingRate'] * 24 * 365
  ftxEstFundingETH = ftx.public_get_futures_future_name_stats({'future_name': 'ETH-PERP'})['result']['nextFundingRate'] * 24 * 365
  ftxEstFundingFTT = ftx.public_get_futures_future_name_stats({'future_name': 'FTT-PERP'})['result']['nextFundingRate'] * 24 * 365
  ftxEstBorrow = pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365

  bnFutBTC=bnGetFut(bn,'BTC')
  bnFutETH=bnGetFut(bn,'ETH')
  bnBTCPrem=bnFutBTC/spotBTC-1
  bnETHPrem=bnFutETH/spotETH-1
  bnEstFundingBTC = float(pd.DataFrame(bn.dapiPublic_get_premiumindex({'symbol': 'BTCUSD_PERP'}))['lastFundingRate']) * 3 * 365
  bnEstFundingETH = float(pd.DataFrame(bn.dapiPublic_get_premiumindex({'symbol': 'ETHUSD_PERP'}))['lastFundingRate']) * 3 * 365

  bbFutBTC=bbGetFut(bb,'BTC')
  bbFutETH=bbGetFut(bb,'ETH')
  bbBTCPrem = bbFutBTC / spotBTC - 1
  bbETHPrem = bbFutETH / spotETH - 1
  bbEstFunding1BTC = float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': 'BTCUSD'})['result']['funding_rate']) * 3 * 365
  bbEstFunding1ETH = float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': 'ETHUSD'})['result']['funding_rate']) * 3 * 365
  bbEstFunding2BTC = bb.v2PrivateGetFundingPredictedFunding({'symbol': 'BTCUSD'})['result']['predicted_funding_rate'] * 3 * 365
  bbEstFunding2ETH = bb.v2PrivateGetFundingPredictedFunding({'symbol': 'ETHUSD'})['result']['predicted_funding_rate'] * 3 * 365

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
