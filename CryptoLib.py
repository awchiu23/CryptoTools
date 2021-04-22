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
import apophis
from retrying import retry

#########
# Classes
#########
class getPrices:
  def __init__(self, exch, api):
    self.exch = exch
    self.api = api

  def run(self):
    if self.exch == 'ftx':
      ftxMarkets=self.ftxGetMarkets(self.api)
      self.spotBTC=self.ftxGetMid(ftxMarkets, 'BTC/USD')
      self.spotETH=self.ftxGetMid(ftxMarkets, 'ETH/USD')
      self.futBTC=self.ftxGetMid(ftxMarkets, 'BTC-PERP')
      self.futETH=self.ftxGetMid(ftxMarkets, 'ETH-PERP')
      self.ftxFutures = self.ftxGetFutures(self.api)
    elif self.exch == 'bb':
      bbTickers=self.bbGetTickers(self.api)
      self.futBTC=self.bbGetMid(bbTickers,'BTC')
      self.futETH = self.bbGetMid(bbTickers,'ETH')
    elif self.exch == 'bn':
      bnBookTicker = self.bnGetBookTicker(self.api)
      self.futBTC = self.bnGetMid(bnBookTicker, 'BTC')
      self.futETH = self.bnGetMid(bnBookTicker, 'ETH')
    elif self.exch == 'db':
      self.futBTC =  self.dbGetMid(self.api, 'BTC')
      self.futETH =  self.dbGetMid(self.api, 'ETH')
    elif self.exch == 'kf':
      self.kfTickers = kfGetTickers(self.api)
      self.futBTC = self.kfGetMid(self.kfTickers, 'BTC')
      self.futETH = self.kfGetMid(self.kfTickers, 'ETH')

  @retry(wait_fixed=1000)
  def ftxGetMarkets(self, ftx):
    return pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')

  @retry(wait_fixed=1000)
  def ftxGetFutures(self, ftx):
    return pd.DataFrame(ftx.public_get_futures()['result']).set_index('name')

  @retry(wait_fixed=1000)
  def bbGetTickers(self, bb):
    return pd.DataFrame(bb.v2PublicGetTickers()['result']).set_index('symbol')

  @retry(wait_fixed=1000)
  def bnGetBookTicker(self, bn):
    return pd.DataFrame(bn.dapiPublicGetTickerBookTicker()).set_index('symbol')

  @retry(wait_fixed=1000)
  def dbGetMid(self, db,ccy):
    d=db.public_get_ticker({'instrument_name': ccy+'-PERPETUAL'})['result']
    return (float(d['best_bid_price'])+float(d['best_ask_price']))/2

  # Do not use @retry
  def ftxGetMid(self, ftxMarkets, name):
    return (float(ftxMarkets.loc[name, 'bid']) + float(ftxMarkets.loc[name, 'ask'])) / 2

  # Do not use @retry
  def bbGetMid(self, bbTickers, ccy):
    return (float(bbTickers.loc[ccy+'USD', 'bid_price']) + float(bbTickers.loc[ccy+'USD', 'ask_price'])) / 2

  # Do not use @retry
  def bnGetMid(self, bnBookTicker, ccy):
    return (float(bnBookTicker.loc[ccy + 'USD_PERP', 'bidPrice']) + float(bnBookTicker.loc[ccy + 'USD_PERP', 'askPrice'])) / 2

  # Do not use @retry
  def kfGetMid(self, kfTickers, ccy):
    if ccy == 'BTC':
      ticker = 'pi_xbtusd'
    elif ccy == 'ETH':
      ticker = 'pi_ethusd'
    else:
      sys.exit(1)
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
  return  ccxt.deribit({'apiKey': API_KEY_DB, 'secret': API_SECRET_DB, 'enableRateLimit': True})

def kfInit():
  return apophis.Apophis(API_KEY_KF,API_SECRET_KF,True)

def krCCXTInit(n=1):
  return ccxt.kraken({'apiKey': globals()['API_KEY_KR'+str(n)], 'secret': globals()['API_SECRET_KR'+str(n)], 'enableRateLimit': False})

def cbCCXTInit():
  return ccxt.coinbase({'apiKey': API_KEY_CB, 'secret': API_SECRET_CB, 'enableRateLimit': True})

