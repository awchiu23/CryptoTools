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

#######################################
# Params for CryptoTrader/CryptoAlerter
#######################################
CT_DEFAULT_BUY_TGT_BPS = -15
CT_DEFAULT_SELL_TGT_BPS = 15

CT_CONFIGS_DICT=dict()
CT_CONFIGS_DICT['FTX_BTC']=['ftx','BTC',CT_DEFAULT_BUY_TGT_BPS,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BN_BTC']=['bn','BTC',CT_DEFAULT_BUY_TGT_BPS,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BB_BTC']=['bb','BTC',CT_DEFAULT_BUY_TGT_BPS,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['FTX_ETH']=['ftx','ETH',CT_DEFAULT_BUY_TGT_BPS,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BN_ETH']=['bn','ETH',CT_DEFAULT_BUY_TGT_BPS,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['BB_ETH']=['bb','ETH',CT_DEFAULT_BUY_TGT_BPS,CT_DEFAULT_SELL_TGT_BPS]
CT_CONFIGS_DICT['FTX_FTT']=['ftx','FTT',CT_DEFAULT_BUY_TGT_BPS-15,CT_DEFAULT_SELL_TGT_BPS+15]

CT_NOBS = 5                    # Number of observations through target before triggering
CT_OBS_ALLOWED_BPS_RANGE = 10  # Max number of allowed bps for range of observations
CT_SLEEP = 3                   # Delay in seconds between observations
CT_NPROGRAMS = 10              # Number of programs (each program being a pair of trades)

CT_TRADE_BTC_NOTIONAL = 3000  # Per trade notional
CT_TRADE_ETH_NOTIONAL = 3000   # Per trade notional
CT_TRADE_FTT_NOTIONAL = 1000   # Per trade notional

CT_MAX_NOTIONAL = 50000        # Hard limit
CT_MAX_BTC = 0.5               # Hard limit
CT_MAX_ETH = 10                # Hard limit
CT_MAX_FTT = 100               # Hard limit

#############################################################################################

###############################
# Params for Smart Basis Models
###############################
HALF_LIFE_HOURS = 4                     # Half life of exponential decay in hours
BASE_USD_RATE = 0.25                    # Equilibrium USD rate P.A.
BASE_FUNDING_RATE_FTX = 0.25            # Equilibrium funding rate P.A.
BASE_FUNDING_RATE_BN = 0.30             # Equilibrium funding rate P.A.
BASE_FUNDING_RATE_BB = 0.35             # Equilibrium funding rate P.A.
BASE_BASIS = BASE_FUNDING_RATE_FTX/365  # Equilibrium future basis

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

@retry(wait_fixed=1000)
def ftxGetEstFunding(ftx, ccy):
  return ftx.public_get_futures_future_name_stats({'future_name': ccy+'-PERP'})['result']['nextFundingRate'] * 24 * 365

@retry(wait_fixed=1000)
def ftxGetEstBorrow(ftx):
  return pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365

@retry(wait_fixed=1000)
def ftxGetEstLending(ftx):
  return pd.DataFrame(ftx.private_get_spot_margin_lending_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365

def ftxRelOrder(side,ftx,ticker,trade_qty,maxChases=0):
  @retry(wait_fixed=1000)
  def ftxGetBid(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['bid']
  @retry(wait_fixed=1000)
  def ftxGetAsk(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['ask']
  @retry(wait_fixed=1000)
  def ftxGetRemainingSize(ftx,orderId):
    return ftx.private_get_orders_order_id({'order_id': orderId})['result']['remainingSize']
  @retry(wait_fixed=1000)
  def ftxGetFilledSize(ftx, orderId):
    return ftx.private_get_orders_order_id({'order_id': orderId})['result']['filledSize']
  @retry(wait_fixed=1000)
  def ftxGetFillPrice(ftx,orderId):
    return ftx.private_get_orders_order_id({'order_id': orderId})['result']['avgFillPrice']
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  if ticker[:3] == 'BTC':
    qty = round(trade_qty, 3)
  elif ticker[:3] == 'ETH':
    qty = round(trade_qty, 2)
  print(getCurrentTime()+': Sending FTX '+side+' order of '+ticker+' (qty='+str(round(qty,6))+') ....')
  if side=='BUY':
    limitPrice = ftxGetBid(ftx, ticker)
    orderId = ftx.create_limit_buy_order(ticker, qty, limitPrice)['info']['id']
  else:
    limitPrice = ftxGetAsk(ftx, ticker)
    orderId = ftx.create_limit_sell_order(ticker, qty, limitPrice)['info']['id']
  nChases=0
  while True:
    if ftxGetRemainingSize(ftx,orderId) == 0:
      break
    if side=='BUY':
      newPrice=ftxGetBid(ftx,ticker)
    else:
      newPrice=ftxGetAsk(ftx,ticker)
    if newPrice != limitPrice:
      limitPrice=newPrice
      nChases+=1
      if nChases>maxChases and ftxGetRemainingSize(ftx,orderId)==qty:
        ftx.private_delete_orders_order_id({'order_id':orderId})
        if ftxGetFilledSize(ftx,orderId)!=0:
          print('Cancelled order with non-zero quantity executed!')
          sys.exit(1)
        print(getCurrentTime() + ': Cancelled')
        return 0
      else:
        try:
          orderId=ftx.private_post_orders_order_id_modify({'order_id':orderId,'price':limitPrice})['result']['id']
        except:
          break
    time.sleep(1)
  fill=ftxGetFillPrice(ftx,orderId)
  print(getCurrentTime() + ': Last filled at '+str(round(fill,6)))
  return fill

#####

@retry(wait_fixed=1000)
def bnGetEstFunding(bn, ccy):
  return float(pd.DataFrame(bn.dapiPublic_get_premiumindex({'symbol': ccy+'USD_PERP'}))['lastFundingRate']) * 3 * 365

def bnRelOrder(side,bn,ccy,trade_notional,maxChases=0):
  @retry(wait_fixed=1000)
  def bnGetBid(bn, ticker):
    return float(bn.dapiPublicGetTickerBookTicker({'symbol':ticker})[0]['bidPrice'])
  @retry(wait_fixed=1000)
  def bnGetAsk(bn, ticker):
    return float(bn.dapiPublicGetTickerBookTicker({'symbol': ticker})[0]['askPrice'])
  @retry(wait_fixed=1000)
  def bnGetOrder(bn, ticker, orderId):
    return bn.dapiPrivate_get_order({'symbol': ticker, 'orderId': orderId})
  # Do not use @retry!
  def bnPlaceOrder(bn, ticker, side, qty, limitPrice):
    return bn.dapiPrivate_post_order({'symbol': ticker, 'side': side, 'type': 'LIMIT', 'quantity': qty, 'price': limitPrice, 'timeInForce': 'GTC'})['orderId']
  # Do not use @retry!
  def bnCancelOrder(bn, ticker, orderId):
    try:
      orderStatus=bn.dapiPrivate_delete_order({'symbol': ticker, 'orderId': orderId})
      if orderStatus['status']!='CANCELED':
        print('Order cancellation failed!')
        sys.exit(1)
      return orderStatus,float(orderStatus['origQty'])-float(orderStatus['executedQty'])
    except:
      orderStatus=bnGetOrder(bn, ticker, orderId)
      return orderStatus,0

  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  ticker=ccy+'USD_PERP'
  print(getCurrentTime() + ': Sending BN ' + side + ' order of ' + ticker + ' (notional=$'+ str(round(trade_notional))+') ....')
  if ccy=='BTC':
    qty=int(trade_notional/100)
  elif ccy=='ETH':
    qty=int(trade_notional/10)
  else:
    sys.exit(1)
  if side == 'BUY':
    limitPrice = bnGetBid(bn, ticker)
  else:
    limitPrice = bnGetAsk(bn, ticker)
  orderId=bnPlaceOrder(bn, ticker, side, qty, limitPrice)
  nChases=0
  while True:
    orderStatus = bnGetOrder(bn, ticker, orderId)
    if orderStatus['status']=='FILLED':
      break
    if side=='BUY':
      newPrice=bnGetBid(bn,ticker)
    else:
      newPrice=bnGetAsk(bn,ticker)
    if newPrice != limitPrice:
      limitPrice = newPrice
      nChases+=1
      orderStatus,leavesQty=bnCancelOrder(bn,ticker,orderId)
      if nChases>maxChases and leavesQty==qty:
        print(getCurrentTime() + ': Cancelled')
        return 0
      elif leavesQty==0:
        break
      else:
        orderId=bnPlaceOrder(bn, ticker, side, leavesQty, limitPrice)
    time.sleep(1)
  fill=float(orderStatus['avgPrice'])
  print(getCurrentTime() + ': Total filled at ' + str(round(fill, 6)))
  return fill

#####

@retry(wait_fixed=1000)
def bbGetEstFunding1(bb,ccy):
  return float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': ccy+'USD'})['result']['funding_rate']) * 3 * 365

@retry(wait_fixed=1000)
def bbGetEstFunding2(bb, ccy):
  return bb.v2PrivateGetFundingPredictedFunding({'symbol': ccy+'USD'})['result']['predicted_funding_rate'] * 3 * 365

def bbRelOrder(side,bb,ccy,trade_notional,maxChases=0):
  @retry(wait_fixed=1000)
  def bbGetBid(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['bid_price'])
  @retry(wait_fixed=1000)
  def bbGetAsk(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['ask_price'])
  @retry(wait_fixed=1000)
  def bbGetOrder(bb,ticker,orderId):
    result=bb.v2_private_get_order({'symbol': ticker, 'orderid': orderId})['result']
    if len(result)==0:
      return 0
    else:
      return result[0]
  @retry(wait_fixed=1000)
  def bbGetFillPrice(bb, ticker, orderId):
    df = pd.DataFrame(bb.v2_private_get_execution_list({'symbol': ticker, 'order_id': orderId})['result']['trade_list'])
    df['exec_qty'] = [float(n) for n in df['exec_qty']]
    df['exec_price'] = [float(n) for n in df['exec_price']]
    return (df['exec_qty'] * df['exec_price']).sum() / df['exec_qty'].sum()
  #####
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
  nChases=0
  while True:
    orderStatus=bbGetOrder(bb,ticker2,orderId)
    if orderStatus==0: # If order doesn't exist, it means all executed
      break
    if side=='BUY':
      newPrice=bbGetBid(bb,ticker1)
    else:
      newPrice=bbGetAsk(bb,ticker1)
    if newPrice != limitPrice:
      limitPrice = newPrice
      nChases+=1
      orderStatus = bbGetOrder(bb, ticker2, orderId)
      if orderStatus == 0:  # If order doesn't exist, it means all executed
        break
      if nChases>maxChases and orderStatus['cum_exec_qty']==0:
        if bb.v2_private_post_order_cancel({'symbol': ticker2, 'order_id': orderId})['result']['cum_exec_qty'] > 0:
          print('Cancelled order with non-zero quantity executed!')
          sys.exit(1)
        else:
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        try:
          bb.v2_private_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': limitPrice})
        except:
          break
    time.sleep(1)
  fill=bbGetFillPrice(bb, ticker2, orderId)
  print(getCurrentTime() + ': Total filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

####################
# Smart basis models
####################
def getFundingDict(ftx,bn,bb,isSkipBN=False,isSkipBB=False):
  d=dict()
  d['ftxEstBorrow'] = ftxGetEstBorrow(ftx)
  d['ftxEstLending'] = ftxGetEstLending(ftx)
  d['ftxEstFundingBTC'] = ftxGetEstFunding(ftx, 'BTC')
  d['ftxEstFundingETH'] = ftxGetEstFunding(ftx, 'ETH')
  d['ftxEstFundingFTT'] = ftxGetEstFunding(ftx, 'FTT')
  if not isSkipBN:
    d['bnEstFundingBTC'] = bnGetEstFunding(bn, 'BTC')
    d['bnEstFundingETH'] = bnGetEstFunding(bn, 'ETH')
  if not isSkipBB:
    d['bbEstFunding1BTC'] = bbGetEstFunding1(bb, 'BTC')
    d['bbEstFunding1ETH'] = bbGetEstFunding1(bb, 'ETH')
    d['bbEstFunding2BTC'] = bbGetEstFunding2(bb, 'BTC')
    d['bbEstFunding2ETH'] = bbGetEstFunding2(bb, 'ETH')
  return d

def getOneDayShortSpotEdge(fundingDict):
  usdRate=(fundingDict['ftxEstBorrow']+fundingDict['ftxEstLending'])/2
  return getOneDayDecayedMean(usdRate,BASE_USD_RATE,HALF_LIFE_HOURS)/365

def getOneDayShortFutEdge(hoursInterval,basis,snapFundingRate,baseFundingRate,estFundingRate,pctElapsedPower=1,prevFundingRate=None):
  # gain on projected basis mtm after 1 day
  edge=basis-getOneDayDecayedValues(basis,BASE_BASIS,HALF_LIFE_HOURS)[-1]

  # gain on coupon from elapsed time
  edge += estFundingRate / 365 / (24 / hoursInterval) * (getPctElapsed(hoursInterval) ** pctElapsedPower)
  hoursAccountedFor=getPctElapsed(hoursInterval)*hoursInterval

  # gain on coupon from previous reset (bb)
  if not prevFundingRate is None:
    edge+=prevFundingRate/365/(24/hoursInterval)
    hoursAccountedFor+=hoursInterval

  # gain on projected funding pickup
  nMinutes = 1440 - round(hoursAccountedFor * 60)
  edge+=getOneDayDecayedMean(snapFundingRate,baseFundingRate,HALF_LIFE_HOURS,nMinutes=nMinutes)/365

  return edge

@retry(wait_fixed=1000)
def ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, ccy, basis):
  if not hasattr(ftxGetOneDayShortFutEdge,'emaBTC'):
    ftxGetOneDayShortFutEdge.emaBTC = fundingDict['ftxEstFundingBTC']
  if not hasattr(ftxGetOneDayShortFutEdge, 'emaETH'):
    ftxGetOneDayShortFutEdge.emaETH = fundingDict['ftxEstFundingETH']
  if not hasattr(ftxGetOneDayShortFutEdge, 'emaFTT'):
    ftxGetOneDayShortFutEdge.emaFTT = fundingDict['ftxEstFundingFTT']
  df=ftxFutures.loc[ccy+'-PERP']
  snapFundingRate=(df['mark'] / df['index'] - 1)*365
  k=2/(300+1)
  if ccy=='BTC':
    ftxGetOneDayShortFutEdge.emaBTC = snapFundingRate * k + ftxGetOneDayShortFutEdge.emaBTC * (1 - k)
    smoothedSnapFundingRate=ftxGetOneDayShortFutEdge.emaBTC
  elif ccy=='ETH':
    ftxGetOneDayShortFutEdge.emaETH = snapFundingRate * k + ftxGetOneDayShortFutEdge.emaETH * (1 - k)
    smoothedSnapFundingRate = ftxGetOneDayShortFutEdge.emaETH
  elif ccy=='FTT':
    ftxGetOneDayShortFutEdge.emaFTT = snapFundingRate * k + ftxGetOneDayShortFutEdge.emaFTT * (1 - k)
    smoothedSnapFundingRate = ftxGetOneDayShortFutEdge.emaFTT
  else:
    sys.exit(1)
  return getOneDayShortFutEdge(1,basis,smoothedSnapFundingRate,BASE_FUNDING_RATE_FTX,fundingDict['ftxEstFunding' + ccy])

@retry(wait_fixed=1000)
def bnGetOneDayShortFutEdge(bn, fundingDict, ccy, basis):
  premIndex=np.mean([float(n) for n in pd.DataFrame(bn.dapiData_get_basis({'pair':ccy+'USD','contractType':'PERPETUAL','period':'5m'}))[-3:]['basisRate']])
  premIndex=premIndex+np.clip(0.0001-premIndex,-0.0005,0.0005)
  snapFundingRate=premIndex*365
  return getOneDayShortFutEdge(8, basis,snapFundingRate,BASE_FUNDING_RATE_BN, fundingDict['bnEstFunding' + ccy], pctElapsedPower=2)

@retry(wait_fixed=1000)
def bbGetOneDayShortFutEdge(bb, fundingDict, ccy, basis):
  start_time = int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(minutes=15))))
  premIndex=np.mean([float(n) for n in pd.DataFrame(bb.v2_public_get_premium_index_kline({'symbol':ccy+'USD','interval':'1','from':start_time})['result'])['close']])
  premIndex = premIndex + np.clip(0.0001 - premIndex, -0.0005, 0.0005)
  snapFundingRate=premIndex*365
  return getOneDayShortFutEdge(8, basis, snapFundingRate, BASE_FUNDING_RATE_BB, fundingDict['bbEstFunding2' + ccy], prevFundingRate=fundingDict['bbEstFunding1'+ccy])

def getSmartBasisDict(ftx, bn, bb, fundingDict, isSkipBN=False, isSkipBB=False):
  @retry(wait_fixed=1000)
  def ftxGetMarkets(ftx):
    return pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')
  #####
  @retry(wait_fixed=1000)
  def ftxGetFutures(ftx):
    return pd.DataFrame(ftx.public_get_futures()['result']).set_index('name')
  #####
  def ftxGetMid(ftxMarkets, name):
    return (ftxMarkets.loc[name,'bid'] + ftxMarkets.loc[name,'ask']) / 2
  #####
  @retry(wait_fixed=1000)
  def bnGetBookTicker(bn):
    return pd.DataFrame(bn.dapiPublicGetTickerBookTicker()).set_index('symbol')
  #####
  def bnGetMid(bnBookTicker, ccy):
    return (float(bnBookTicker.loc[ccy+'USD_PERP','bidPrice']) + float(bnBookTicker.loc[ccy+'USD_PERP','askPrice'])) / 2
  #####
  @retry(wait_fixed=1000)
  def bbGetTickers(bb):
    return pd.DataFrame(bb.v2PublicGetTickers()['result']).set_index('symbol')
  #####
  def bbGetMid(bbTickers, ccy):
    return (float(bbTickers.loc[ccy,'bid_price']) + float(bbTickers.loc[ccy,'ask_price'])) / 2
  #####
  oneDayShortSpotEdge = getOneDayShortSpotEdge(fundingDict)
  ftxMarkets = ftxGetMarkets(ftx)
  ftxFutures = ftxGetFutures(ftx)
  spotBTC = ftxGetMid(ftxMarkets, 'BTC/USD')
  spotETH = ftxGetMid(ftxMarkets, 'ETH/USD')
  spotFTT = ftxGetMid(ftxMarkets, 'FTT/USD')
  d = dict()
  d['ftxBTCBasis'] = ftxGetMid(ftxMarkets, 'BTC-PERP') / spotBTC - 1
  d['ftxETHBasis'] = ftxGetMid(ftxMarkets, 'ETH-PERP') / spotETH - 1
  d['ftxFTTBasis'] = ftxGetMid(ftxMarkets, 'FTT-PERP') / spotFTT - 1
  d['ftxBTCSmartBasis'] = (ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, 'BTC', d['ftxBTCBasis']) - oneDayShortSpotEdge)
  d['ftxETHSmartBasis'] = (ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, 'ETH', d['ftxETHBasis']) - oneDayShortSpotEdge)
  d['ftxFTTSmartBasis'] = (ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, 'FTT', d['ftxFTTBasis']) - oneDayShortSpotEdge)
  #####
  if not isSkipBN:
    bnBookTicker = bnGetBookTicker(bn)
    d['bnBTCBasis'] = bnGetMid(bnBookTicker, 'BTC') / spotBTC - 1
    d['bnETHBasis'] = bnGetMid(bnBookTicker, 'ETH') / spotETH - 1
    d['bnBTCSmartBasis'] = (bnGetOneDayShortFutEdge(bn, fundingDict, 'BTC', d['bnBTCBasis']) - oneDayShortSpotEdge)
    d['bnETHSmartBasis'] = (bnGetOneDayShortFutEdge(bn, fundingDict, 'ETH', d['bnETHBasis']) - oneDayShortSpotEdge)
  ####
  if not isSkipBB:
    bbTickers = bbGetTickers(bb)
    d['bbBTCBasis'] = bbGetMid(bbTickers, 'BTCUSD') / spotBTC - 1
    d['bbETHBasis'] = bbGetMid(bbTickers, 'ETHUSD') / spotETH - 1
    d['bbBTCSmartBasis'] = (bbGetOneDayShortFutEdge(bb,fundingDict, 'BTC',d['bbBTCBasis']) - oneDayShortSpotEdge)
    d['bbETHSmartBasis'] = (bbGetOneDayShortFutEdge(bb,fundingDict, 'ETH',d['bbETHBasis']) - oneDayShortSpotEdge)
  return d

