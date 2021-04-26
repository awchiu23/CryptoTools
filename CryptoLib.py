################
# Crypto Library
################
from CryptoParams import *
from joblib import Parallel, delayed
import pandas as pd
import numpy as np
import datetime
import sys
import time
import operator
import termcolor
import ccxt
from ccxt.base.errors import RateLimitExceeded
import apophis
from retrying import retry

#########
# Classes
#########
class getPrices:
  def __init__(self, exch, api, ccy):
    self.exch = exch
    self.api = api
    self.ccy = ccy

  def run(self):
    if self.exch == 'ftx':
      self.spot = ftxGetMid(self.api, self.ccy+'/USD')      
      self.fut = ftxGetMid(self.api, self.ccy+'-PERP')
      self.spotUSDT = ftxGetMid(self.api, 'USDT/USD')
    elif self.exch == 'bb':
      self.fut=self.bbGetMid(self.api,self.ccy)
    elif self.exch == 'bbt':
      self.fut=self.bbtGetMid(self.api,self.ccy)
    elif self.exch == 'bn':
      self.fut = self.bnGetMid(self.api,self.ccy)
    elif self.exch == 'bnt':
      self.fut = self.bntGetMid(self.api,self.ccy)
    elif self.exch == 'db':
      self.fut =  self.dbGetMid(self.api,self.ccy)
    elif self.exch == 'kf':
      self.kfTickers = kfGetTickers(self.api)
      self.fut = self.kfGetMid(self.kfTickers,self.ccy)

  @retry(wait_fixed=1000)
  def bbGetMid(self, bb, ccy):
    d = bb.v2PublicGetTickers({'symbol': ccy + 'USD'})['result'][0]
    return (float(d['bid_price']) + float(d['ask_price'])) / 2

  @retry(wait_fixed=1000)
  def bbtGetMid(self, bb, ccy):
    d = bb.v2PublicGetTickers({'symbol': ccy + 'USDT'})['result'][0]
    return (float(d['bid_price']) + float(d['ask_price'])) / 2

  @retry(wait_fixed=1000)
  def bnGetMid(self, bn, ccy):
    d=bn.dapiPublicGetTickerBookTicker({'symbol':ccy+'USD_PERP'})[0]
    return (float(d['bidPrice']) + float(d['askPrice'])) / 2

  @retry(wait_fixed=1000)
  def bntGetMid(self, bn, ccy):
    d = bn.fapiPublic_get_ticker_bookticker({'symbol': ccy + 'USDT'})
    return (float(d['bidPrice']) + float(d['askPrice'])) / 2

  @retry(wait_fixed=1000)
  def dbGetMid(self, db,ccy):
    d=db.public_get_ticker({'instrument_name': ccy+'-PERPETUAL'})['result']
    return (float(d['best_bid_price'])+float(d['best_ask_price']))/2

  # Do not use @retry
  def kfGetMid(self, kfTickers, ccy):
    ticker=kfCcyToSymbol(ccy)
    return (kfTickers.loc[ticker, 'bid'] + kfTickers.loc[ticker, 'ask']) / 2

###########
# Functions
###########
def ftxCCXTInit():
  return ccxt.ftx({'apiKey': API_KEY_FTX, 'secret': API_SECRET_FTX, 'enableRateLimit': True})

def bbCCXTInit():
  return ccxt.bybit({'apiKey': API_KEY_BB, 'secret': API_SECRET_BB, 'enableRateLimit': True})

def bnCCXTInit():
  return  ccxt.binance({'apiKey': API_KEY_BN, 'secret': API_SECRET_BN, 'enableRateLimit': True})

def dbCCXTInit():
  return ccxt.deribit({'apiKey': API_KEY_DB, 'secret': API_SECRET_DB, 'enableRateLimit': True, 'nonce': lambda: ccxt.Exchange.milliseconds()})

def kfInit():
  return apophis.Apophis(API_KEY_KF,API_SECRET_KF,True)

def krCCXTInit(n=1):
  return ccxt.kraken({'apiKey': globals()['API_KEY_KR'+str(n)], 'secret': globals()['API_SECRET_KR'+str(n)], 'enableRateLimit': False})

def cbCCXTInit():
  return ccxt.coinbase({'apiKey': API_KEY_CB, 'secret': API_SECRET_CB, 'enableRateLimit': True})

def getLimitPrice(exch,price,ccy,side):
  if exch == 'ftx':
    distanceToBestBps = CT_FTX_DISTANCE_TO_BEST_BPS
  elif exch == 'bb':
    distanceToBestBps = CT_BB_DISTANCE_TO_BEST_BPS
  elif exch == 'bbt':
    distanceToBestBps = CT_BBT_DISTANCE_TO_BEST_BPS
  elif exch == 'bn':
    distanceToBestBps = CT_BN_DISTANCE_TO_BEST_BPS
  elif exch == 'bnt':
    distanceToBestBps = CT_BNT_DISTANCE_TO_BEST_BPS
  elif exch == 'db':
    distanceToBestBps = CT_DB_DISTANCE_TO_BEST_BPS
  elif exch == 'kf':
    distanceToBestBps = CT_KF_DISTANCE_TO_BEST_BPS
  else:
    sys.exit(1)
  if side == 'BUY':
    mult = 1 + distanceToBestBps / 10000
  else:
    mult = 1 - distanceToBestBps / 10000
  return roundPrice(exch, price * mult, ccy)

def roundPrice(exch, price, ccy):
  if exch=='ftx':
    if ccy=='BTC':
      return round(price)
    else:
      return round(price,1)
  elif exch in 'bn':
    if ccy=='BTC':
      return round(price,1)
    else:
      return round(price,2)
  elif exch in 'bnt':
    return round(price,2)
  else:
    if ccy=='BTC':
      return round(price*2)/2
    else:
      return round(price*20)/20

#############################################################################################

@retry(wait_fixed=1000)
def ftxGetMid(ftx, name):
  d=ftx.public_get_markets_market_name({'market_name': name})['result']
  return (float(d['bid'])+float(d['ask']))/2

@retry(wait_fixed=1000)
def ftxGetWallet(ftx):
  wallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  dfSetFloat(wallet,wallet.columns)
  wallet['spot']=wallet['usdValue']/wallet['total']
  return wallet

@retry(wait_fixed=1000)
def ftxGetFutPos(ftx,ccy):
  df = pd.DataFrame(ftx.private_get_account()['result']['positions']).set_index('future')
  s=df.loc[ccy+'-PERP']
  pos=float(s['size'])
  if s['side']=='sell':
    pos*=-1
  return pos

@retry(wait_fixed=1000)
def ftxGetEstFunding(ftx, ccy):
  return float(ftx.public_get_futures_future_name_stats({'future_name': ccy+'-PERP'})['result']['nextFundingRate']) * 24 * 365

@retry(wait_fixed=1000)
def ftxGetEstBorrow(ftx, ccy=None):
  s=pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin')['estimate'].astype(float)*24*365
  if ccy is None:
    return s
  else:
    return s[ccy]

@retry(wait_fixed=1000)
def ftxGetEstLending(ftx, ccy=None):
  s=pd.DataFrame(ftx.private_get_spot_margin_lending_rates()['result']).set_index('coin')['estimate'].astype(float) * 24 * 365
  if ccy is None:
    return s
  else:
    return s[ccy]

def ftxGetSpotEUR(ftx):
  d = ftx.public_get_markets_market_name({'market_name': 'EUR/USD'})['result']
  return (float(d['bid']) + float(d['ask'])) / 2