#############################################################################################

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
  # Do not use @retry!
  def ftxGetLimitPrice(side, refPrice):
    if side == 'BUY':
      return round(refPrice * (1 - CT_FTX_DISTANCE_TO_BEST_BPS / 10000), 1)
    else:
      return round(refPrice * (1 + CT_FTX_DISTANCE_TO_BEST_BPS / 10000), 1)
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
  if ticker[:3] == 'BTC':
    qty = round(trade_qty, 3)
  elif ticker[:3] == 'ETH':
    qty = round(trade_qty, 2)
  else:
    sys.exit(1)
  print(getCurrentTime()+': Sending FTX '+side+' order of '+ticker+' (qty='+str(qty)+') ....')
  if side == 'BUY':
    refPrice = ftxGetBid(ftx, ticker)
  else:
    refPrice = ftxGetAsk(ftx, ticker)
  limitPrice = ftxGetLimitPrice(side, refPrice)
  orderId = ftx.private_post_orders({'market': ticker, 'side': side.lower(), 'price': limitPrice, 'type': 'limit', 'size': qty})['result']['id']
  refTime = time.time()
  nChases=0
  while True:
    if ftxGetRemainingSize(ftx,orderId) == 0:
      break
    if side=='BUY':
      newRefPrice=ftxGetBid(ftx,ticker)
    else:
      newRefPrice=ftxGetAsk(ftx,ticker)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_FTX_MAX_WAIT_TIME):
      refPrice=newRefPrice
      nChases+=1
      if nChases>maxChases and ftxGetRemainingSize(ftx,orderId)==qty:
        if side == 'BUY':
          farPrice = round(refPrice * .95,1)
        else:
          farPrice = round(refPrice * 1.05,1)
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
        newLimitPrice=ftxGetLimitPrice(side,refPrice)
        if newLimitPrice!=limitPrice:
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
  # Do not use @retry!
  def bbGetLimitPrice(side,refPrice):
    if side == 'BUY':
      return round(refPrice * (1 - CT_BB_DISTANCE_TO_BEST_BPS / 10000),2)
    else:
      return round(refPrice * (1 + CT_BB_DISTANCE_TO_BEST_BPS / 10000),2)
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
    limitPrice=bbGetLimitPrice(side, refPrice)
    orderId = bb.create_limit_buy_order(ticker1, trade_notional, limitPrice)['info']['order_id']
  else:
    refPrice = bbGetAsk(bb, ticker1)
    limitPrice = bbGetLimitPrice(side, refPrice)
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
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_BB_MAX_WAIT_TIME):
      refPrice = newRefPrice
      nChases+=1
      orderStatus = bbGetOrder(bb, ticker2, orderId)
      if orderStatus['order_status']=='Filled': break
      if nChases>maxChases and float(orderStatus['cum_exec_qty'])==0:
        if side == 'BUY':
          farPrice = round(refPrice * .95, 2)
        else:
          farPrice = round(refPrice * 1.05, 2)
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
        newLimitPrice=bbGetLimitPrice(side,refPrice)
        if newLimitPrice!=limitPrice:
          limitPrice=newLimitPrice
          try:
            bb.v2_private_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': limitPrice})
          except:
            break
    time.sleep(1)
  fill=bbGetFillPrice(bb, ticker2, orderId)
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