#############################################################################################

##############
# CryptoTrader
##############
def cryptoTraderRun(config):
  def printTradeStats(spotFill, futFill, mult, obsBasisBps, realizedBasisBps, realizedSlippageBps, savedMults):
    b=(futFill/spotFill-1)*10000
    s= mult * (b - obsBasisBps)
    print(getCurrentTime() +   ': Realized basis        = ' + str(round(b))+'bps')
    print(getCurrentTime() +   ': Realized slippage     = ' + str(round(s))+'bps')
    realizedBasisBps.append(b)
    realizedSlippageBps.append(s)
    savedMults.append(mult)
    if len(realizedBasisBps) > 1:
      if np.sum(savedMults)!=0:
        products=[]
        for n1,n2 in zip(realizedBasisBps,savedMults):
          products.append(n1*n2)
        print(getCurrentTime() + ': Avg realized basis    = ' + str(round(np.sum(products)/np.sum(savedMults))) + 'bps')
      print(getCurrentTime() + ': Avg realized slippage = ' + str(round(np.mean(realizedSlippageBps))) + 'bps')
    return realizedBasisBps,realizedSlippageBps,savedMults
  #####
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

  futExch, ccy, buyTgtBps, sellTgtBps = CT_CONFIGS_DICT[config]
  if not futExch in ['ftx', 'bn', 'bb']:
    print('Invalid futExch!')
    sys.exit(1)
  if not ccy in ['BTC', 'ETH', 'FTT']:
    print('Invalid ccy!')
    sys.exit(1)
  trade_qty = qty_dict[ccy]
  trade_notional = notional_dict[ccy]

  ###########
  # Main loop
  ###########
  prevSmartBasis = []
  realizedBasisBps = []
  realizedSlippageBps = []
  savedMults = []
  for i in range(CT_NPROGRAMS):
    status = 0
    while True:
      fundingDict=getFundingDict(ftx, bn, bb,isSkipBN=futExch!='bn',isSkipBB=futExch!='bb')
      smartBasisDict= getSmartBasisDict(ftx, bn, bb, fundingDict, isSkipBN=futExch != 'bn', isSkipBB=futExch != 'bb')
      prefix=futExch+ccy
      smartBasisBps = smartBasisDict[prefix + 'SmartBasis'] * 10000
      basisBps      = smartBasisDict[prefix + 'Basis'] * 10000
      prevSmartBasis.append(smartBasisBps)
      prevSmartBasis=prevSmartBasis[-CT_NOBS:]
      isStable=(np.max(prevSmartBasis)-np.min(prevSmartBasis)) <= CT_OBS_ALLOWED_BPS_RANGE
      z = ('Program ' + str(i + 1) + ':').ljust(20)
      if smartBasisBps<=buyTgtBps and status<=0:
        status-=1
      elif smartBasisBps>=sellTgtBps and status>=0:
        status+=1
      else:
        status=0
      if status==0:
        z += '  '
      else:
        z += termcolor.colored(str(status).rjust(2), 'red')
      z += ' '+termcolor.colored((ccy + ' (' + futExch + ') smart/raw basis: ' + str(round(smartBasisBps)) + '/' + str(round(basisBps)) + 'bps').ljust(45), 'blue')
      print(z + termcolor.colored('Targets: ' + str(round(buyTgtBps)) +'/' +str(round(sellTgtBps))+'bps', 'magenta'))

      if abs(status) >= CT_NOBS and isStable:
        isDone = False
        print()
        if status>0:
          speak('Entering')
          mult = -1

          if futExch == 'ftx':
            spotFill=ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty)  # FTX Spot Buy (Maker)
            if spotFill!=0:
              futFill=ftxRelOrder('SELL', ftx, ccy + '-PERP', trade_qty,maxChases=888)  # FTX Fut Sell (Maker)
              isDone=True
          elif futExch == 'bn':
            futFill = bnRelOrder('SELL', bn, ccy, trade_notional)  # Binance Fut Sell (Taker)
            if futFill!=0:
              spotFill=ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty,maxChases=888)  # FTX Spot Buy (Maker)
              isDone=True
          else:
            futFill=bbRelOrder('SELL', bb, ccy, trade_notional)  # Bybit Fut Sell (Maker)
            if futFill!=0:
              spotFill=ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty,maxChases=888)  # FTX Spot Buy (Maker)
              isDone=True
        else:
          speak('Unwinding')
          mult = 1
          if futExch == 'ftx':
            spotFill=ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty)  # FTX Spot Sell (Maker)
            if spotFill != 0:
              futFill=ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_qty, maxChases=888)  # FTX Fut Buy (Maker)
              isDone = True
          elif futExch == 'bn':
            futFill = bnRelOrder('BUY', bn, ccy, trade_notional)  # Binance Fut Buy (Taker)
            if futFill!=0:
              spotFill=ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty, maxChases=888)  # FTX Spot Sell (Maker)
              isDone = True
          else:
            futFill=bbRelOrder('BUY', bb, ccy, trade_notional)  # Bybit Fut Buy (Maker)
            if futFill!=0:
              spotFill=ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty, maxChases=888)  # FTX Spot Sell (Maker)
              isDone = True
        if not isDone:
          status=status-np.sign(status)*2
          print()
          speak('Cancelled')
        else:
          realizedBasisBps, realizedSlippageBps, savedMults = printTradeStats(spotFill, futFill, mult, basisBps, realizedBasisBps, realizedSlippageBps,savedMults)
          print(getCurrentTime() + ': Done')
          print()
          speak('Done')
          break
      time.sleep(CT_SLEEP)

  speak('All done')