def ftxRelOrder(side,ftx,ticker,trade_qty,maxChases=0):
  @retry(wait_fixed=1000)
  def ftxGetBid(ftx,ticker):
    return float(ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['bid'])
  @retry(wait_fixed=1000)
  def ftxGetAsk(ftx,ticker):
    return float(ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['ask'])
  @retry(wait_fixed=1000)
  def ftxGetRemainingSize(ftx,orderId):
    return float(ftx.private_get_orders_order_id({'order_id': orderId})['result']['remainingSize'])
  @retry(wait_fixed=1000)
  def ftxGetFilledSize(ftx, orderId):
    return float(ftx.private_get_orders_order_id({'order_id': orderId})['result']['filledSize'])
  @retry(wait_fixed=1000)
  def ftxGetFillPrice(ftx,orderId):
    return float(ftx.private_get_orders_order_id({'order_id': orderId})['result']['avgFillPrice'])
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  ccy=ticker[:3]
  if ccy == 'BTC':
    qty = round(trade_qty, 3)
  elif ccy == 'ETH':
    qty = round(trade_qty, 2)
  else:
    sys.exit(1)
  print(getCurrentTime()+': Sending FTX '+side+' order of '+ticker+' (qty='+str(qty)+') ....')
  if side == 'BUY':
    refPrice = ftxGetBid(ftx, ticker)
  else:
    refPrice = ftxGetAsk(ftx, ticker)
  limitPrice = getLimitPrice('ftx',refPrice,ccy,side)
  try:
    orderId = ftx.private_post_orders({'market': ticker, 'side': side.lower(), 'price': limitPrice, 'type': 'limit', 'size': qty})['result']['id']
  except RateLimitExceeded:
    print('RateLimitExceeded caught!')
    sys.exit(1)
  refTime = time.time()
  nChases=0
  while True:
    if ftxGetRemainingSize(ftx,orderId) == 0:
      break
    if side=='BUY':
      newRefPrice=ftxGetBid(ftx,ticker)
    else:
      newRefPrice=ftxGetAsk(ftx,ticker)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_MAX_WAIT_TIME):
      refPrice=newRefPrice
      nChases+=1
      if nChases>maxChases and ftxGetRemainingSize(ftx,orderId)==qty:
        mult=.95 if side == 'BUY' else 1.05
        farPrice = roundPrice('ftx', refPrice * mult,ccy)
        try:
          orderId = ftx.private_post_orders_order_id_modify({'order_id': orderId, 'price': farPrice})['result']['id']
        except:
          break
        if ftxGetRemainingSize(ftx, orderId) == qty:
          ftx.private_delete_orders_order_id({'order_id': orderId})
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        refTime=time.time()
        newLimitPrice=getLimitPrice('ftx',refPrice,ccy,side)
        if (side=='BUY' and newLimitPrice > limitPrice) or (side=='SELL' and newLimitPrice < limitPrice):
          limitPrice=newLimitPrice
          try:
            orderId=ftx.private_post_orders_order_id_modify({'order_id':orderId,'price':limitPrice})['result']['id']
          except:
            break
    time.sleep(1)
  fill=ftxGetFillPrice(ftx,orderId)
  print(getCurrentTime() + ': Filled at '+str(round(fill,6)))
  return fill

#############################################################################################

@retry(wait_fixed=1000)
def bbGetFutPos(bb,ccy):
  df = bb.v2_private_get_position_list()['result']
  df = pd.DataFrame([pos['data'] for pos in df]).set_index('symbol')
  s=df.loc[ccy+'USD']
  pos = float(s['size'])
  if s['side'] == 'Sell':
    pos *= -1
  return pos

@retry(wait_fixed=1000)
def bbGetEstFunding1(bb,ccy):
  return float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': ccy+'USD'})['result']['funding_rate']) * 3 * 365

@retry(wait_fixed=1000)
def bbGetEstFunding2(bb, ccy):
  return float(bb.v2PrivateGetFundingPredictedFunding({'symbol': ccy+'USD'})['result']['predicted_funding_rate']) * 3 * 365

def bbRelOrder(side,bb,ccy,trade_notional,maxChases=0):
  @retry(wait_fixed=1000)
  def bbGetBid(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['bid_price'])
  @retry(wait_fixed=1000)
  def bbGetAsk(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['ask_price'])
  @retry(wait_fixed=1000)
  def bbGetOrder(bb,ticker,orderId):
    result=bb.v2_private_get_order({'symbol': ticker, 'order_id': orderId})['result']
    if len(result)==0:
      result=dict()
      result['orderStatus']='Filled'
    return result
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
  trade_notional = round(trade_notional)
  print(getCurrentTime() + ': Sending BB ' + side + ' order of ' + ticker1 + ' (notional=$'+ str(trade_notional)+') ....')
  if side=='BUY':
    refPrice = bbGetBid(bb, ticker1)
    limitPrice=getLimitPrice('bb',refPrice,ccy,side)
    orderId = bb.create_limit_buy_order(ticker1, trade_notional, limitPrice)['info']['order_id']
  else:
    refPrice = bbGetAsk(bb, ticker1)
    limitPrice=getLimitPrice('bb',refPrice,ccy,side)
    orderId = bb.create_limit_sell_order(ticker1, trade_notional, limitPrice)['info']['order_id']
  refTime = time.time()
  nChases=0
  while True:
    orderStatus=bbGetOrder(bb,ticker2,orderId)
    if orderStatus['order_status']=='Filled': break
    if side=='BUY':
      newRefPrice=bbGetBid(bb,ticker1)
    else:
      newRefPrice=bbGetAsk(bb,ticker1)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_MAX_WAIT_TIME):
      refPrice = newRefPrice
      nChases+=1
      orderStatus = bbGetOrder(bb, ticker2, orderId)
      if orderStatus['order_status']=='Filled': break
      if nChases>maxChases and float(orderStatus['cum_exec_qty'])==0:
        mult = .95 if side == 'BUY' else 1.05
        farPrice = roundPrice('bb',refPrice*mult,ccy)
        try:
          bb.v2_private_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': farPrice})
        except:
          break
        orderStatus = bbGetOrder(bb, ticker2, orderId)
        if float(orderStatus['cum_exec_qty']) == 0:
          bb.v2_private_post_order_cancel({'symbol': ticker2, 'order_id': orderId})
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        refTime = time.time()
        newLimitPrice=getLimitPrice('bb',refPrice,ccy,side)
        if (side == 'BUY' and newLimitPrice > limitPrice) or (side == 'SELL' and newLimitPrice < limitPrice):
          print(getCurrentTime() + ': [DEBUG: replace order; price=' + str(limitPrice)+'->'+str(newLimitPrice) + '; nChases=' + str(nChases) + ']')
          limitPrice=newLimitPrice
          try:
            bb.v2_private_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': limitPrice})
          except:
            break
        else:
          print(getCurrentTime() + ': [DEBUG: leave order alone; price='+str(limitPrice)+'; nChases=' + str(nChases)+']')
    time.sleep(1)
  fill=bbGetFillPrice(bb, ticker2, orderId)
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

@retry(wait_fixed=1000)
def bbtGetFutPos(bb,ccy):
  df=pd.DataFrame(bb.private_linear_get_position_list({'symbol':ccy+'USDT'})['result']).set_index('side')
  return float(df.loc['Buy','size'])-float(df.loc['Sell','size'])

@retry(wait_fixed=1000)
def bbtGetEstFunding1(bb,ccy):
  return float(bb.public_linear_get_funding_prev_funding_rate({'symbol': ccy+'USDT'})['result']['funding_rate'])*3*365

@retry(wait_fixed=1000)
def bbtGetEstFunding2(bb,ccy):
  return float(bb.private_linear_get_funding_predicted_funding({'symbol': ccy+'USDT'})['result']['predicted_funding_rate'])* 3 * 365