@retry(wait_fixed=1000)
def bnGetFutPos(bn,ccy):
  return float(pd.DataFrame(bn.dapiPrivate_get_positionrisk()).set_index('symbol').loc[ccy + 'USD_PERP']['positionAmt'])

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
  # Do not use @retry!
  def bnGetLimitPrice(side, refPrice,ccy):
    if side == 'BUY':
      px=refPrice * (1 - CT_BN_DISTANCE_TO_BEST_BPS / 10000)
    else:
      px=refPrice * (1 + CT_BN_DISTANCE_TO_BEST_BPS / 10000)
    if ccy=='BTC':
      return round(px,1)
    elif ccy=='ETH':
      return round(px,2)
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
  limitPrice = bnGetLimitPrice(side, refPrice,ccy)
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
    if (side == 'BUY' and newRefPrice > refPrice) or (side == 'SELL' and newRefPrice < refPrice) or ((time.time() - refTime) > CT_BN_MAX_WAIT_TIME):
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
        limitPrice = bnGetLimitPrice(side, refPrice,ccy)
        orderId=bnPlaceOrder(bn, ticker, side, leavesQty, limitPrice)
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
  # Do not use @retry!
  def dbRoundPrice(price,ccy):
    if ccy == 'BTC':
      return round(price * 2) / 2
    elif ccy == 'ETH':
      return round(price * 20) / 20
  # Do not use @retry!
  def dbGetLimitPrice(side, refPrice,ccy):
    if side == 'BUY':
      px=refPrice * (1 - CT_DB_DISTANCE_TO_BEST_BPS / 10000)
    else:
      px=refPrice * (1 + CT_DB_DISTANCE_TO_BEST_BPS / 10000)
    return dbRoundPrice(px,ccy)
  @retry(wait_fixed=1000)
  def dbGetOrder(db,orderId):
    return db.private_get_get_order_state({'order_id': orderId})['result']
  # Do not use @retry!
  def dbEditOrder(db, orderId, trade_notional, limitPrice):
    if dbGetOrder(db, orderId)['order_state']=='filled':
      return False
    for i in range(3):
      try:
        print(getCurrentTime() + ': [DEBUG INFO: private_get_edit order_id=' + str(orderId) + ' price=' + str(limitPrice) + ' try='+str(i+1)+']')
        db.private_get_edit({'order_id': orderId, 'amount': trade_notional, 'price': limitPrice})
        return True
      except:
        time.sleep(1)
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
    limitPrice = dbGetLimitPrice(side, refPrice,ccy)
    orderId=db.private_get_buy({'instrument_name':ticker,'amount':trade_notional,'type':'limit','price':limitPrice})['result']['order']['order_id']
  else:
    refPrice = dbGetAsk(db, ticker)
    limitPrice = dbGetLimitPrice(side, refPrice,ccy)
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
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_DB_MAX_WAIT_TIME):
      refPrice = newRefPrice
      nChases+=1
      orderStatus = dbGetOrder(db, orderId)
      if orderStatus['order_state'] == 'filled':
        break
      if nChases>maxChases and float(orderStatus['filled_amount'])==0:
        if side == 'BUY':
          farPrice = dbRoundPrice(refPrice * .95,ccy)
        else:
          farPrice = dbRoundPrice(refPrice * 1.05,ccy)
        if not dbEditOrder(db, orderId, trade_notional, farPrice):
          break
        if float(dbGetOrder(db, orderId)['filled_amount'])==0:
          db.private_get_cancel({'order_id': orderId})
          print(getCurrentTime() + ': Cancelled')
          return 0
      else:
        refTime = time.time()
        newLimitPrice=dbGetLimitPrice(side,refPrice,ccy)
        if newLimitPrice!=limitPrice:
          limitPrice=newLimitPrice
          if not dbEditOrder(db, orderId, trade_notional, limitPrice):
            break
    time.sleep(1)
  fill=float(dbGetOrder(db, orderId)['average_price'])
  print(getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

#############################################################################################

def kfCcyToSymbol(ccy):
  if ccy=='BTC':
    return 'pi_xbtusd'
  elif ccy=='ETH':
    return 'pi_ethusd'
  else:
    sys.exit(1)

@retry(wait_fixed=1000)
def kfGetFutPos(kf,ccy):
  piSymbol=kfCcyToSymbol(ccy)
  fiSymbol='f'+piSymbol[1:]
  return kf.query('accounts')['accounts'][fiSymbol]['balances'][piSymbol]

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
  # Do not use @retry!
  def kfRoundPrice(price, ccy):
    if ccy == 'BTC':
      return round(price * 2) / 2
    elif ccy == 'ETH':
      return round(price * 20) / 20
  # Do not use @retry!
  def kfGetLimitPrice(side, refPrice, ccy):
    if side == 'BUY':
      px = refPrice * (1 - CT_KF_DISTANCE_TO_BEST_BPS / 10000)
    else:
      px = refPrice * (1 + CT_KF_DISTANCE_TO_BEST_BPS / 10000)
    return kfRoundPrice(px,ccy)
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
  limitPrice=kfGetLimitPrice(side,refPrice,ccy)
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
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_KF_MAX_WAIT_TIME):
      refPrice=newRefPrice
      nChases+=1
      orderStatus = kfGetOrderStatus(kf, orderId)
      if orderStatus is None:  # If order doesn't exist, it means all executed
        break
      if nChases>maxChases and float(orderStatus['filledSize'])==0:
        if side == 'BUY':
          farPrice = kfRoundPrice(refPrice * .98,ccy)
        else:
          farPrice = kfRoundPrice(refPrice * 1.02,ccy)
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
        newLimitPrice=kfGetLimitPrice(side,refPrice,ccy)
        if newLimitPrice!=limitPrice:
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
def getFundingDict(ftx,bb,bn,db,kf):
  def getMarginal(ftxWallet,borrowS,lendingS,ccy):
    if ftxWallet.loc[ccy, 'total'] >= 0:
      return lendingS[ccy]
    else:
      return borrowS[ccy]
  #####
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
  d['ftxEstFundingBTC'] = ftxGetEstFunding(ftx, 'BTC')
  d['ftxEstFundingETH'] = ftxGetEstFunding(ftx, 'ETH')
  d['bbEstFunding1BTC'] = bbGetEstFunding1(bb, 'BTC')
  d['bbEstFunding1ETH'] = bbGetEstFunding1(bb, 'ETH')
  d['bbEstFunding2BTC'] = bbGetEstFunding2(bb, 'BTC')
  d['bbEstFunding2ETH'] = bbGetEstFunding2(bb, 'ETH')
  d['bnEstFundingBTC'] = bnGetEstFunding(bn, 'BTC')
  d['bnEstFundingETH'] = bnGetEstFunding(bn, 'ETH')  
  d['dbEstFundingBTC'] = dbGetEstFunding(db, 'BTC')
  d['dbEstFundingETH'] = dbGetEstFunding(db, 'ETH')
  kfTickers = kfGetTickers(kf)
  d['kfEstFunding1BTC'] = kfGetEstFunding1(kf, 'BTC',kfTickers)
  d['kfEstFunding1ETH'] = kfGetEstFunding1(kf, 'ETH',kfTickers)
  d['kfEstFunding2BTC'] = kfGetEstFunding2(kf, 'BTC',kfTickers)
  d['kfEstFunding2ETH'] = kfGetEstFunding2(kf, 'ETH',kfTickers)
  return d

