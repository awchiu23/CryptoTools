################
# Crypto Library
################
import pandas as pd
import numpy as np
import datetime
import sys
import time
import termcolor
import ccxt
from retrying import retry

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

#########################
# Params for CryptoTrader
#########################
CT_DEFAULT_SELL_TGT_BPS = 20
CT_DEFAULT_BUY_TGT_BPS = 0

CT_CONFIGS_DICT=dict() # Future exchange, Ccy, Is sell prem?, Target prem in bps
CT_CONFIGS_DICT['FTX_BTC_SELL']=['ftx','BTC',True,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BN_BTC_SELL']=['bn','BTC',True,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BB_BTC_SELL']=['bb','BTC',True,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['FTX_ETH_SELL']=['ftx','ETH',True,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BN_ETH_SELL']=['bn','ETH',True,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BB_ETH_SELL']=['bb','ETH',True,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['FTX_FTT_SELL']=['ftx','FTT',True,CT_DEFAULT_SELL_TGT_BPS+10]

CT_CONFIGS_DICT['FTX_BTC_BUY']=['ftx','BTC',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BN_BTC_BUY']=['bn','BTC',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BB_BTC_BUY']=['bb','BTC',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['FTX_ETH_BUY']=['ftx','ETH',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BN_ETH_BUY']=['bn','ETH',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BB_ETH_BUY']=['bb','ETH',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['FTX_FTT_BUY']=['ftx','FTT',False,CT_DEFAULT_BUY_TGT_BPS-10]

CT_NOBS = 5          # Number of observations through target before triggering
CT_NPROGRAMS = 10    # Number of programs (each program being a pair of trades)

CT_TRADE_BTC_NOTIONAL = 3000  # Per trade notional
CT_TRADE_ETH_NOTIONAL = 3000   # Per trade notional
CT_TRADE_FTT_NOTIONAL = 1000   # Per trade notional

CT_MAX_NOTIONAL = 50000        # Hard limit
CT_MAX_BTC = 0.5               # Hard limit
CT_MAX_ETH = 10                # Hard limit
CT_MAX_FTT = 100               # Hard limit

#############################################################################################

###########################
# Params for Premium Models
###########################
HALF_LIFE_HOURS = 4            # Half life of exponential decay in hours
BASE_USD_RATE = 0.15           # Equilibrium USD rate P.A.
BASE_FUNDING_RATE = 0.11       # Equilibrium funding rate P.A. (all exchanges)
BASE_BASIS = 0.001             # Equilibrium future basis

#############################################################################################

###########
# Functions
###########
def ftxCCXTInit():
  return ccxt.ftx({'apiKey': API_KEY_FTX, 'secret': API_SECRET_FTX, 'enableRateLimit': True})

def bnCCXTInit():
  return  ccxt.binance({'apiKey': API_KEY_BINANCE, 'secret': API_SECRET_BINANCE, 'enableRateLimit': True})

def bbCCXTInit():
  return ccxt.bybit({'apiKey': API_KEY_BYBIT, 'secret': API_SECRET_BYBIT, 'enableRateLimit': True})

def cbCCXTInit():
  return ccxt.coinbase({'apiKey': API_KEY_CB, 'secret': API_SECRET_CB, 'enableRateLimit': True})

#############################################################################################

@retry
def ftxGetEstFunding(ftx, ccy):
  return ftx.public_get_futures_future_name_stats({'future_name': ccy+'-PERP'})['result']['nextFundingRate'] * 24 * 365

@retry
def ftxGetEstBorrow(ftx):
  return pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365

@retry
def ftxGetEstLending(ftx):
  return pd.DataFrame(ftx.private_get_spot_margin_lending_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365

def ftxRelOrder(side,ftx,ticker,trade_qty):
  @retry
  def ftxGetBid(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['bid']

  @retry
  def ftxGetAsk(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['ask']

  @retry
  def ftxGetRemainingSize(ftx,orderId):
    return ftx.private_get_orders_order_id({'order_id': orderId})['result']['remainingSize']
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  print(getCurrentTime()+': Sending FTX '+side+' order of '+ticker+' (qty='+str(round(trade_qty,6))+') ....')
  if side=='BUY':
    limitPrice = ftxGetBid(ftx, ticker)
    orderId = ftx.create_limit_buy_order(ticker, trade_qty, limitPrice)['info']['id']
  else:
    limitPrice = ftxGetAsk(ftx, ticker)
    orderId = ftx.create_limit_sell_order(ticker, trade_qty, limitPrice)['info']['id']
  while True:
    if ftxGetRemainingSize(ftx,orderId) == 0:
      break
    else:
      if side=='BUY':
        newPrice=ftxGetBid(ftx,ticker)
      else:
        newPrice=ftxGetAsk(ftx,ticker)
      if newPrice != limitPrice:
        limitPrice=newPrice
        try:
          orderId=ftx.private_post_orders_order_id_modify({'order_id':orderId,'price':limitPrice})['result']['id']
        except:
          break
      time.sleep(1)

#####

@retry
def bnGetEstFunding(bn, ccy):
  return float(pd.DataFrame(bn.dapiPublic_get_premiumindex({'symbol': ccy+'USD_PERP'}))['lastFundingRate']) * 3 * 365

def bnMarketOrder(side,bn,ccy,trade_notional):
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)()
  ticker=ccy+'USD_PERP'
  print(getCurrentTime() + ': Sending BN ' + side + ' order of ' + ticker + ' (notional=$'+ str(round(trade_notional))+') ....')
  if ccy=='BTC':
    qty=int(trade_notional/100)
  elif ccy=='ETH':
    qty=int(trade_notional/10)
  else:
    sys.exit(1)
  bn.dapiPrivate_post_order({'symbol': ticker, 'side': side, 'type': 'MARKET', 'quantity': qty})

#####

@retry
def bbGetEstFunding1(bb,ccy):
  return float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': ccy+'USD'})['result']['funding_rate']) * 3 * 365

@retry
def bbGetEstFunding2(bb, ccy):
  return bb.v2PrivateGetFundingPredictedFunding({'symbol': ccy+'USD'})['result']['predicted_funding_rate'] * 3 * 365

def bbRelOrder(side,bb,ccy,trade_notional):
  def bbGetBid(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['bid_price'])
  def bbGetAsk(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['ask_price'])
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  ticker1=ccy+'/USD'
  ticker2=ccy+'USD'
  print(getCurrentTime() + ': Sending BB ' + side + ' order of ' + ticker1 + ' (notional=$'+ str(round(trade_notional))+') ....')
  if side=='BUY':
    limitPrice = bbGetBid(bb, ticker1)
    orderId = bb.create_limit_buy_order(ticker1, trade_notional, limitPrice)['info']['order_id']
  else:
    limitPrice = bbGetAsk(bb, ticker1)
    orderId = bb.create_limit_sell_order(ticker1, trade_notional, limitPrice)['info']['order_id']
  while True:
    if len(bb.v2_private_get_order({'symbol':ticker2,'orderid':orderId})['result'])==0:
      break
    else:
      if side=='BUY':
        newPrice=bbGetBid(bb,ticker1)
      else:
        newPrice=bbGetAsk(bb,ticker1)
      if newPrice != limitPrice:
        limitPrice = newPrice
        try:
          bb.v2_private_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': limitPrice})
        except:
          break
    time.sleep(1)

#############################################################################################

################
# Premium models
################
def getFundingDict(ftx,bn,bb):
  d=dict()
  d['ftxEstFundingBTC'] = ftxGetEstFunding(ftx, 'BTC')
  d['ftxEstFundingETH'] = ftxGetEstFunding(ftx, 'ETH')
  d['ftxEstFundingFTT'] = ftxGetEstFunding(ftx, 'FTT')
  d['ftxEstBorrow'] = ftxGetEstBorrow(ftx)
  d['ftxEstLending'] = ftxGetEstLending(ftx)
  d['bnEstFundingBTC'] = bnGetEstFunding(bn, 'BTC')
  d['bnEstFundingETH'] = bnGetEstFunding(bn, 'ETH')
  d['bbEstFunding1BTC'] = bbGetEstFunding1(bb, 'BTC')
  d['bbEstFunding1ETH'] = bbGetEstFunding1(bb, 'ETH')
  d['bbEstFunding2BTC'] = bbGetEstFunding2(bb, 'BTC')
  d['bbEstFunding2ETH'] = bbGetEstFunding2(bb, 'ETH')
  return d

def getOneDayShortSpotEdge(fundingDict):
  usdRate=(fundingDict['ftxEstBorrow']+fundingDict['ftxEstLending'])/2
  return getOneDayDecayedMean(usdRate,BASE_USD_RATE,HALF_LIFE_HOURS)/365

def getOneDayShortFutEdge(hoursInterval,basis,snapFundingRate,estFundingRate,prevFundingRate=None):
  edge=basis-getOneDayDecayedMean(basis,BASE_BASIS,HALF_LIFE_HOURS)
  edge+=getOneDayDecayedMean(snapFundingRate,BASE_FUNDING_RATE,HALF_LIFE_HOURS)/365
  edge+=estFundingRate/365/(24/hoursInterval) * getPctElapsed(hoursInterval)  # Locked funding from elapsed
  if not prevFundingRate is None:
    edge+=prevFundingRate/365/(24/hoursInterval)                              # Locked funding from previous reset
  return edge

def ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, ccy, basis):
  df=ftxFutures.loc[ccy+'-PERP']
  snapFundingRate=(df['mark'] / df['index'] - 1)*365
  return getOneDayShortFutEdge(1,basis,snapFundingRate,fundingDict['ftxEstFunding' + ccy])

def bnGetOneDayShortFutEdge(bn, fundingDict, ccy, basis):
  df=bn.dapiPublic_get_premiumindex({'symbol': ccy + 'USD_PERP'})[0]
  snapFundingRate = (float(df['markPrice']) / float(df['indexPrice']) - 1) * 365
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['bnEstFunding' + ccy])

def bbGetOneDayShortFutEdge(bbTickers, fundingDict, ccy, basis):
  snapFundingRate=(float(bbTickers.loc[ccy+'USD']['mark_price'])/float(bbTickers.loc[ccy+'USD']['index_price'])-1)*365
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['bbEstFunding2' + ccy], fundingDict['bbEstFunding1'+ccy])

def getPremDict(ftx,bn,bb,fundingDict):
  def ftxGetMid(ftxMarkets, name):
    return (ftxMarkets.loc[name,'bid'] + ftxMarkets.loc[name,'ask']) / 2
  #####
  def bnGetMid(bnBookTicker, ccy):
    return (float(bnBookTicker.loc[ccy+'USD_PERP','bidPrice']) + float(bnBookTicker.loc[ccy+'USD_PERP','askPrice'])) / 2
  #####
  def bbGetMid(bbTickers, ccy):
    return (float(bbTickers.loc[ccy,'bid_price']) + float(bbTickers.loc[ccy,'ask_price'])) / 2
  #####
  d=dict()
  ftxMarkets = pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')
  bnBookTicker = pd.DataFrame(bn.dapiPublicGetTickerBookTicker()).set_index('symbol')
  bbTickers = pd.DataFrame(bb.v2PublicGetTickers()['result']).set_index('symbol')
  spotBTC = ftxGetMid(ftxMarkets, 'BTC/USD')
  spotETH = ftxGetMid(ftxMarkets, 'ETH/USD')
  spotFTT = ftxGetMid(ftxMarkets, 'FTT/USD')
  ftxBTCBasis = ftxGetMid(ftxMarkets, 'BTC-PERP') / spotBTC - 1
  ftxETHBasis = ftxGetMid(ftxMarkets, 'ETH-PERP') / spotETH - 1
  ftxFTTBasis = ftxGetMid(ftxMarkets, 'FTT-PERP') / spotFTT - 1
  bnBTCBasis = bnGetMid(bnBookTicker, 'BTC') / spotBTC - 1
  bnETHBasis = bnGetMid(bnBookTicker, 'ETH') / spotETH - 1
  bbBTCBasis = bbGetMid(bbTickers, 'BTCUSD') / spotBTC - 1
  bbETHBasis = bbGetMid(bbTickers, 'ETHUSD') / spotETH - 1
  #####
  oneDayShortSpotEdge=getOneDayShortSpotEdge(fundingDict)
  ftxFutures = pd.DataFrame(ftx.public_get_futures()['result']).set_index('name')
  d['ftxBTCPrem'] = (ftxGetOneDayShortFutEdge(ftxFutures,fundingDict,'BTC',ftxBTCBasis) - oneDayShortSpotEdge)
  d['ftxETHPrem'] = (ftxGetOneDayShortFutEdge(ftxFutures,fundingDict,'ETH',ftxETHBasis) - oneDayShortSpotEdge)
  d['ftxFTTPrem'] = (ftxGetOneDayShortFutEdge(ftxFutures,fundingDict,'FTT',ftxFTTBasis) - oneDayShortSpotEdge)
  d['bnBTCPrem'] = (bnGetOneDayShortFutEdge(bn,fundingDict, 'BTC',bnBTCBasis) - oneDayShortSpotEdge)
  d['bnETHPrem'] = (bnGetOneDayShortFutEdge(bn,fundingDict, 'ETH',bnETHBasis) - oneDayShortSpotEdge)
  d['bbBTCPrem'] = (bbGetOneDayShortFutEdge(bbTickers,fundingDict, 'BTC',bbBTCBasis) - oneDayShortSpotEdge)
  d['bbETHPrem'] = (bbGetOneDayShortFutEdge(bbTickers,fundingDict, 'ETH',bbETHBasis) - oneDayShortSpotEdge)
  return d

#############################################################################################

##############
# CryptoTrader
##############
def cryptoTraderInit(config):
  ftx=ftxCCXTInit()
  bn = bnCCXTInit()
  bb = bbCCXTInit()
  ftxWallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main'])
  ftxWallet['Ccy']=ftxWallet['coin']
  ftxWallet['SpotDelta']=ftxWallet['total']
  ftxWallet=ftxWallet.set_index('Ccy').loc[['BTC','ETH','FTT','USD']]
  spotBTC = ftxWallet.loc['BTC', 'usdValue'] / ftxWallet.loc['BTC', 'total']
  spotETH = ftxWallet.loc['ETH', 'usdValue'] / ftxWallet.loc['ETH', 'total']
  spotFTT = ftxWallet.loc['FTT', 'usdValue'] / ftxWallet.loc['FTT', 'total']
  trade_btc = np.min([np.min([CT_TRADE_BTC_NOTIONAL,CT_MAX_NOTIONAL])/spotBTC,CT_MAX_BTC])
  trade_eth = np.min([np.min([CT_TRADE_ETH_NOTIONAL,CT_MAX_NOTIONAL])/spotETH,CT_MAX_ETH])
  trade_ftt = np.min([np.min([CT_TRADE_FTT_NOTIONAL,CT_MAX_NOTIONAL])/spotFTT,CT_MAX_FTT])
  trade_btc_notional = trade_btc*spotBTC
  trade_eth_notional = trade_eth*spotETH
  trade_ftt_notional = trade_ftt*spotFTT
  qty_dict=dict()
  qty_dict['BTC']=trade_btc
  qty_dict['ETH']=trade_eth
  qty_dict['FTT']=trade_ftt
  notional_dict=dict()
  notional_dict['BTC']=trade_btc_notional
  notional_dict['ETH']=trade_eth_notional
  notional_dict['FTT']=trade_ftt_notional

  printHeader('CryptoTrader')
  print('Qtys:     ',qty_dict)
  print('Notionals:',notional_dict)
  print()

  futExch, ccy, isSellPrem, premTgtBps = CT_CONFIGS_DICT[config]
  if not futExch in ['ftx', 'bn', 'bb']:
    print('Invalid futExch!')
    sys.exit(1)
  if not ccy in ['BTC', 'ETH', 'FTT']:
    print('Invalid ccy!')
    sys.exit(1)
  trade_qty = qty_dict[ccy]
  trade_notional = notional_dict[ccy]

  return ftx,bn,bb,futExch,ccy,isSellPrem,premTgtBps,trade_qty,trade_notional

def cryptoTraderRun(config):
  ftx, bn, bb, futExch, ccy, isSellPrem, premTgtBps, trade_qty, trade_notional = cryptoTraderInit(config)
  for i in range(CT_NPROGRAMS):
    status = 0
    while True:
      d = getPremDict(ftx, bn, bb)
      premBps = d[futExch + ccy + 'Prem'] * 10000
      z = ('Program ' + str(i + 1) + ': ').rjust(15)
      if (isSellPrem and premBps > premTgtBps) or (not isSellPrem and premBps < premTgtBps):
        status += 1
        z += ('(' + str(status) + ') ').rjust(10)
      else:
        status = 0
        z += ''.rjust(10)
      z += termcolor.colored(ccy + ' Premium (' + futExch + '): ' + str(round(premBps)) + 'bps', 'blue')
      print(z.ljust(30).rjust(40).ljust(70) + termcolor.colored('Target: ' + str(round(premTgtBps)) + 'bps', 'red'))
      if status >= CT_NOBS:
        speak('Trading')
        print()
        if isSellPrem:  # i.e., selling premium
          ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty)  # FTX Spot Buy (Maker)
          if futExch == 'ftx':
            ftxRelOrder('SELL', ftx, ccy + '-PERP', trade_qty)  # FTX Fut Sell (Maker)
          elif futExch == 'bn':
            bnMarketOrder('SELL', bn, ccy, trade_notional)  # Binance Fut Sell (Taker)
          else:
            bbRelOrder('SELL', bb, ccy, trade_notional)  # Bybit Fut Sell (Maker)
        else:  # i.e., buying premium
          ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty)  # FTX Spot Sell (Maker)
          if futExch == 'ftx':
            ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_qty)  # FTX Fut Buy (Maker)
          elif futExch == 'bn':
            bnMarketOrder('BUY', bn, ccy, trade_notional)  # Binance Fut Buy (Taker)
          else:
            bbRelOrder('BUY', bb, ccy, trade_notional)  # Bybit Fut Buy (Maker)
        print(getCurrentTime() + ': Done')
        print()
        speak('Done')
        break
      time.sleep(5)
  speak('All done')

#############################################################################################

#####
# Etc
#####
# Get current time
def getCurrentTime():
  return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

# Get mean over one day with exponential decay features
def getOneDayDecayedMean(current,terminal,halfLifeHours):
  values=[1.0 * (0.5**(1/halfLifeHours)) ** i for i in range(25)] # T0, T1 .... T24 (25 values)
  values=[i*(current-terminal)+terminal for i in values]
  return np.mean(values)

# Get percent of funding period that has elapsed
def getPctElapsed(hoursInterval):
  utcNow = datetime.datetime.utcnow()
  return (utcNow.hour * 3600 + utcNow.minute * 60 + utcNow.second) % (hoursInterval * 3600) / (hoursInterval * 3600)

# Print header
def printHeader(header=''):
  print()
  print('-' * 100)
  print()
  if len(header) > 0:
    print('['+header+']')
    print()

# Speak text
@retry
def speak(text):
  import win32com.client as wincl
  wincl.Dispatch("SAPI.SpVoice").Speak(text)