def bbtRelOrder(side,bb,ccy,trade_qty,maxChases=0):
  @retry(wait_fixed=1000)
  def bbtGetBid(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['bid_price'])
  @retry(wait_fixed=1000)
  def bbtGetAsk(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['ask_price'])
  @retry(wait_fixed=1000)
  def bbtGetOrder(bb,ticker,orderId):
    result=bb.private_linear_get_order_list({'symbol': ticker, 'order_id': orderId})['result']['data'][0]
    #if len(result)==0:
    #  result=dict()
    #  result['orderStatus']='Filled'
    return result
  # Do not use @retry!
  def bbtGetFillPrice(bb, ticker, orderId):
    orderStatus = bbtGetOrder(bb, ticker, orderId)
    cumExecValue=float(orderStatus['cum_exec_value'])
    cumExecQty=float(orderStatus['cum_exec_qty'])
    if cumExecQty==0:
      return 0
    else:
      return cumExecValue/cumExecQty
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  ticker1=ccy+'/USDT'
  ticker2=ccy+'USDT'
  qty = round(trade_qty, 3)
  print(getCurrentTime() + ': Sending BBT ' + side + ' order of ' + ticker1 + ' (qty='+ str(qty)+') ....')
  if side=='BUY':
    refPrice = bbtGetBid(bb, ticker1)
    limitPrice=getLimitPrice('bbt',refPrice,ccy,side)
    orderId = bb.create_limit_buy_order(ticker1, qty, limitPrice)['info']['order_id']
  else:
    refPrice = bbtGetAsk(bb, ticker1)
    limitPrice=getLimitPrice('bbt',refPrice,ccy,side)
    orderId = bb.create_limit_sell_order(ticker1, qty, limitPrice)['info']['order_id']
  refTime = time.time()
  nChases=0
  while True:
    orderStatus=bbtGetOrder(bb,ticker2,orderId)
    if orderStatus['order_status']=='Filled': break
    if side=='BUY':
      newRefPrice=bbtGetBid(bb,ticker1)
    else:
      newRefPrice=bbtGetAsk(bb,ticker1)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_MAX_WAIT_TIME):
      refPrice = newRefPrice
      nChases+=1
      orderStatus = bbtGetOrder(bb, ticker2, orderId)
      if orderStatus['order_status']=='Filled': break
      if nChases>maxChases and float(orderStatus['cum_exec_qty'])==0:
        mult = .95 if side == 'BUY' else 1.05
        farPrice = roundPrice('bbt',refPrice*mult,ccy)
        try:
          bb.private_linear_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': farPrice})
        except:
          break
        orderStatus = bbtGetOrder(bb, ticker2, orderId)
        if float(orderStatus['cum_exec_qty']) == 0:
          bb.private_linear_post_order_cancel({'symbol': ticker2, 'order_id': orderId})
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        refTime = time.time()
        newLimitPrice=getLimitPrice('bbt',refPrice,ccy,side)
        if (side == 'BUY' and newLimitPrice > limitPrice) or (side == 'SELL' and newLimitPrice < limitPrice):
          print(getCurrentTime() + ': [DEBUG: replace order; price=' + str(limitPrice)+'->'+str(newLimitPrice) + '; nChases=' + str(nChases) + ']')
          limitPrice=newLimitPrice
          try:
            bb.private_linear_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': limitPrice})
          except:
            break
        else:
          print(getCurrentTime() + ': [DEBUG: leave order alone; price='+str(limitPrice)+'; nChases=' + str(nChases)+']')
    time.sleep(1)
  fill=bbtGetFillPrice(bb, ticker2, orderId)
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

@retry(wait_fixed=1000)
def bnGetFutPos(bn,ccy):
  return float(pd.DataFrame(bn.dapiPrivate_get_positionrisk({'pair':ccy+'USD'})).set_index('symbol').loc[ccy + 'USD_PERP']['positionAmt'])

@retry(wait_fixed=1000)
def bnGetEstFunding(bn, ccy):
  return float(bn.dapiPublic_get_premiumindex({'symbol': ccy + 'USD_PERP'})[0]['lastFundingRate'])*3*365

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
    qty=round(trade_notional/100)
  elif ccy=='ETH':
    qty=round(trade_notional/10)
  else:
    sys.exit(1)
  if side == 'BUY':
    refPrice = bnGetBid(bn, ticker)
  else:
    refPrice = bnGetAsk(bn, ticker)
  limitPrice = getLimitPrice('bn', refPrice, ccy, side)
  orderId=bnPlaceOrder(bn, ticker, side, qty, limitPrice)
  refTime = time.time()
  nChases=0
  while True:
    orderStatus = bnGetOrder(bn, ticker, orderId)
    if orderStatus['status']=='FILLED':
      break
    if side=='BUY':
      newRefPrice=bnGetBid(bn,ticker)
    else:
      newRefPrice=bnGetAsk(bn,ticker)
    if (side == 'BUY' and newRefPrice > refPrice) or (side == 'SELL' and newRefPrice < refPrice) or ((time.time() - refTime) > CT_MAX_WAIT_TIME):
      refPrice=newRefPrice
      nChases+=1
      orderStatus,leavesQty=bnCancelOrder(bn,ticker,orderId)
      if nChases>maxChases and leavesQty==qty:
        print(getCurrentTime() + ': Cancelled')
        return 0
      elif leavesQty==0:
        break
      else:
        refTime = time.time()
        limitPrice = getLimitPrice('bn', refPrice, ccy, side)
        orderId=bnPlaceOrder(bn, ticker, side, leavesQty, limitPrice)
    time.sleep(1)
  fill=float(orderStatus['avgPrice'])
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

@retry(wait_fixed=1000)
def bntGetFutPos(bn, ccy):
  return float(bn.fapiPrivate_get_positionrisk({'symbol':ccy+'USDT'})[0]['positionAmt'])

@retry(wait_fixed=1000)
def bntGetEstFunding(bn, ccy):
  return float(bn.fapiPublic_get_premiumindex({'symbol': ccy + 'USDT'})['lastFundingRate']) * 3 * 365

def bntRelOrder(side, bn, ccy, trade_qty, maxChases=0):
  @retry(wait_fixed=1000)
  def bntGetBid(bn, ticker):
    return float(bn.fapiPublicGetTickerBookTicker({'symbol':ticker})['bidPrice'])
  @retry(wait_fixed=1000)
  def bntGetAsk(bn, ticker):
    return float(bn.fapiPublicGetTickerBookTicker({'symbol':ticker})['askPrice'])
  @retry(wait_fixed=1000)
  def bntGetOrder(bn, ticker, orderId):
    return bn.fapiPrivate_get_order({'symbol': ticker, 'orderId': orderId})
  # Do not use @retry!
  def bntPlaceOrder(bn, ticker, side, qty, limitPrice):
    print(getCurrentTime() + ': [DEBUG: place order; qty=' + str(qty)+' price=' + str(limitPrice) + ']')
    return bn.fapiPrivate_post_order({'symbol': ticker, 'side': side, 'type': 'LIMIT', 'quantity': qty, 'price': limitPrice, 'timeInForce': 'GTC'})['orderId']
  # Do not use @retry!
  def bntCancelOrder(bn, ticker, orderId):
    try:
      orderStatus=bn.fapiPrivate_delete_order({'symbol': ticker, 'orderId': orderId})
      if orderStatus['status']!='CANCELED':
        print('Order cancellation failed!')
        sys.exit(1)
      return orderStatus,float(orderStatus['origQty'])-float(orderStatus['executedQty'])
    except:
      orderStatus=bntGetOrder(bn, ticker, orderId)
      return orderStatus,0
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  ticker=ccy+'USDT'
  qty = round(trade_qty, 3)
  print(getCurrentTime()+': Sending BNT '+side+' order of '+ticker+' (qty='+str(qty)+') ....')
  if side == 'BUY':
    refPrice = bntGetBid(bn, ticker)
  else:
    refPrice = bntGetAsk(bn, ticker)
  limitPrice = getLimitPrice('bnt', refPrice, ccy, side)
  orderId=bntPlaceOrder(bn, ticker, side, qty, limitPrice)
  refTime = time.time()
  nChases=0
  while True:
    orderStatus = bntGetOrder(bn, ticker, orderId)
    if orderStatus['status']=='FILLED':
      break
    if side=='BUY':
      newRefPrice=bntGetBid(bn,ticker)
    else:
      newRefPrice=bntGetAsk(bn,ticker)
    if (side == 'BUY' and newRefPrice > refPrice) or (side == 'SELL' and newRefPrice < refPrice) or ((time.time() - refTime) > CT_MAX_WAIT_TIME):
      refPrice=newRefPrice
      nChases+=1
      orderStatus,leavesQty=bntCancelOrder(bn,ticker,orderId)
      if nChases>maxChases and leavesQty==qty:
        print(getCurrentTime() + ': Cancelled')
        return 0
      elif leavesQty==0:
        break
      else:
        refTime = time.time()
        limitPrice = getLimitPrice('bnt', refPrice, ccy, side)
        orderId=bntPlaceOrder(bn, ticker, side, leavesQty, limitPrice)
    time.sleep(1)
  fill=float(orderStatus['avgPrice'])
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