#############################################################################################

def getOneDayShortSpotEdge(fundingDict):
  return getOneDayDecayedMean(fundingDict['ftxEstSpot'], BASE_SPOT_RATE, HALF_LIFE_HOURS_SPOT) / 365

def getOneDayShortFutEdge(hoursInterval,basis,snapFundingRate,estFundingRate,pctElapsedPower=1,prevFundingRate=None,isKF=False):
  # gain on projected basis mtm after 1 day
  edge=basis-getOneDayDecayedValues(basis, BASE_BASIS, HALF_LIFE_HOURS_BASIS)[-1]

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
  edge+= getOneDayDecayedMean(snapFundingRate, BASE_FUNDING_RATE, HALF_LIFE_HOURS_FUNDING, nMinutes=nMinutes) / 365 * (nMinutes/1440)

  return edge

@retry(wait_fixed=1000)
def ftxGetOneDayShortFutEdge(ftxFutures, fundingDict, ccy, basis):
  if not hasattr(ftxGetOneDayShortFutEdge,'emaSnapBTC'):
    ftxGetOneDayShortFutEdge.emaSnapBTC = fundingDict['ftxEstFundingBTC']
  if not hasattr(ftxGetOneDayShortFutEdge, 'emaSnapETH'):
    ftxGetOneDayShortFutEdge.emaSnapETH = fundingDict['ftxEstFundingETH']
  df=ftxFutures.loc[ccy+'-PERP']
  snapFundingRate=(float(df['mark']) / float(df['index']) - 1)*365
  k=2/(60 * 15 / CT_SLEEP + 1)
  if ccy=='BTC':
    smoothedSnapRate = ftxGetOneDayShortFutEdge.emaSnapBTC = getEMANow(snapFundingRate, ftxGetOneDayShortFutEdge.emaSnapBTC, k)
  elif ccy=='ETH':
    smoothedSnapRate = ftxGetOneDayShortFutEdge.emaSnapETH = getEMANow(snapFundingRate, ftxGetOneDayShortFutEdge.emaSnapETH, k)
  else:
    sys.exit(1)
  return getOneDayShortFutEdge(1,basis,smoothedSnapRate, fundingDict['ftxEstFunding' + ccy])

@retry(wait_fixed=1000)
def bbGetOneDayShortFutEdge(bb, fundingDict, ccy, basis):
  start_time = int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(minutes=15))))
  premIndex=np.mean([float(n) for n in pd.DataFrame(bb.v2_public_get_premium_index_kline({'symbol':ccy+'USD','interval':'1','from':start_time})['result'])['close']])
  premIndexClamped  = premIndex + np.clip(0.0001 - premIndex, -0.0005, 0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['bbEstFunding2' + ccy], prevFundingRate=fundingDict['bbEstFunding1'+ccy])

