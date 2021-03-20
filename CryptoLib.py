################
# Crypto Library
################
import pandas as pd
import datetime

#############################################################################################

# Please replace the following section with your own API codes

import SimonLib as sl
API_KEY_FTX = sl.jLoad('API_KEY_FTX')
API_SECRET_FTX = sl.jLoad('API_SECRET_FTX')
API_KEY_BINANCE = sl.jLoad('API_KEY_BINANCE')
API_SECRET_BINANCE = sl.jLoad('API_SECRET_BINANCE')
API_KEY_BYBIT = sl.jLoad('API_KEY_BYBIT')
API_SECRET_BYBIT = sl.jLoad('API_SECRET_BYBIT')
API_KEY_CB = sl.jLoad('API_KEY_CB')
API_SECRET_CB = sl.jLoad('API_SECRET_CB')

#API_KEY_FTX = ''
#API_SECRET_FTX = ''
#API_KEY_BINANCE = ''
#API_SECRET_BINANCE = ''
#API_KEY_BYBIT = ''
#API_SECRET_BYBIT = ''
#API_KEY_CB = ''
#API_SECRET_CB = ''

#############################################################################################

def ftxGetMid(ftxMarkets, name):
  df = ftxMarkets[ftxMarkets['name'] == name]
  return float((df['bid'] + df['ask']) / 2)

def ftxGetEstFunding(ftx, ccy):
  while True:
    try:
      ef = ftx.public_get_futures_future_name_stats({'future_name': ccy+'-PERP'})['result']['nextFundingRate'] * 24 * 365
    except:
      continue
    else:
      break
  return ef

def ftxGetEstBorrow(ftx):
  while True:
    try:
      eb = pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365
    except:
      continue
    else:
      break
  return eb

def bnGetFut(bn,ccy):
  while True:
    try:
      bnBookTicker = bn.dapiPublicGetTickerBookTicker({'symbol': ccy + 'USD_PERP'})[0]
    except:
      continue
    else:
      break
  return (float(bnBookTicker['bidPrice']) + float(bnBookTicker['askPrice'])) / 2

def bnGetEstFunding(bn, ccy):
  while True:
    try:
      ef = float(pd.DataFrame(bn.dapiPublic_get_premiumindex({'symbol': ccy+'USD_PERP'}))['lastFundingRate']) * 3 * 365
    except:
      continue
    else:
      break
  return ef

def bbGetFut(bb,ccy):
  while True:
    try:
      bbTickers=bb.v2PublicGetTickers({'symbol':ccy+'USD'})['result'][0]
    except:
      continue
    else:
      break
  return (float(bbTickers['bid_price'])+float(bbTickers['ask_price']))/2

def bbGetEstFunding1(bb,ccy):
  while True:
    try:
      ef = float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': ccy+'USD'})['result']['funding_rate']) * 3 * 365
    except:
      continue
    else:
      break
  return ef

def bbGetEstFunding2(bb, ccy):
  while True:
    try:
      ef2 = bb.v2PrivateGetFundingPredictedFunding({'symbol': ccy+'USD'})['result']['predicted_funding_rate'] * 3 * 365
    except:
      continue
    else:
      break
  return ef2

#############################################################################################

def getPremDict(ftx,bn,bb):
  d=dict()
  ftxMarkets = pd.DataFrame(ftx.public_get_markets()['result'])
  spotBTC = ftxGetMid(ftxMarkets, 'BTC/USD')
  spotETH = ftxGetMid(ftxMarkets, 'ETH/USD')
  spotFTT = ftxGetMid(ftxMarkets, 'FTT/USD')
  ftxFutBTC = ftxGetMid(ftxMarkets, 'BTC-PERP')
  ftxFutETH = ftxGetMid(ftxMarkets, 'ETH-PERP')
  ftxFutFTT = ftxGetMid(ftxMarkets, 'FTT-PERP')
  d['ftxBTCPrem']=ftxFutBTC / spotBTC - 1
  d['ftxETHPrem']=ftxFutETH / spotETH - 1
  d['ftxFTTPrem']=ftxFutFTT / spotFTT - 1

  bnFutBTC = bnGetFut(bn, 'BTC')
  bnFutETH = bnGetFut(bn, 'ETH')
  d['bnBTCPrem'] = bnFutBTC / spotBTC - 1
  d['bnETHPrem'] = bnFutETH / spotETH - 1

  bbFutBTC = bbGetFut(bb, 'BTC')
  bbFutETH = bbGetFut(bb, 'ETH')
  d['bbBTCPrem'] = bbFutBTC / spotBTC - 1
  d['bbETHPrem'] = bbFutETH / spotETH - 1

  return d

#############################################################################################
#####
# Etc
#####
# Get current time
def getCurrentTime():
  return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

# Print header
def printHeader(header=''):
  print()
  print('-' * 100)
  print()
  if len(header) > 0:
    print('['+header+']')
    print()