@retry(wait_fixed=1000)
def dbGetFutPos(db,ccy):
  return float(db.private_get_get_position({'instrument_name': ccy + '-PERPETUAL'})['result']['size'])

@retry(wait_fixed=1000)
def dbGetEstFunding(db,ccy,mins=15):
  now=datetime.datetime.now()
  start_timestamp = int(datetime.datetime.timestamp(now - pd.DateOffset(minutes=mins)))*1000
  end_timestamp = int(datetime.datetime.timestamp(now))*1000
  return float(db.public_get_get_funding_rate_value({'instrument_name': ccy+'-PERPETUAL', 'start_timestamp': start_timestamp, 'end_timestamp': end_timestamp})['result'])*(60/mins)*24*365

def dbRelOrder(side,db,ccy,trade_notional,maxChases=0):
  @retry(wait_fixed=1000)
  def dbGetBid(db, ticker):
    d = db.public_get_ticker({'instrument_name': ticker})['result']
    return float(d['best_bid_price'])
  @retry(wait_fixed=1000)
  def dbGetAsk(db, ticker):
    d = db.public_get_ticker({'instrument_name': ticker})['result']
    return float(d['best_ask_price'])
  @retry(wait_fixed=1000)
  def dbGetOrder(db,orderId):
    return db.private_get_get_order_state({'order_id': orderId})['result']
  # Do not use @retry!
  def dbEditOrder(db, orderId, trade_notional, limitPrice):
    if dbGetOrder(db, orderId)['order_state'] == 'filled':
      return False
    try:
      db.private_get_edit({'order_id': orderId, 'amount': trade_notional, 'price': limitPrice})
      return True
    except:
      return False
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  if ccy=='BTC':
    trade_notional=round(trade_notional,-1)
  elif ccy=='ETH':
    trade_notional=round(trade_notional)
  else:
    sys.exit(1)
  ticker = ccy + '-PERPETUAL'
  print(getCurrentTime() + ': Sending DB ' + side + ' order of ' + ticker + ' (notional=$'+ str(trade_notional)+') ....')
  if side=='BUY':
    refPrice = dbGetBid(db, ticker)
    limitPrice = getLimitPrice('db', refPrice, ccy, side)
    orderId=db.private_get_buy({'instrument_name':ticker,'amount':trade_notional,'type':'limit','price':limitPrice})['result']['order']['order_id']
  else:
    refPrice = dbGetAsk(db, ticker)
    limitPrice = getLimitPrice('db', refPrice, ccy, side)
    orderId=db.private_get_sell({'instrument_name':ticker,'amount':trade_notional,'type':'limit','price':limitPrice})['result']['order']['order_id']
  refTime = time.time()
  nChases=0
  while True:
    if dbGetOrder(db, orderId)['order_state']=='filled':
      break
    if side=='BUY':
      newRefPrice=dbGetBid(db,ticker)
    else:
      newRefPrice=dbGetAsk(db,ticker)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_MAX_WAIT_TIME):
      refPrice = newRefPrice
      nChases+=1
      orderStatus = dbGetOrder(db, orderId)
      if orderStatus['order_state'] == 'filled':
        break
      if nChases>maxChases and float(orderStatus['filled_amount'])==0:
        mult = .98 if side == 'BUY' else 1.02
        farPrice = roundPrice('db', refPrice * mult, ccy)
        if not dbEditOrder(db, orderId, trade_notional, farPrice):
          break
        if float(dbGetOrder(db, orderId)['filled_amount'])==0:
          db.private_get_cancel({'order_id': orderId})
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        refTime = time.time()
        newLimitPrice = getLimitPrice('db', refPrice, ccy, side)
        if (side=='BUY' and newLimitPrice > limitPrice) or (side=='SELL' and newLimitPrice < limitPrice):
          limitPrice=newLimitPrice
          if not dbEditOrder(db, orderId, trade_notional, limitPrice):
            break
    time.sleep(1)
  fill=float(dbGetOrder(db, orderId)['average_price'])
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

def kfCcyToSymbol(ccy,isIndex=False):
  if isIndex:
    if ccy == 'BTC':
      return 'in_xbtusd'
    elif ccy == 'ETH':
      return 'in_ethusd'
    else:
      sys.exit(1)
  else:
    if ccy=='BTC':
      return 'pi_xbtusd'
    elif ccy=='ETH':
      return 'pi_ethusd'
    else:
      sys.exit(1)

@retry(wait_fixed=1000)
def kfGetFutPos(kf,ccy):
  symbol=kfCcyToSymbol(ccy)
  return kf.query('accounts')['accounts']['f'+symbol[1:]]['balances'][symbol]

@retry(wait_fixed=1000)
def kfGetTickers(kf):
  return pd.DataFrame(kf.query('tickers')['tickers']).set_index('symbol')

@retry(wait_fixed=1000)
def kfGetEstFunding1(kf,ccy,kfTickers=None):
  if kfTickers is None:
    kfTickers=kfGetTickers(kf)
  symbol=kfCcyToSymbol(ccy)
  return kfTickers.loc[symbol,'fundingRate']*kfTickers.loc[symbol,'markPrice']*24*365

@retry(wait_fixed=1000)
def kfGetEstFunding2(kf, ccy,kfTickers=None):
  if kfTickers is None:
    kfTickers = kfGetTickers(kf)
  symbol = kfCcyToSymbol(ccy)
  return kfTickers.loc[symbol, 'fundingRatePrediction']*kfTickers.loc[symbol,'markPrice']*24*365

def kfRelOrder(side,kf,ccy,trade_notional,maxChases=0):
  # Do not use @retry
  def kfGetBid(kf, symbol):
    return kfGetTickers(kf).loc[symbol,'bid']
  # Do not use @retry
  def kfGetAsk(kf, symbol):
    return kfGetTickers(kf).loc[symbol,'ask']
  @retry(wait_fixed=1000)
  def kfGetOrderStatus(kf, orderId):
    l = kf.query('openorders')['openOrders']
    if len(l)==0:
      return None
    else:
      df= pd.DataFrame(l).set_index('order_id')
      if orderId in df.index:
        return df.loc[orderId]
      else:
        return None
  # Do not use @retry
  def kfGetFillPrice(kf, orderId):
    df=pd.DataFrame(kf.query('fills')['fills']).set_index('order_id').loc[orderId]
    if isinstance(df, pd.Series):
      return df['price']
    else:
      df['value']=df['size']*df['price']
      return df['value'].sum()/df['size'].sum()
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  symbol=kfCcyToSymbol(ccy)
  trade_notional = round(trade_notional)
  print(getCurrentTime() + ': Sending KF ' + side + ' order of ' + symbol + ' (notional=$' + str(trade_notional) + ') ....')
  if side == 'BUY':
    refPrice = kfGetBid(kf, symbol)
  else:
    refPrice = kfGetAsk(kf, symbol)
  limitPrice = getLimitPrice('kf', refPrice, ccy, side)
  orderId=kf.query('sendorder',{'orderType':'lmt','symbol':symbol,'side':side.lower(),'size':trade_notional,'limitPrice':limitPrice})['sendStatus']['order_id']
  refTime=time.time()
  nChases=0
  while True:
    orderStatus=kfGetOrderStatus(kf,orderId)
    if orderStatus is None:  # If order doesn't exist, it means all executed
      break
    if side=='BUY':
      newRefPrice=kfGetBid(kf,symbol)
    else:
      newRefPrice=kfGetAsk(kf,symbol)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_MAX_WAIT_TIME):
      refPrice=newRefPrice
      nChases+=1
      orderStatus = kfGetOrderStatus(kf, orderId)
      if orderStatus is None:  # If order doesn't exist, it means all executed
        break
      if nChases>maxChases and float(orderStatus['filledSize'])==0:
        mult = .98 if side == 'BUY' else 1.02
        farPrice = roundPrice('kf', refPrice * mult, ccy)
        try:
          kf.query('editorder',{'orderId':orderId,'limitPrice':farPrice})
        except:
          break
        orderStatus = kfGetOrderStatus(kf, orderId)
        if orderStatus is None:  # If order doesn't exist, it means all executed
          break
        if float(orderStatus['filledSize']) == 0:
          kf.query('cancelorder',{'order_id':orderId})
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        refTime=time.time()
        newLimitPrice = getLimitPrice('kf', refPrice, ccy, side)
        if (side=='BUY' and newLimitPrice > limitPrice) or (side=='SELL' and newLimitPrice < limitPrice):
          limitPrice=newLimitPrice
          try:
            kf.query('editorder', {'orderId': orderId, 'limitPrice': limitPrice})
          except:
            break
    time.sleep(1)
  fill=kfGetFillPrice(kf, orderId)
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