#############################################################################################

#####
# Etc
#####
# Get current time
def getCurrentTime():
  return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

# Get values over next 1440 minutes (one day) with exponential decay features
def getOneDayDecayedValues(current,terminal,halfLifeHours):
  halfLifeMinutes=halfLifeHours*60
  values = [1.0 * (0.5 ** (1 / halfLifeMinutes)) ** i for i in range(1,1441)]  # 1min, 2min .... 1440mins
  values = [i * (current - terminal) + terminal for i in values]
  return values

# Get mean over next specified minutes with exponential decay features
def getOneDayDecayedMean(current,terminal,halfLifeHours,nMinutes=1440):
  return np.mean(getOneDayDecayedValues(current,terminal,halfLifeHours)[:nMinutes])

# Get percent of funding period that has elapsed
def getPctElapsed(hoursInterval):
  utcNow = datetime.datetime.utcnow()
  return (utcNow.hour * 3600 + utcNow.minute * 60 + utcNow.second) % (hoursInterval * 3600) / (hoursInterval * 3600)

# Print dictionary
def printDict(d, indent=0, isSort=True):
  keys=d.keys()
  if isSort:
    keys=sorted(keys)
  for key in keys:
    value=d[key]
    print('\t' * indent + str(key))
    if isinstance(value, dict):
      printDict(value, indent + 1, isSort=isSort)
    else:
      print('\t' * (indent + 1) + str(value))

# Print header
def printHeader(header=''):
  print()
  print('-' * 100)
  print()
  if len(header) > 0:
    print('['+header+']')
    print()

# Sleep until time chosen
def sleepUntil(h, m, s):
  t = datetime.datetime.today()
  future = datetime.datetime(t.year, t.month, t.day, h, m, s)
  if future < t:
    future += datetime.timedelta(days=1)
  fmt = '%Y-%m-%d %H:%M:%S'
  print('Current time is', t.strftime(fmt))
  print('Sleeping until ', future.strftime(fmt), '....')
  print('')
  time.sleep((future - t).seconds+1)

# Speak text
@retry(wait_fixed=1000)
def speak(text):
  import win32com.client as wincl
  wincl.Dispatch("SAPI.SpVoice").Speak(text)