@retry(wait_fixed=1000)
def bnGetOneDayShortFutEdge(bn, fundingDict, ccy, basis):
  df=pd.DataFrame(bn.dapiData_get_basis({'pair': ccy + 'USD', 'contractType': 'PERPETUAL', 'period': '1m'}))[-15:]
  dfSetFloat(df,['basis','indexPrice'])
  premIndex=(df['basis'] / df['indexPrice']).mean()
  premIndexClamped=premIndex+np.clip(0.0001-premIndex,-0.0005,0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis,snapFundingRate, fundingDict['bnEstFunding' + ccy], pctElapsedPower=2)

@retry(wait_fixed=1000)
def dbGetOneDayShortFutEdge(fundingDict, ccy, basis):
  edge = basis - getOneDayDecayedValues(basis, BASE_BASIS, HALF_LIFE_HOURS_BASIS)[-1] # basis
  edge += getOneDayDecayedMean(fundingDict['dbEstFunding' + ccy], BASE_FUNDING_RATE, HALF_LIFE_HOURS_FUNDING) / 365 # funding
  return edge

@retry(wait_fixed=1000)
def kfGetOneDayShortFutEdge(kfTickers, fundingDict, ccy, basis):
  if not hasattr(kfGetOneDayShortFutEdge, 'emaSnapBTC'):
    kfGetOneDayShortFutEdge.emaSnapBTC = fundingDict['kfEstFunding2BTC']
  if not hasattr(kfGetOneDayShortFutEdge, 'emaEst2BTC'):
    kfGetOneDayShortFutEdge.emaEst2BTC = fundingDict['kfEstFunding2BTC']
  if not hasattr(kfGetOneDayShortFutEdge, 'emaSnapETH'):
    kfGetOneDayShortFutEdge.emaSnapETH = fundingDict['kfEstFunding2ETH']
  if not hasattr(kfGetOneDayShortFutEdge, 'emaEst2ETH'):
    kfGetOneDayShortFutEdge.emaEst2ETH = fundingDict['kfEstFunding2ETH']
  symbol = kfCcyToSymbol(ccy)
  if ccy == 'BTC':
    indexSymbol = 'in_xbtusd'
  elif ccy == 'ETH':
    indexSymbol = 'in_ethusd'
  else:
    sys.exit(1)
  mid = (kfTickers.loc[symbol, 'bid'] + kfTickers.loc[symbol, 'ask']) / 2
  premIndexClipped = np.clip(mid / kfTickers.loc[indexSymbol, 'last'] - 1, -0.008, 0.008)
  snapFundingRate = premIndexClipped * 365 * 3
  k = 2 / (60 * 15 / CT_SLEEP + 1)
  if ccy == 'BTC':
    smoothedSnapRate = kfGetOneDayShortFutEdge.emaSnapBTC = getEMANow(snapFundingRate, kfGetOneDayShortFutEdge.emaSnapBTC, k)
    smoothedEst2Rate=kfGetOneDayShortFutEdge.emaEst2BTC=getEMANow(fundingDict['kfEstFunding2BTC'], kfGetOneDayShortFutEdge.emaEst2BTC, k)
  elif ccy == 'ETH':
    smoothedSnapRate = kfGetOneDayShortFutEdge.emaSnapETH = getEMANow(snapFundingRate, kfGetOneDayShortFutEdge.emaSnapETH, k)
    smoothedEst2Rate=kfGetOneDayShortFutEdge.emaEst2ETH=getEMANow(fundingDict['kfEstFunding2ETH'], kfGetOneDayShortFutEdge.emaEst2ETH, k)
  else:
    sys.exit(1)
  ##################################################
  if False: # Turn to True for debugging
    if ccy=='BTC':
      z = 'Snap: ' + str(round(snapFundingRate * 100)) + ' / SmoothedSnap: ' + str(round(smoothedSnapRate * 100)) + ' / SmoothedEst2: ' + str(round(smoothedEst2Rate * 100))
      print()
      print(termcolor.colored(z, 'cyan').rjust(125), end='')
    else:
      z = 'Snap: ' + str(round(snapFundingRate * 100)) + ' / SmoothedSnap: ' + str(round(smoothedSnapRate * 100)) + ' / SmoothedEst2: ' + str(round(smoothedEst2Rate * 100))
      print(termcolor.colored(z, 'red').rjust(112))
  ##################################################
  return getOneDayShortFutEdge(4, basis, smoothedSnapRate, smoothedEst2Rate, prevFundingRate=fundingDict['kfEstFunding1' + ccy], isKF=True)