####################
# Smart basis models
####################
def getFundingDict(ftx,bb,bn,db,kf,ccy):
  def getMarginal(ftxWallet,borrowS,lendingS,ccy):
    if ftxWallet.loc[ccy, 'total'] >= 0:
      return lendingS[ccy]
    else:
      return borrowS[ccy]
  #####
  # Common
  ftxWallet = ftxGetWallet(ftx)
  borrowS = ftxGetEstBorrow(ftx)
  lendingS = ftxGetEstLending(ftx)
  d=dict()  
  d['ftxEstBorrowUSD'] = borrowS['USD']
  d['ftxEstLendingUSD'] = lendingS['USD']
  d['ftxEstMarginalUSD'] = getMarginal(ftxWallet,borrowS,lendingS,'USD')
  d['ftxEstMarginalUSDT'] = getMarginal(ftxWallet, borrowS, lendingS, 'USDT')
  d['ftxEstLendingBTC']=  lendingS['BTC']
  d['ftxEstLendingETH']=  lendingS['ETH']
  d['ftxEstSpot']=d['ftxEstMarginalUSD']-(d['ftxEstLendingBTC']+d['ftxEstLendingETH'])/2
  #####
  # Ccy-specific
  d['Ccy'] = ccy
  d['ftxEstFunding'] = ftxGetEstFunding(ftx, ccy)  
  d['bbEstFunding1'] = bbGetEstFunding1(bb, ccy)  
  d['bbEstFunding2'] = bbGetEstFunding2(bb, ccy)  
  d['bbtEstFunding1'] = bbtGetEstFunding1(bb, ccy)  
  d['bbtEstFunding2'] = bbtGetEstFunding2(bb, ccy)  
  d['bnEstFunding'] = bnGetEstFunding(bn, ccy)  
  d['bntEstFunding'] = bntGetEstFunding(bn, ccy)  
  d['dbEstFunding'] = dbGetEstFunding(db, ccy)  
  kfTickers = kfGetTickers(kf)
  d['kfEstFunding1'] = kfGetEstFunding1(kf,ccy,kfTickers)  
  d['kfEstFunding2'] = kfGetEstFunding2(kf,ccy,kfTickers)  
  return d

#############################################################################################

def getOneDayShortSpotEdge(fundingDict):
  return getOneDayDecayedMean(fundingDict['ftxEstSpot'], SMB_BASE_RATE, SMB_HALF_LIFE_HOURS) / 365

def getOneDayUSDTCollateralBleed(fundingDict):
  return -getOneDayDecayedMean(fundingDict['ftxEstMarginalUSDT'], SMB_BASE_RATE, SMB_HALF_LIFE_HOURS) / 365 * SMB_USDT_COLLATERAL_COVERAGE

def getOneDayShortFutEdge(hoursInterval,basis,snapFundingRate,estFundingRate,pctElapsedPower=1,prevFundingRate=None,isKF=False):
  # gain on projected basis mtm after 1 day
  edge=basis-getOneDayDecayedValues(basis, SMB_BASE_BASIS, SMB_HALF_LIFE_HOURS)[-1]

  # gain on coupon from elapsed time
  if isKF: # Special mod for kf
    pctElapsed=1
  else:
    pctElapsed = getPctElapsed(hoursInterval) ** pctElapsedPower
  edge += estFundingRate / 365 / (24 / hoursInterval) * pctElapsed
  hoursAccountedFor=hoursInterval*pctElapsed

  # gain on coupon from previous reset
  if not prevFundingRate is None:
    if isKF: # Special mod for kf
      pctCaptured=1-getPctElapsed(hoursInterval)
    else:
      pctCaptured=1
    edge+=prevFundingRate/365/(24/hoursInterval)*pctCaptured
    hoursAccountedFor+=hoursInterval*pctCaptured

  # gain on projected funding pickup
  nMinutes = 1440 - round(hoursAccountedFor * 60)
  edge+= getOneDayDecayedMean(snapFundingRate, SMB_BASE_RATE, SMB_HALF_LIFE_HOURS, nMinutes=nMinutes) / 365 * (nMinutes / 1440)

  return edge

@retry(wait_fixed=1000)
def ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, basis):
  if fundingDict['Ccy']=='BTC' and not hasattr(ftxGetOneDayShortFutEdge,'emaSnapBTC'):
    ftxGetOneDayShortFutEdge.emaSnapBTC = fundingDict['ftxEstFunding']
  elif fundingDict['Ccy']=='ETH' and not hasattr(ftxGetOneDayShortFutEdge, 'emaSnapETH'):
    ftxGetOneDayShortFutEdge.emaSnapETH = fundingDict['ftxEstFunding']
  df=ftxFutures.loc[fundingDict['Ccy']+'-PERP']
  snapFundingRate=(float(df['mark']) / float(df['index']) - 1)*365
  if fundingDict['Ccy']=='BTC':
    smoothedSnapRate = ftxGetOneDayShortFutEdge.emaSnapBTC = getEMANow(snapFundingRate, ftxGetOneDayShortFutEdge.emaSnapBTC, CT_K)
  elif fundingDict['Ccy']=='ETH':
    smoothedSnapRate = ftxGetOneDayShortFutEdge.emaSnapETH = getEMANow(snapFundingRate, ftxGetOneDayShortFutEdge.emaSnapETH, CT_K)
  else:
    sys.exit(1)
  return getOneDayShortFutEdge(1,basis,smoothedSnapRate, fundingDict['ftxEstFunding'])

@retry(wait_fixed=1000)
def bbGetOneDayShortFutEdge(bb, fundingDict, basis):
  start_time = int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(minutes=15))))
  premIndex=np.mean([float(n) for n in pd.DataFrame(bb.v2_public_get_premium_index_kline({'symbol':fundingDict['Ccy']+'USD','interval':'1','from':start_time})['result'])['close']])
  premIndexClamped  = premIndex + np.clip(0.0001 - premIndex, -0.0005, 0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['bbEstFunding2'], prevFundingRate=fundingDict['bbEstFunding1'])

@retry(wait_fixed=1000)
def bbtGetOneDayShortFutEdge(bb, fundingDict, basis):
  start_time = int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(minutes=15))))
  premIndex=np.mean([float(n) for n in pd.DataFrame(bb.public_linear_get_premium_index_kline({'symbol':fundingDict['Ccy']+'USDT','interval':1,'from':start_time})['result'])['close']])
  premIndexClamped  = premIndex + np.clip(0.0001 - premIndex, -0.0005, 0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['bbtEstFunding2'], prevFundingRate=fundingDict['bbtEstFunding1']) - getOneDayUSDTCollateralBleed(fundingDict)

@retry(wait_fixed=1000)
def bnGetOneDayShortFutEdge(bn, fundingDict, basis):
  df=pd.DataFrame(bn.dapiData_get_basis({'pair': fundingDict['Ccy'] + 'USD', 'contractType': 'PERPETUAL', 'period': '1m'}))[-15:]
  dfSetFloat(df,['basis','indexPrice'])
  premIndex=(df['basis'] / df['indexPrice']).mean()
  premIndexClamped=premIndex+np.clip(0.0001-premIndex,-0.0005,0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis,snapFundingRate, fundingDict['bnEstFunding'], pctElapsedPower=2)

@retry(wait_fixed=1000)
def bntGetOneDayShortFutEdge(bn, fundingDict, basis):
  if fundingDict['Ccy']=='BTC' and not hasattr(bntGetOneDayShortFutEdge, 'emaPremIndexBTC'):
    bntGetOneDayShortFutEdge.emaPremIndexBTC = fundingDict['bntEstFunding'] / 365 / 3
  elif fundingDict['Ccy']=='ETH' and not hasattr(bntGetOneDayShortFutEdge, 'emaPremIndexETH'):
    bntGetOneDayShortFutEdge.emaPremIndexETH = fundingDict['bntEstFunding'] / 365 / 3
  d = bn.fapiPublic_get_premiumindex({'symbol': fundingDict['Ccy'] + 'USDT'})
  premIndex = float(d['markPrice']) / float(d['indexPrice']) - 1
  if fundingDict['Ccy'] == 'BTC':
    smoothedPremIndex = bntGetOneDayShortFutEdge.emaPremIndexBTC = getEMANow(premIndex, bntGetOneDayShortFutEdge.emaPremIndexBTC, CT_K)
  elif fundingDict['Ccy'] == 'ETH':
    smoothedPremIndex = bntGetOneDayShortFutEdge.emaPremIndexETH = getEMANow(premIndex, bntGetOneDayShortFutEdge.emaPremIndexETH, CT_K)
  else:
    sys.exit(1)
  smoothedSnapRate = (smoothedPremIndex + np.clip(0.0001 - smoothedPremIndex, -0.0005, 0.0005))*365*3
  return getOneDayShortFutEdge(8, basis,smoothedSnapRate, fundingDict['bntEstFunding'], pctElapsedPower=2) - getOneDayUSDTCollateralBleed(fundingDict)

@retry(wait_fixed=1000)
def dbGetOneDayShortFutEdge(fundingDict, basis):
  edge = basis - getOneDayDecayedValues(basis, SMB_BASE_BASIS, SMB_HALF_LIFE_HOURS)[-1] # basis
  edge += getOneDayDecayedMean(fundingDict['dbEstFunding'], SMB_BASE_RATE, SMB_HALF_LIFE_HOURS) / 365 # funding
  return edge

@retry(wait_fixed=1000)
def kfGetOneDayShortFutEdge(kfTickers, fundingDict, basis):
  if fundingDict['Ccy']=='BTC' and not hasattr(kfGetOneDayShortFutEdge, 'emaSnapBTC'):
    kfGetOneDayShortFutEdge.emaSnapBTC = fundingDict['kfEstFunding2']
    kfGetOneDayShortFutEdge.emaEst2BTC = fundingDict['kfEstFunding2']
  elif fundingDict['Ccy']=='ETH' and not hasattr(kfGetOneDayShortFutEdge, 'emaSnapETH'):
    kfGetOneDayShortFutEdge.emaSnapETH = fundingDict['kfEstFunding2']
    kfGetOneDayShortFutEdge.emaEst2ETH = fundingDict['kfEstFunding2']
  symbol = kfCcyToSymbol(fundingDict['Ccy'])
  indexSymbol = kfCcyToSymbol(fundingDict['Ccy'],isIndex=True)
  mid = (kfTickers.loc[symbol, 'bid'] + kfTickers.loc[symbol, 'ask']) / 2
  premIndexClipped = np.clip(mid / kfTickers.loc[indexSymbol, 'last'] - 1, -0.008, 0.008)
  snapFundingRate = premIndexClipped * 365 * 3
  if fundingDict['Ccy'] == 'BTC':
    smoothedSnapRate = kfGetOneDayShortFutEdge.emaSnapBTC = getEMANow(snapFundingRate, kfGetOneDayShortFutEdge.emaSnapBTC, CT_K)
    smoothedEst2Rate=kfGetOneDayShortFutEdge.emaEst2BTC=getEMANow(fundingDict['kfEstFunding2'], kfGetOneDayShortFutEdge.emaEst2BTC, CT_K)
  elif fundingDict['Ccy'] == 'ETH':
    smoothedSnapRate = kfGetOneDayShortFutEdge.emaSnapETH = getEMANow(snapFundingRate, kfGetOneDayShortFutEdge.emaSnapETH, CT_K)
    smoothedEst2Rate=kfGetOneDayShortFutEdge.emaEst2ETH=getEMANow(fundingDict['kfEstFunding2'], kfGetOneDayShortFutEdge.emaEst2ETH, CT_K)
  else:
    sys.exit(1)
  return getOneDayShortFutEdge(4, basis, smoothedSnapRate, smoothedEst2Rate, prevFundingRate=fundingDict['kfEstFunding1'], isKF=True)

#############################################################################################

def getSmartBasisDict(ftx, bb, bn, db, kf, ccy, fundingDict, isSkipAdj=False):
  @retry(wait_fixed=1000)
  def ftxGetFutures(ftx):
    return pd.DataFrame(ftx.public_get_futures()['result']).set_index('name')
  #####
  ftxPrices = getPrices('ftx', ftx, ccy)
  bbPrices = getPrices('bb', bb, ccy)
  bbtPrices = getPrices('bbt',bb, ccy)
  bnPrices = getPrices('bn', bn, ccy)
  bntPrices = getPrices('bnt', bn, ccy)
  kfPrices = getPrices('kf', kf, ccy)
  dbPrices = getPrices('db', db, ccy)
  #####
  objs = [ftxPrices, bbPrices, bbtPrices, bnPrices, bntPrices, kfPrices, dbPrices]
  Parallel(n_jobs=len(objs), backend='threading')(delayed(obj.run)() for obj in objs)
  #####
  oneDayShortSpotEdge = getOneDayShortSpotEdge(fundingDict)
  if isSkipAdj:
    ftxAdj=0    
    bbAdj = 0    
    bbtAdj = 0    
    bnAdj=0    
    bntAdj=0    
    dbAdj = 0        
    kfAdj=0    
  else:
    ftxAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['FTX_'+ccy+'_ADJ_BPS']) / 10000    
    bbAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['BB_'+ccy+'_ADJ_BPS']) / 10000    
    bbtAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['BBT_'+ccy+'_ADJ_BPS']) / 10000    
    bnAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['BN_'+ccy+'_ADJ_BPS']) / 10000    
    bntAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['BNT_'+ccy+'_ADJ_BPS']) / 10000    
    dbAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['DB_'+ccy+'_ADJ_BPS']) / 10000        
    kfAdj = (CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS'] - CT_CONFIGS_DICT['KF_'+ccy+'_ADJ_BPS']) / 10000                
  #####
  ftxFutures = ftxGetFutures(ftx)
  d = dict()
  d['ftxBasis'] = ftxPrices.fut / ftxPrices.spot - 1  
  d['ftxSmartBasis'] = ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, d['ftxBasis']) - oneDayShortSpotEdge + ftxAdj
  #####
  d['bbBasis'] = bbPrices.fut / ftxPrices.spot - 1  
  d['bbSmartBasis'] = bbGetOneDayShortFutEdge(bb,fundingDict, d['bbBasis']) - oneDayShortSpotEdge + bbAdj
  #####
  d['bbtBasis'] = bbtPrices.fut * ftxPrices.spotUSDT / ftxPrices.spot - 1  
  d['bbtSmartBasis'] = bbtGetOneDayShortFutEdge(bb, fundingDict, d['bbtBasis']) - oneDayShortSpotEdge + bbtAdj
  #####
  d['bnBasis'] = bnPrices.fut / ftxPrices.spot - 1  
  d['bnSmartBasis'] = bnGetOneDayShortFutEdge(bn, fundingDict, d['bnBasis']) - oneDayShortSpotEdge + bnAdj
  ###
  d['bntBasis'] = bntPrices.fut * ftxPrices.spotUSDT / ftxPrices.spot - 1  
  d['bntSmartBasis'] = bntGetOneDayShortFutEdge(bn, fundingDict, d['bntBasis']) - oneDayShortSpotEdge + bntAdj
  ###
  d['dbBasis'] = dbPrices.fut / ftxPrices.spot - 1  
  d['dbSmartBasis'] = dbGetOneDayShortFutEdge(fundingDict, d['dbBasis']) - oneDayShortSpotEdge + dbAdj
  ###
  d['kfBasis']= kfPrices.fut / ftxPrices.spot - 1  
  d['kfSmartBasis'] = kfGetOneDayShortFutEdge(kfPrices.kfTickers,fundingDict, d['kfBasis']) - oneDayShortSpotEdge + kfAdj
  return d