#############################################################################################

def getSmartBasisDict(ftx, bb, bn, db, kf, fundingDict, isSkipAdj=False):
  ftxPrices = getPrices('ftx', ftx)
  bbPrices = getPrices('bb', bb)
  bnPrices = getPrices('bn', bn)
  kfPrices = getPrices('kf', kf)
  dbPrices = getPrices('db', db)
  objs = [ftxPrices, bbPrices, bnPrices, kfPrices, dbPrices]
  Parallel(n_jobs=len(objs), backend='threading')(delayed(obj.run)() for obj in objs)
  #####
  oneDayShortSpotEdge = getOneDayShortSpotEdge(fundingDict)
  if isSkipAdj:
    ftxBTCAdj=0
    ftxETHAdj=0
    bbBTCAdj = 0
    bbETHAdj = 0
    bnBTCAdj=0
    bnETHAdj=0    
    dbBTCAdj = 0
    dbETHAdj = 0    
    kfBTCAdj=0
    kfETHAdj=0
  else:
    ftxBTCAdj = (CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS'] - CT_CONFIGS_DICT['FTX_BTC_ADJ_BPS']) / 10000
    ftxETHAdj = (CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS'] - CT_CONFIGS_DICT['FTX_ETH_ADJ_BPS']) / 10000
    bbBTCAdj = (CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS'] - CT_CONFIGS_DICT['BB_BTC_ADJ_BPS']) / 10000
    bbETHAdj = (CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS'] - CT_CONFIGS_DICT['BB_ETH_ADJ_BPS']) / 10000
    bnBTCAdj = (CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS'] - CT_CONFIGS_DICT['BN_BTC_ADJ_BPS']) / 10000
    bnETHAdj = (CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS'] - CT_CONFIGS_DICT['BN_ETH_ADJ_BPS']) / 10000
    dbBTCAdj = (CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS'] - CT_CONFIGS_DICT['DB_BTC_ADJ_BPS']) / 10000
    dbETHAdj = (CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS'] - CT_CONFIGS_DICT['DB_ETH_ADJ_BPS']) / 10000    
    kfBTCAdj = (CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS'] - CT_CONFIGS_DICT['KF_BTC_ADJ_BPS']) / 10000
    kfETHAdj = (CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS'] - CT_CONFIGS_DICT['KF_ETH_ADJ_BPS']) / 10000            
  #####
  d = dict()
  d['ftxBTCBasis'] = ftxPrices.futBTC / ftxPrices.spotBTC - 1
  d['ftxETHBasis'] = ftxPrices.futETH / ftxPrices.spotETH - 1
  d['ftxBTCSmartBasis'] = ftxGetOneDayShortFutEdge(ftxPrices.ftxFutures, fundingDict, 'BTC', d['ftxBTCBasis']) - oneDayShortSpotEdge + ftxBTCAdj
  d['ftxETHSmartBasis'] = ftxGetOneDayShortFutEdge(ftxPrices.ftxFutures, fundingDict, 'ETH', d['ftxETHBasis']) - oneDayShortSpotEdge + ftxETHAdj
  #####
  d['bbBTCBasis'] = bbPrices.futBTC / ftxPrices.spotBTC - 1
  d['bbETHBasis'] = bbPrices.futETH / ftxPrices.spotETH - 1
  d['bbBTCSmartBasis'] = bbGetOneDayShortFutEdge(bb,fundingDict, 'BTC',d['bbBTCBasis']) - oneDayShortSpotEdge + bbBTCAdj
  d['bbETHSmartBasis'] = bbGetOneDayShortFutEdge(bb,fundingDict, 'ETH',d['bbETHBasis']) - oneDayShortSpotEdge + bbETHAdj
  #####
  d['bnBTCBasis'] = bnPrices.futBTC / ftxPrices.spotBTC - 1
  d['bnETHBasis'] = bnPrices.futETH / ftxPrices.spotETH - 1
  d['bnBTCSmartBasis'] = bnGetOneDayShortFutEdge(bn, fundingDict, 'BTC', d['bnBTCBasis']) - oneDayShortSpotEdge + bnBTCAdj
  d['bnETHSmartBasis'] = bnGetOneDayShortFutEdge(bn, fundingDict, 'ETH', d['bnETHBasis']) - oneDayShortSpotEdge + bnETHAdj
  ###
  d['dbBTCBasis'] = dbPrices.futBTC / ftxPrices.spotBTC - 1
  d['dbETHBasis'] = dbPrices.futETH / ftxPrices.spotETH - 1
  d['dbBTCSmartBasis'] = dbGetOneDayShortFutEdge(fundingDict, 'BTC', d['dbBTCBasis']) - oneDayShortSpotEdge + dbBTCAdj
  d['dbETHSmartBasis'] = dbGetOneDayShortFutEdge(fundingDict, 'ETH', d['dbETHBasis']) - oneDayShortSpotEdge + dbETHAdj
  ###
  d['kfBTCBasis']= kfPrices.futBTC / ftxPrices.spotBTC - 1
  d['kfETHBasis'] = kfPrices.futETH / ftxPrices.spotETH - 1
  d['kfBTCSmartBasis'] = kfGetOneDayShortFutEdge(kfPrices.kfTickers,fundingDict, 'BTC', d['kfBTCBasis']) - oneDayShortSpotEdge + kfBTCAdj
  d['kfETHSmartBasis'] = kfGetOneDayShortFutEdge(kfPrices.kfTickers,fundingDict, 'ETH', d['kfETHBasis']) - oneDayShortSpotEdge + kfETHAdj
  return d

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

def ctRemoveDisabledInstrument(smartBasisDict, exch, ccy):
  if CT_CONFIGS_DICT[exch + '_' + ccy + '_OK'] == 0:
    d = filterDict(smartBasisDict, 'Basis')
    d = filterDict(d, exch.lower())
    d = filterDict(d, ccy)
    for key in d:
      del smartBasisDict[key]
  return smartBasisDict

def ctGetTargetString(tgtBps):
  return termcolor.colored('Target: ' + str(round(tgtBps)) + 'bps', 'magenta')

def ctTooFewCandidates(i, tgtBps):
  print(('Program ' + str(i + 1) + ':').ljust(23) + termcolor.colored('************ Too few candidates ************'.ljust(65), 'blue') + ctGetTargetString(tgtBps))
  chosenLong = ''
  time.sleep(CT_SLEEP)
  return chosenLong

def ctStreakEnded(i, tgtBps):
  print(('Program ' + str(i + 1) + ':').ljust(23) + termcolor.colored('*************** Streak ended ***************'.ljust(65), 'blue') + ctGetTargetString(tgtBps))
  prevSmartBasis = []
  chosenLong = ''
  chosenShort = ''
  return prevSmartBasis, chosenLong, chosenShort

def ctGetMaxChases(completedLegs):
  if completedLegs == 0:
    return 0
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
  if len(realizedSlippageBps) > 1:
    print(getCurrentTime() + ': '+ termcolor.colored('Avg realized slippage:  '+str(round(np.mean(realizedSlippageBps))) + 'bps','red'))
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
      fundingDict=getFundingDict(ftx, bb, bn, db, kf)
      smartBasisDict = getSmartBasisDict(ftx, bb, bn, db, kf, fundingDict)
      smartBasisDict['spot' + ccy + 'SmartBasis'] = 0
      smartBasisDict['spot' + ccy + 'Basis'] = 0

      # Remove disabled instruments
      for exch in ['SPOT','FTX','BB','BN','DB','KF']:
        smartBasisDict = ctRemoveDisabledInstrument(smartBasisDict,exch,ccy)

      # Remove spots when high spot rate
      if CT_IS_HIGH_SPOT_RATE_PAUSE and fundingDict['ftxEstMarginalUSD'] >= 1:
        for key in filterDict(smartBasisDict, 'spot'):
          del smartBasisDict[key]

      # Filter dictionary
      d = filterDict(smartBasisDict, 'SmartBasis')
      d = filterDict(d, ccy)

      # Check for too few candidates
      if len(d.keys())<2:
        chosenLong = ctTooFewCandidates(i, tgtBps)
        continue  # to next iteration in While True loop

      # If pair not lock-in yet
      if chosenLong=='':

        # Pick pair to trade
        while True:
          keyMax=max(d.items(), key=operator.itemgetter(1))[0]
          keyMin=min(d.items(), key=operator.itemgetter(1))[0]
          smartBasisBps=(d[keyMax]-d[keyMin])*10000
          chosenLong = keyMin[:len(keyMin) - 13]
          chosenShort = keyMax[:len(keyMax) - 13]
          if not CT_IS_NO_FUT_BUYS_WHEN_LONG:
            break
          if chosenLong=='ftx':
            pos=ftxGetFutPos(ftx,ccy)
          elif chosenLong=='bb':
            pos=bbGetFutPos(bb,ccy)
          elif chosenLong=='bn':
            pos=bnGetFutPos(bn,ccy)
          elif chosenLong=='db':
            pos=dbGetFutPos(db,ccy)
          elif chosenLong=='kf':
            pos=kfGetFutPos(kf,ccy)
          else:
            break
          if pos>=0:
            del d[chosenLong+ccy+'SmartBasis']
          else:
            break

        # Check for too few candidates again
        if len(d.keys()) < 2:
          chosenLong = ctTooFewCandidates(i, tgtBps)
          continue  # to next iteration in While True loop

        # If target not reached yet ....
        if smartBasisBps<tgtBps:
          z = ('Program ' + str(i + 1) + ':').ljust(23)
          z += termcolor.colored((ccy+' (buy ' + chosenLong + '/sell '+chosenShort+') smart basis: '+str(round(smartBasisBps))+'bps').ljust(65),'blue')
          print(z + ctGetTargetString(tgtBps))
          chosenLong = ''
          time.sleep(CT_SLEEP)
          continue # to next iteration in While True loop
        else:
          status=0

      # Maintenance
      try:
        smartBasisBps = (smartBasisDict[chosenShort+ccy+'SmartBasis'] - smartBasisDict[chosenLong+ccy+'SmartBasis'])* 10000
      except:
        prevSmartBasis, chosenLong, chosenShort = ctStreakEnded(i, tgtBps)
        continue # to next iteration in While True Loop
      basisBps      = (smartBasisDict[chosenShort+ccy+'Basis']      - smartBasisDict[chosenLong+ccy+'Basis'])*10000
      prevSmartBasis.append(smartBasisBps)
      prevSmartBasis= prevSmartBasis[-CT_STREAK:]
      isStable= (np.max(prevSmartBasis)-np.min(prevSmartBasis)) <= CT_STREAK_BPS_RANGE

      # If target reached ....
      if smartBasisBps>=tgtBps:
        status+=1
      else:
        prevSmartBasis, chosenLong, chosenShort = ctStreakEnded(i, tgtBps)
        continue # to next iteration in While True Loop

      # Chosen long/short legs
      z = ('Program ' + str(i + 1) + ':').ljust(20) + termcolor.colored(str(status).rjust(2), 'red') + ' '
      z += termcolor.colored((ccy + ' (buy ' + chosenLong + '/sell '+chosenShort+') smart/raw basis: ' + str(round(smartBasisBps)) + '/' + str(round(basisBps)) + 'bps').ljust(65), 'blue')
      print(z + ctGetTargetString(tgtBps))

      if abs(status) >= CT_STREAK and isStable:
        print()
        speak('Go')
        completedLegs = 0
        isCancelled=False
        if 'bb' in chosenLong and not isCancelled:
          longFill = bbRelOrder('BUY', bb, ccy, trade_notional,maxChases=ctGetMaxChases(completedLegs))
          completedLegs,isCancelled=ctProcessFill(longFill,completedLegs,isCancelled)
        if 'bb' in chosenShort and not isCancelled:
          shortFill = bbRelOrder('SELL', bb, ccy, trade_notional,maxChases=ctGetMaxChases(completedLegs))
          completedLegs,isCancelled=ctProcessFill(shortFill,completedLegs,isCancelled)
        if 'kf' in chosenLong and not isCancelled:
          longFill = kfRelOrder('BUY', kf, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'kf' in chosenShort and not isCancelled:
          shortFill = kfRelOrder('SELL', kf, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'db' in chosenLong and not isCancelled:
          longFill = dbRelOrder('BUY', db, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'db' in chosenShort and not isCancelled:
          shortFill = dbRelOrder('SELL', db, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'spot' in chosenLong and not isCancelled:
          longFill = ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'spot' in chosenShort and not isCancelled:
          shortFill = ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'ftx' in chosenLong and not isCancelled:
          longFill = ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'ftx' in chosenShort and not isCancelled:
          shortFill = ftxRelOrder('SELL', ftx, ccy + '-PERP', trade_qty, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'bn' in chosenLong and not isCancelled:
          longFill = bnRelOrder('BUY', bn, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'bn' in chosenShort and not isCancelled:
          shortFill = bnRelOrder('SELL', bn, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs))
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
      time.sleep(CT_SLEEP)
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