#############################################################################################

###############
# CryptoAlerter
###############
def caRun(ccy, color):
  def getCurrentTimeCondensed():
    return datetime.datetime.today().strftime('%H:%M:%S')
  def process(exch, smartBasisDict, color, funding, funding2=None):
    smartBasisBps = smartBasisDict[exch + 'SmartBasis'] * 10000
    basisBps = smartBasisDict[exch + 'Basis'] * 10000
    z = exch.upper() + ':' + str(round(smartBasisBps)) + '/' + str(round(basisBps)) + 'bps(' + str(round(funding * 100))
    if funding2 is None:
      n = 20
    else:
      z = z + '/' + str(round(funding2 * 100))
      n = 23
    z += ')'
    print(termcolor.colored(z.ljust(n), color), end='')
  #####
  printHeader(ccy+'Alerter')
  col1N = 23
  print('Column 1:'.ljust(col1N)+'USD marginal rate / USDT marginal rate / Average coin lending rates (BTC, ETH)')
  print('Body:'.ljust(col1N)+'Smart basis / raw basis (est. funding rate)')
  print()
  ftx=ftxCCXTInit()
  bb=bbCCXTInit()
  bn=bnCCXTInit()
  db=dbCCXTInit()
  kf=kfInit()
  while True:
    fundingDict = getFundingDict(ftx,bb,bn,db,kf,ccy)
    smartBasisDict = getSmartBasisDict(ftx,bb,bn,db,kf,ccy, fundingDict, isSkipAdj=True)
    print(getCurrentTimeCondensed().ljust(10),end='')
    avgCoinRate=(fundingDict['ftxEstLendingBTC']+fundingDict['ftxEstLendingETH'])/2
    print(termcolor.colored((str(round(fundingDict['ftxEstMarginalUSD'] * 100))+'/'+str(round(fundingDict['ftxEstMarginalUSDT'] * 100)) + '/'+ \
      str(round(avgCoinRate * 100))).ljust(col1N-10),'red'),end='')
    process('ftx', smartBasisDict, color, fundingDict['ftxEstFunding'])
    process('bb', smartBasisDict, color, fundingDict['bbEstFunding1'], fundingDict['bbEstFunding2'])
    process('bbt', smartBasisDict, color, fundingDict['bbtEstFunding1'], fundingDict['bbtEstFunding2'])
    process('bn', smartBasisDict, color, fundingDict['bnEstFunding'])
    process('bnt', smartBasisDict, color, fundingDict['bntEstFunding'])
    process('db', smartBasisDict, color, fundingDict['dbEstFunding'])
    process('kf', smartBasisDict, color, fundingDict['kfEstFunding1'], fundingDict['kfEstFunding2'])
    print()

#############################################################################################

##############
# CryptoTrader
##############
def ctInit():
  ftx = ftxCCXTInit()
  bb = bbCCXTInit()
  bn = bnCCXTInit()
  db = dbCCXTInit()
  kf = kfInit()
  ftxWallet=ftxGetWallet(ftx)
  spotBTC=ftxWallet.loc['BTC','spot']
  spotETH=ftxWallet.loc['ETH', 'spot']
  trade_btc = np.min([np.min([CT_TRADE_BTC_NOTIONAL, CT_MAX_NOTIONAL]) / spotBTC, CT_MAX_BTC])
  trade_eth = np.min([np.min([CT_TRADE_ETH_NOTIONAL, CT_MAX_NOTIONAL]) / spotETH, CT_MAX_ETH])
  trade_btc_notional = trade_btc * spotBTC
  trade_eth_notional = trade_eth * spotETH
  qty_dict = dict()
  qty_dict['BTC'] = trade_btc
  qty_dict['ETH'] = trade_eth
  notional_dict = dict()
  notional_dict['BTC'] = trade_btc_notional
  notional_dict['ETH'] = trade_eth_notional
  printHeader('CryptoTrader')
  print('Qtys:     ', qty_dict)
  print('Notionals:', notional_dict)
  print()
  return ftx,bb,bn,db,kf,qty_dict,notional_dict

def ctGetSuffix(tgtBps, realizedSlippageBps):
  z= termcolor.colored('Target: ' + str(round(tgtBps)) + 'bps', 'magenta')
  if len(realizedSlippageBps) > 0:
    z += ''.ljust(15) + termcolor.colored('Avg realized slippage:  ' + str(round(np.mean(realizedSlippageBps))) + 'bps', 'red')
  return z

def ctTooFewCandidates(i, tgtBps, realizedSlippageBps):
  print(('Program ' + str(i + 1) + ':').ljust(23) + termcolor.colored('************ Too few candidates ************'.ljust(65), 'blue') + ctGetSuffix(tgtBps, realizedSlippageBps))
  chosenLong = ''
  return chosenLong

def ctStreakEnded(i, tgtBps, realizedSlippageBps):
  print(('Program ' + str(i + 1) + ':').ljust(23) + termcolor.colored('*************** Streak ended ***************'.ljust(65), 'blue') + ctGetSuffix(tgtBps, realizedSlippageBps))
  prevSmartBasis = []
  chosenLong = ''
  chosenShort = ''
  return prevSmartBasis, chosenLong, chosenShort

def ctGetMaxChases(completedLegs):
  if completedLegs == 0:
    return 2
  else:
    return 888

def ctProcessFill(fill, completedLegs, isCancelled):
  if fill==0:
    if completedLegs==0:
      isCancelled=True
    else:
      print('Abnormal termination!')
      print('Leg '+str(completedLegs+1)+ ' cancelled when it should not have been')
      sys.exit(1)
  else:
    completedLegs+=1
  return completedLegs, isCancelled

def ctPrintTradeStats(longFill, shortFill, obsBasisBps, realizedSlippageBps):
  s= -((shortFill/longFill-1)*10000 - obsBasisBps)
  print(getCurrentTime() +   ': '+ termcolor.colored('Realized slippage:      '+str(round(s))+'bps','red'))
  realizedSlippageBps.append(s)
  return realizedSlippageBps

def ctRun(ccy,tgtBps):
  ftx, bb, bn, db, kf, qty_dict, notional_dict = ctInit()
  if not ccy in ['BTC', 'ETH']:
    print('Invalid ccy!')
    sys.exit(1)
  trade_qty = qty_dict[ccy]
  trade_notional = notional_dict[ccy]
  realizedSlippageBps = []
  for i in range(CT_NPROGRAMS):
    prevSmartBasis = []
    chosenLong = ''
    chosenShort = ''
    while True:
      fundingDict=getFundingDict(ftx, bb, bn, db, kf, ccy)
      smartBasisDict = getSmartBasisDict(ftx, bb, bn, db, kf, ccy, fundingDict)
      smartBasisDict['spotSmartBasis'] = 0
      smartBasisDict['spotBasis'] = 0

      # Remove disabled instruments
      for exch in ['spot','ftx','bb','bbt','bn','bnt','db','kf']:
        if CT_CONFIGS_DICT[exch.upper() + '_' + ccy + '_OK'] == 0:
          del smartBasisDict[exch + 'SmartBasis']
          del smartBasisDict[exch+'Basis']

      # Remove spots when high spot rate
      if CT_IS_HIGH_SPOT_RATE_PAUSE and fundingDict['ftxEstMarginalUSD'] >= 1:
        for key in filterDict(smartBasisDict, 'spot'):
          del smartBasisDict[key]

      # Filter dictionary
      d = filterDict(smartBasisDict, 'SmartBasis')

      # Check for too few candidates
      if len(d.keys())<2:
        chosenLong = ctTooFewCandidates(i, tgtBps, realizedSlippageBps)
        continue  # to next iteration in While True loop

      # If pair not lock-in yet
      if chosenLong=='':

        # Pick pair to trade
        while True:
          keyMax=max(d.items(), key=operator.itemgetter(1))[0]
          keyMin=min(d.items(), key=operator.itemgetter(1))[0]
          smartBasisBps=(d[keyMax]-d[keyMin])*10000
          chosenLong = keyMin[:len(keyMin) - 10]
          chosenShort = keyMax[:len(keyMax) - 10]
          if not CT_IS_NO_FUT_BUYS_WHEN_LONG:
            break
          if chosenLong=='ftx':
            pos=ftxGetFutPos(ftx,ccy)
          elif chosenLong=='bb':
            pos=bbGetFutPos(bb,ccy)
          elif chosenLong=='bbt':
            pos=bbGetFutPos(bb,ccy)
          elif chosenLong=='bn':
            pos=bnGetFutPos(bn,ccy)
          elif chosenLong=='bnt':
            pos=bntGetFutPos(bn, ccy)
          elif chosenLong=='db':
            pos=dbGetFutPos(db,ccy)
          elif chosenLong=='kf':
            pos=kfGetFutPos(kf,ccy)
          else:
            break
          if pos>=0:
            del d[chosenLong+'SmartBasis']
          else:
            break

        # Check for too few candidates again
        if len(d.keys()) < 2:
          chosenLong = ctTooFewCandidates(i, tgtBps, realizedSlippageBps)
          continue  # to next iteration in While True loop

        # If target not reached yet ....
        if smartBasisBps<tgtBps:
          z = ('Program ' + str(i + 1) + ':').ljust(23)
          z += termcolor.colored((ccy+' (buy ' + chosenLong + '/sell '+chosenShort+') smart basis: '+str(round(smartBasisBps))+'bps').ljust(65),'blue')
          z += ctGetSuffix(tgtBps, realizedSlippageBps)
          print(z)
          chosenLong = ''
          continue # to next iteration in While True loop
        else:
          status=0

      # Maintenance
      try:
        smartBasisBps = (smartBasisDict[chosenShort+'SmartBasis'] - smartBasisDict[chosenLong+'SmartBasis'])* 10000
      except:
        prevSmartBasis, chosenLong, chosenShort = ctStreakEnded(i, tgtBps, realizedSlippageBps)
        continue # to next iteration in While True Loop
      basisBps      = (smartBasisDict[chosenShort+'Basis']      - smartBasisDict[chosenLong+'Basis'])*10000
      prevSmartBasis.append(smartBasisBps)
      prevSmartBasis= prevSmartBasis[-CT_STREAK:]
      isStable= (np.max(prevSmartBasis)-np.min(prevSmartBasis)) <= CT_STREAK_BPS_RANGE

      # If target reached ....
      if smartBasisBps>=tgtBps:
        status+=1
      else:
        prevSmartBasis, chosenLong, chosenShort = ctStreakEnded(i, tgtBps, realizedSlippageBps)
        continue # to next iteration in While True Loop

      # Chosen long/short legs
      z = ('Program ' + str(i + 1) + ':').ljust(20) + termcolor.colored(str(status).rjust(2), 'red') + ' '
      z += termcolor.colored((ccy + ' (buy ' + chosenLong + '/sell '+chosenShort+') smart/raw basis: ' + str(round(smartBasisBps)) + '/' + str(round(basisBps)) + 'bps').ljust(65), 'blue')
      print(z + ctGetSuffix(tgtBps, realizedSlippageBps))

      if abs(status) >= CT_STREAK and isStable:
        print()
        speak('Go')
        completedLegs = 0
        isCancelled=False
        if 'bb' == chosenLong and not isCancelled:
          longFill = bbRelOrder('BUY', bb, ccy, trade_notional,maxChases=ctGetMaxChases(completedLegs))
          completedLegs,isCancelled=ctProcessFill(longFill,completedLegs,isCancelled)
        if 'bb' == chosenShort and not isCancelled:
          shortFill = bbRelOrder('SELL', bb, ccy, trade_notional,maxChases=ctGetMaxChases(completedLegs))
          completedLegs,isCancelled=ctProcessFill(shortFill,completedLegs,isCancelled)
        if 'bbt' == chosenLong and not isCancelled:
          longFill = bbtRelOrder('BUY', bb, ccy, trade_qty,maxChases=ctGetMaxChases(completedLegs)) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs,isCancelled=ctProcessFill(longFill,completedLegs,isCancelled)
        if 'bbt' == chosenShort and not isCancelled:
          shortFill = bbtRelOrder('SELL', bb, ccy, trade_qty,maxChases=ctGetMaxChases(completedLegs)) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs,isCancelled=ctProcessFill(shortFill,completedLegs,isCancelled)
        if 'kf' == chosenLong and not isCancelled:
          longFill = kfRelOrder('BUY', kf, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'kf' == chosenShort and not isCancelled:
          shortFill = kfRelOrder('SELL', kf, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'db' == chosenLong and not isCancelled:
          longFill = dbRelOrder('BUY', db, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'db' == chosenShort and not isCancelled:
          shortFill = dbRelOrder('SELL', db, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'spot' == chosenLong and not isCancelled:
          longFill = ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'spot' == chosenShort and not isCancelled:
          shortFill = ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'ftx' == chosenLong and not isCancelled:
          longFill = ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'ftx' == chosenShort and not isCancelled:
          shortFill = ftxRelOrder('SELL', ftx, ccy + '-PERP', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'bn' == chosenLong and not isCancelled:
          longFill = bnRelOrder('BUY', bn, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'bn' == chosenShort and not isCancelled:
          shortFill = bnRelOrder('SELL', bn, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'bnt' == chosenLong and not isCancelled:
          longFill = bntRelOrder('BUY', bn, ccy, trade_qty, maxChases=ctGetMaxChases(completedLegs)) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'bnt' == chosenShort and not isCancelled:
          shortFill = bntRelOrder('SELL', bn, ccy, trade_qty, maxChases=ctGetMaxChases(completedLegs)) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)

        if isCancelled:
          status=(min(abs(status),CT_STREAK)-1)*np.sign(status)
          print()
          speak('Cancelled')
          continue # to next iteration in While True loop
        else:
          realizedSlippageBps = ctPrintTradeStats(longFill, shortFill, basisBps, realizedSlippageBps)
          print(getCurrentTime() + ': Done')
          print()
          speak('Done')
          break # Go to next program
  speak('All done')

#############################################################################################

#####
# Etc
#####
# Cast column of dataframe to float
def dfSetFloat(df,colName):
  df[colName] = df[colName].astype(float)

# Get EMA now
def getEMANow(valueNow,emaPrev,k):
  return valueNow*k + emaPrev*(1-k)

# Filter dictionary by keyword
def filterDict(d, keyword):
  d2 = dict()
  for (key, value) in d.items():
    if keyword in key:
      d2[key] = value
  return d2

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
def speak(text):
  try:
    import win32com.client as wincl
    speaker = wincl.Dispatch("SAPI.SpVoice")
    speaker.Voice = speaker.getvoices()[1]
    speaker.Speak(text)
  except:
    print('[Speaking: "'+text+'"]')
    print()