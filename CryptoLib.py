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
import traceback
import uuid
import ccxt
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
      self.fut=bbGetMid(self.api,self.ccy)
    elif self.exch == 'bbt':
      self.fut=bbtGetMid(self.api,self.ccy)
    elif self.exch == 'db':
      self.fut = dbGetMid(self.api,self.ccy)
    elif self.exch == 'kf':
      self.kfTickers = kfGetTickers(self.api)
      self.fut = kfGetMid(self.api,self.ccy,kfTickers=self.kfTickers)
    elif self.exch == 'kut':
      self.fut = kutGetMid(self.api,self.ccy)

class kutGetRiskDfs:
  def __init__(self, n):
    self.n = n

  def run(self):
    self.api = kutCCXTInit(self.n)
    self.availableBalance = float(kutGetUSDTDict(self.api)['availableBalance'])
    self.riskDf = kutGetRiskDf(self.api,availableBalance=self.availableBalance)

class kutGetCcyData:
  def __init__(self, ccy, apiDict, riskDfs):
    self.ccy = ccy
    self.apiDict = apiDict
    self.riskDfs = riskDfs

  def run(self):
    ccy2 = kutGetCcy(self.ccy)
    self.df = pd.DataFrame()
    for i in range(SHARED_EXCH_DICT['kut']):
      if ccy2 + 'USDTM' in self.riskDfs[i].riskDf.index:
        s = self.riskDfs[i].riskDf.loc[ccy2 + 'USDTM']
        self.df = self.df.append({'account': 'KUT' + str(i + 1),
                                  'liq': s['liq'],
                                  'markValue': s['markValue'],
                                  'maintMargin': s['maintMargin'],
                                  'ratio': s['ratio']}, ignore_index=True)
    if len(self.df) > 0:
      self.df = self.df.set_index('account')
      self.liq = self.df['liq'].min()
      self.ratio = self.df['ratio'].min()
      self.futDeltaUSD = self.df['markValue'].sum()
    #####
    SHARED_CCY_DICT[self.ccy] = {'futExch': ['ftx', 'kut']}
    self.fDict = getFundingDict(self.apiDict, self.ccy)
    self.sbDict = getSmartBasisDict(self.apiDict, self.ccy, self.fDict, isSkipAdj=True)
    self.yld = (self.fDict['kutEstFunding1'] + self.fDict['kutEstFunding2']) / 2
    self.sb = self.sbDict['kutSmartBasis']
    if self.ccy in SHARED_ETC_DICT['FTX_SPOT_USED']:
      self.yld -= self.fDict['ftxEstBorrowUSD']
    else:
      self.yld -= self.fDict['ftxEstFunding']
      self.sb -= self.sbDict['ftxSmartBasis']

#####################################################################################################################################

###########
# Functions
###########
###########
# API Inits
###########
def getApiDict():
  apiDict = dict()
  apiDict['ftx'] = ftxCCXTInit()
  apiDict['bb'] = bbCCXTInit()
  apiDict['bbtCurrent'] = bbCCXTInit(CT_CONFIGS_DICT['CURRENT_BBT']) if SHARED_EXCH_DICT['bbt'] > 0 else None
  apiDict['db'] = dbCCXTInit()
  apiDict['kf'] = kfApophisInit()
  apiDict['kut'] = kutCCXTInit()
  apiDict['kutCurrent'] = kutCCXTInit(CT_CONFIGS_DICT['CURRENT_KUT']) if SHARED_EXCH_DICT['kut'] > 0 else None
  return apiDict

def ftxCCXTInit():
  return ccxt.ftx({'apiKey': API_KEY_FTX, 'secret': API_SECRET_FTX, 'enableRateLimit': True, 'nonce': lambda: ccxt.Exchange.milliseconds()})

def bbCCXTInit(n=1):
  apiKey=API_KEYS_BB[n-1]
  apiSecret=API_SECRETS_BB[n-1]
  api = ccxt.bybit({'apiKey': apiKey, 'secret': apiSecret, 'enableRateLimit': True, 'nonce': lambda: ccxt.Exchange.milliseconds()})
  api.options['recvWindow']=50000
  return api

def dbCCXTInit():
  return ccxt.deribit({'apiKey': API_KEY_DB, 'secret': API_SECRET_DB, 'enableRateLimit': True, 'nonce': lambda: ccxt.Exchange.milliseconds()})

def kfApophisInit():
  return apophis.Apophis(API_KEY_KF,API_SECRET_KF,True)

def kutCCXTInit(n=1):
  apiKey = API_KEYS_KUT[n - 1]
  apiSecret = API_SECRETS_KUT[n - 1]
  apiPassword = API_PASSWORDS_KUT[n - 1]
  return ccxt.kucoin({'apiKey': apiKey, 'secret': apiSecret, 'password': apiPassword, 'enableRateLimit': True, 'nonce': lambda: ccxt.Exchange.milliseconds()})

#########
# Helpers
#########
@retry(wait_fixed=1000)
def ftxGetMid(ftx, name):
  if name not in ftxGetNames(ftx):
    if name.endswith('/USD'):
      return float(ftx.public_get_futures_future_name({'future_name': name[:(len(name) - 4)] + '-PERP'})['result']['index'])
    else:
      print('Invalid FTX name: '+name+'!')
      sys.exit(1)
  else:
    d=ftx.publicGetMarketsMarketNameOrderbook({'market_name': name, 'depth': 1})['result']
    if name=='SHIB-PERP': # Special fix for SHIB
      return float(d['bids'][0][0])+1e-8
    else:
      return (float(d['bids'][0][0])+float(d['asks'][0][0]))/2

@retry(wait_fixed=1000)
def ftxGetBid(ftx,ticker):
  return float(ftx.publicGetMarketsMarketNameOrderbook({'market_name': ticker,'depth': 1})['result']['bids'][0][0])

@retry(wait_fixed=1000)
def ftxGetAsk(ftx,ticker):
  if ticker == 'SHIB-PERP':  # Special fix for SHIB
    return ftxGetBid(ftx, ticker) + 2e-8
  else:
    return float(ftx.publicGetMarketsMarketNameOrderbook({'market_name': ticker,'depth': 1})['result']['asks'][0][0])

@retry(wait_fixed=1000)
def ftxGetFuture(ftx,ccy):
  return ftx.public_get_futures_future_name({'future_name':ccy+'-PERP'})['result']

@retry(wait_fixed=1000)
def bbGetMid(bb, ccy):
  d = bb.v2PublicGetTickers({'symbol': ccy + 'USD'})['result'][0]
  return (float(d['bid_price']) + float(d['ask_price'])) / 2

@retry(wait_fixed=1000)
def bbGetBid(bb,ccy):
  return float(bb.v2PublicGetTickers({'symbol': ccy + 'USD'})['result'][0]['bid_price'])

@retry(wait_fixed=1000)
def bbGetAsk(bb,ccy):
  return float(bb.v2PublicGetTickers({'symbol': ccy + 'USD'})['result'][0]['ask_price'])

@retry(wait_fixed=1000)
def bbtGetMid(bb, ccy):
  if ccy == 'SHIB':  # Special fix for SHIB
    return bbtGetMid(bb, 'SHIB1000')/1000
  else:
    d = bb.v2PublicGetTickers({'symbol': ccy + 'USDT'})['result'][0]
    return (float(d['bid_price']) + float(d['ask_price'])) / 2

@retry(wait_fixed=1000)
def bbtGetBid(bb,ccy):
  if ccy == 'SHIB': # Special fix for SHIB
    return bbtGetBid(bb, 'SHIB1000')/1000
  else:
    return float(bb.v2PublicGetTickers({'symbol': ccy + 'USDT'})['result'][0]['bid_price'])

@retry(wait_fixed=1000)
def bbtGetAsk(bb,ccy):
  if ccy == 'SHIB': # Special fix for SHIB
    return bbtGetAsk(bb, 'SHIB1000')/1000
  else:
    return float(bb.v2PublicGetTickers({'symbol': ccy + 'USDT'})['result'][0]['ask_price'])

@retry(wait_fixed=1000)
def dbGetMid(db,ccy):
  d=db.public_get_ticker({'instrument_name': ccy+'-PERPETUAL'})['result']
  return (float(d['best_bid_price'])+float(d['best_ask_price']))/2

@retry(wait_fixed=1000)
def dbGetBid(db,ccy):
  return float(db.public_get_ticker({'instrument_name': ccy+'-PERPETUAL'})['result']['best_bid_price'])

@retry(wait_fixed=1000)
def dbGetAsk(db,ccy):
  return float(db.public_get_ticker({'instrument_name': ccy+'-PERPETUAL'})['result']['best_ask_price'])

# Do not use @retry
def kfGetMid(kf, ccy, kfTickers=None):
  if kfTickers is None: kfTickers = kfGetTickers(kf)
  ticker=kfCcyToSymbol(ccy)
  return (kfTickers.loc[ticker, 'bid'] + kfTickers.loc[ticker, 'ask']) / 2

# Do not use @retry
def kfGetBid(kf, ccy, kfTickers=None):
  if kfTickers is None: kfTickers = kfGetTickers(kf)
  return kfTickers.loc[kfCcyToSymbol(ccy), 'bid']

# Do not use @retry
def kfGetAsk(kf, ccy, kfTickers=None):
  if kfTickers is None: kfTickers = kfGetTickers(kf)
  return kfTickers.loc[kfCcyToSymbol(ccy), 'ask']

@retry(wait_fixed=1000)
def kutGetMid(kut, ccy):
  d=kut.futuresPublic_get_ticker({'symbol': kutGetCcy(ccy) + 'USDTM'})['data']
  return (float(d['bestBidPrice'])+float(d['bestAskPrice']))/2

@retry(wait_fixed=1000)
def kutGetBid(kut, ccy):
  return float(kut.futuresPublic_get_ticker({'symbol': kutGetCcy(ccy) + 'USDTM'})['data']['bestBidPrice'])

@retry(wait_fixed=1000)
def kutGetAsk(kut, ccy):
  return float(kut.futuresPublic_get_ticker({'symbol': kutGetCcy(ccy) + 'USDTM'})['data']['bestAskPrice'])

#####

def roundPrice(api, exch, ccyOrTicker, price, side=None, distance=None):
  if exch in ['db','kf']:
    tickSize = dict({'BTC': 0.5, 'ETH': 0.05, 'XRP': 0.0001, 'BCH': 0.1, 'LTC': 0.01}).get(ccyOrTicker)
  elif exch=='ftx':
    tickSize = ftxGetTickSize(api, ccyOrTicker)
  elif exch in ['bb','bbt']:
    tickSize=bbGetTickSize(api, ccyOrTicker, isBBT=(exch == 'bbt'))
  elif exch=='kut':
    tickSize=kutGetTickSize(api, ccyOrTicker)

  #####
  adjPrice = round(price / tickSize) * tickSize
  if not side is None:
    if side == 'BUY':
      adjPrice += tickSize * distance
    elif side == 'SELL':
      adjPrice -= tickSize * distance
    else:
      sys.exit(1)
  nDigits=8 if ccyOrTicker[:4] == 'SHIB' else 6   # Special fix for SHIB
  return round(adjPrice,nDigits)

def roundQty(api, ccyOrTicker, qty):
  if api.name=='FTX':
    lotSize = ftxGetLotSize(api, ccyOrTicker)
  else:
    sys.exit(1)
  return round(round(qty / lotSize) * lotSize, 6)

#############################################################################################

#####
# FTX
#####
@retry(wait_fixed=1000)
def ftxGetNames(ftx):
  key='ftxNames'
  myList=cache('r',key)
  if myList is None:
    myList=pd.DataFrame(ftx.public_get_markets()['result'])['name'].to_list()
    cache('w',key,myList)
  return myList

@retry(wait_fixed=1000)
def ftxGetWallet(ftx,validCcys=None):
  wallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main']).set_index('coin')
  if validCcys is not None:
    for ccy in validCcys:
      if ccy not in wallet.index:
        s = wallet.iloc[-1].copy()
        s[:] = 0
        s.name = ccy
        wallet = wallet.append(s)
  dfSetFloat(wallet,wallet.columns)
  return wallet

@retry(wait_fixed=1000)
def ftxGetFutPos(ftx,ccy):
  df = pd.DataFrame(ftx.private_get_account()['result']['positions']).set_index('future')
  ccy2=ccy+'-PERP'
  if ccy2 in df.index:
    s=df.loc[ccy2]
    pos=float(s['size'])
    if s['side']=='sell':
      pos*=-1
    return pos
  else:
    return 0

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

@retry(wait_fixed=1000)
def ftxGetTickSize(ftx,ticker):
  key='ftxTickSize'
  df=cache('r',key)
  if df is None:
    df=pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')
    cache('w',key,df)
  return float(df.loc[ticker, 'priceIncrement'])

@retry(wait_fixed=1000)
def ftxGetLotSize(ftx,ticker):
  key='ftxLotSize'
  df=cache('r',key)
  if df is None:
    df=pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')
    cache('w',key,df)
  return float(df.loc[ticker, 'sizeIncrement'])

def ftxRelOrder(side,ftx,ticker,trade_qty,maxChases=0,distance=0):
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
  assertSide(side)
  qty=roundQty(ftx,ticker,trade_qty)
  maxWaitTime = CT_CONFIGS_DICT['FTX_MAX_WAIT_TIME'] if 'PERP' in ticker else CT_CONFIGS_DICT['SPOT_MAX_WAIT_TIME']
  print(timeTag('Sending FTX '+side+' order of '+ticker+' (qty='+str(qty)+') ....'))
  if side == 'BUY':
    refPrice = ftxGetBid(ftx, ticker)
  else:
    refPrice = ftxGetAsk(ftx, ticker)
  limitPrice = roundPrice(ftx,'ftx',ticker,refPrice,side=side,distance=distance)
  #####
  isOk=False
  for i in range(3):
    try:
      orderId = ftx.private_post_orders({'market': ticker, 'side': side.lower(), 'price': limitPrice, 'type': 'limit', 'size': qty})['result']['id']
      isOk=True
      break
    except ccxt.RateLimitExceeded:
      print(timeTag('FTX rate limit exceeded; trying to recover ....'))
      time.sleep(3)
    except ccxt.RequestTimeout:
      print(timeTag('FTX request timed out; trying to recover ....'))
      time.sleep(3)
    except:
      print(traceback.print_exc())
      sys.exit(1)
  if not isOk:
    sys.exit(1)
  #####
  print(timeTag('[DEBUG: orderId=' + orderId + '; price=' + str(limitPrice) + '] '))
  refTime = time.time()
  nChases=0
  while True:
    if ftxGetRemainingSize(ftx,orderId) == 0: break
    if side=='BUY':
      newRefPrice=ftxGetBid(ftx,ticker)
    else:
      newRefPrice=ftxGetAsk(ftx,ticker)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>maxWaitTime):
      refPrice=newRefPrice
      nChases+=1
      if nChases>maxChases and ftxGetRemainingSize(ftx,orderId)==qty:
        mult=.95 if side == 'BUY' else 1.05
        farPrice = roundPrice(ftx,'ftx', ticker,refPrice * mult)
        try:
          orderId = ftx.private_post_orders_order_id_modify({'order_id': orderId, 'price': farPrice})['result']['id']
        except:
          break
        if ftxGetRemainingSize(ftx, orderId) == qty:
          ftx.private_delete_orders_order_id({'order_id': orderId})
          print(timeTag('Cancelled'))
          return 0
      else:
        refTime=time.time()
        newLimitPrice=roundPrice(ftx,'ftx',ticker,refPrice,side=side,distance=distance)
        if ((side=='BUY' and newLimitPrice > limitPrice) or (side=='SELL' and newLimitPrice < limitPrice)) and limitPrice!=refPrice:
          print(timeTag('[DEBUG: replace order; nChases=' + str(nChases) + '; price=' + str(limitPrice) + '->' + str(newLimitPrice) + ']'))
          limitPrice=newLimitPrice
          try:
            orderId=ftx.private_post_orders_order_id_modify({'order_id':orderId,'price':limitPrice})['result']['id']
          except:
            break
        else:
          print(timeTag('[DEBUG: leave order alone; nChases=' + str(nChases) + '; price=' + str(limitPrice) + ']'))
    time.sleep(1)
  fill=ftxGetFillPrice(ftx,orderId)
  print(timeTag('Filled at '+str(round(fill,6))))
  return fill

#############################################################################################

####
# BB
####
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
def bbGetSpotPos(bb,ccy):
  wallet = pd.DataFrame(bb.v2_private_get_wallet_balance()['result']).transpose()
  return float(wallet.loc[ccy, 'equity'])

@retry(wait_fixed=1000)
def bbGetEstFunding1(bb,ccy):
  return float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': ccy+'USD'})['result']['funding_rate']) * 3 * 365

@retry(wait_fixed=1000)
def bbGetEstFunding2(bb, ccy):
  return float(bb.v2PrivateGetFundingPredictedFunding({'symbol': ccy+'USD'})['result']['predicted_funding_rate']) * 3 * 365

@retry(wait_fixed=1000)
def bbGetTickSize(bb,ccy,isBBT=False):
  ticker=ccy+'USD'
  if isBBT: ticker+='T'
  key='bbTickSize'
  df=cache('r',key)
  if df is None:
    df = pd.DataFrame(bb.v2_public_get_symbols()['result']).set_index('name')['price_filter']
    cache('w',key,df)
  return float(df[ticker]['tick_size'])

def bbRelOrderCore(side,bb,ccy,maxChases,distance,exch,ticker,qty,getBidFunc,getAskFunc,getOrderFunc,getFillPriceFunc,orderReplaceFunc,orderCancelFunc):
  # Do not use @retry
  def getIsReduceOnly(bb, ccy, side, qty):
    df = pd.DataFrame(bb.private_linear_get_position_list({'symbol': ccy + 'USDT'})['result']).set_index('side')
    oppSide = 'Sell' if side == 'BUY' else 'Buy'
    return qty <= float(df.loc[oppSide, 'size'])
  #####
  if side=='BUY':
    refPrice = getBidFunc(bb, ccy)
  else:
    refPrice = getAskFunc(bb, ccy)
  limitPrice = roundPrice(bb, exch, ccy, refPrice, side=side, distance=distance)
  if exch=='bb':
    orderId=bb.v2_private_post_order_create({'side':side.capitalize(),'symbol':ticker,'order_type':'Limit','qty':qty,'price':limitPrice,'time_in_force':'GoodTillCancel'})['result']['order_id']
  else:
    orderId = bb.private_linear_post_order_create({'side': side.capitalize(), 'symbol': ticker, 'order_type': 'Limit', 'qty': qty, 'price': limitPrice, 'time_in_force': 'GoodTillCancel',
                                                   'reduce_only': bool(getIsReduceOnly(bb, ccy, side, qty)), 'close_on_trigger': False})['result']['order_id']
  print(timeTag('[DEBUG: orderId=' + orderId + '; price=' + str(limitPrice) + '] '))
  refTime = time.time()
  nChases=0
  while True:
    orderStatus=getOrderFunc(bb,ticker,orderId)
    if orderStatus['order_status']=='Filled': break
    if side=='BUY':
      newRefPrice=getBidFunc(bb,ccy)
    else:
      newRefPrice=getAskFunc(bb,ccy)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_CONFIGS_DICT[exch.upper()+'_MAX_WAIT_TIME']):
      refPrice = newRefPrice
      nChases+=1
      orderStatus = getOrderFunc(bb, ticker, orderId)
      if orderStatus['order_status']=='Filled': break
      if nChases>maxChases and float(orderStatus['cum_exec_qty'])==0:
        mult = .95 if side == 'BUY' else 1.05
        farPrice = roundPrice(bb,exch,ccy,refPrice*mult)
        try:
          orderReplaceFunc({'symbol':ticker,'order_id':orderId, 'p_r_price': farPrice})
        except:
          break
        orderStatus = getOrderFunc(bb, ticker, orderId)
        if float(orderStatus['cum_exec_qty']) == 0:
          orderCancelFunc({'symbol': ticker, 'order_id': orderId})
          print(timeTag('Cancelled'))
          return 0
      else:
        refTime = time.time()
        newLimitPrice=roundPrice(bb,exch,ccy,refPrice,side=side,distance=distance)
        if ((side == 'BUY' and newLimitPrice > limitPrice) or (side == 'SELL' and newLimitPrice < limitPrice)) and limitPrice!=refPrice:
          print(timeTag('[DEBUG: replace order; nChases=' + str(nChases) + '; price=' + str(limitPrice) + '->' + str(newLimitPrice) + ']'))
          limitPrice=newLimitPrice
          try:
            orderReplaceFunc({'symbol':ticker,'order_id':orderId, 'p_r_price': limitPrice})
          except:
            break
        else:
          print(timeTag('[DEBUG: leave order alone; nChases=' + str(nChases)+'; price='+str(limitPrice)+']'))
    time.sleep(1)
  fill=getFillPriceFunc(bb, ticker, orderId)
  print(timeTag('Filled at ' + str(round(fill, 6))))
  if ccy=='SHIB1000': fill/=1000 # Special fix for SHIB
  return fill

def bbRelOrder(side,bb,ccy,trade_notional,maxChases=0,distance=0):
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
  assertSide(side)
  ticker=ccy+'USD'
  trade_notional = round(trade_notional)
  print(timeTag('Sending BB ' + side + ' order of ' + ticker + ' (notional=$'+ str(trade_notional)+') ....'))
  return bbRelOrderCore(side,bb,ccy,maxChases,distance,'bb',ticker,trade_notional,
                        bbGetBid,bbGetAsk,bbGetOrder,bbGetFillPrice,
                        bb.v2_private_post_order_replace,bb.v2_private_post_order_cancel)

#############################################################################################

#####
# BBT
#####
@retry(wait_fixed=1000)
def bbtGetFutPos(bb,ccy):
  if ccy=='SHIB': # Special fix for SHIB
    return bbtGetFutPos(bb,'SHIB1000')*1000
  else:
    df=pd.DataFrame(bb.private_linear_get_position_list({'symbol':ccy+'USDT'})['result']).set_index('side')
    return float(df.loc['Buy','size'])-float(df.loc['Sell','size'])

@retry(wait_fixed=1000)
def bbtGetEstFunding1(bb,ccy):
  if ccy=='SHIB': # Special fix for SHIB
    return bbtGetEstFunding1(bb, 'SHIB1000')
  else:
    return float(bb.public_linear_get_funding_prev_funding_rate({'symbol': ccy+'USDT'})['result']['funding_rate'])*3*365

@retry(wait_fixed=1000)
def bbtGetEstFunding2(bb,ccy):
  if ccy == 'SHIB':
    return bbtGetEstFunding2(bb, 'SHIB1000')
  else:
    return float(bb.private_linear_get_funding_predicted_funding({'symbol': ccy+'USDT'})['result']['predicted_funding_rate'])* 3 * 365

@retry(wait_fixed=1000)
def bbtGetRiskDf(bb, spotDict):
  # Get position list dataframe
  plDf = bb.private_linear_get_position_list()['result']
  plDf = pd.DataFrame([pos['data'] for pos in plDf]).set_index('symbol')
  buyDf = plDf[plDf['side'] == 'Buy']
  sellDf = plDf[plDf['side'] == 'Sell']
  validSymbols = []
  for symbol in plDf.index.unique():
    if buyDf.loc[symbol, 'size'] != sellDf.loc[symbol, 'size']: validSymbols.append(symbol)
  plDf = plDf.loc[validSymbols]
  dfSetFloat(plDf, ['size', 'position_value', 'liq_price', 'unrealised_pnl', 'entry_price', 'leverage'])

  # Get dictionaries of risk_id -> mm
  mmDict = dict()
  for symbol in validSymbols:
    riskLimit = bb.public_linear_get_risk_limit({'symbol': symbol})['result']
    for i in range(len(riskLimit)):
      mmDict[riskLimit[i]['id']] = float(riskLimit[i]['maintain_margin'])

  # Generate riskDf
  df = pd.DataFrame()
  for symbol in validSymbols:
    ccy = symbol[:(len(symbol) - 4)]
    tmp = plDf.loc[symbol].set_index('side')
    position_value = tmp.loc['Buy', 'position_value'] - tmp.loc['Sell', 'position_value']
    dominantSide = 'Buy' if tmp.loc['Buy', 'size'] >= tmp.loc['Sell', 'size'] else 'Sell'
    if ccy=='SHIB1000': # Special fix for SHIB
      if 'SHIB' not in spotDict: spotDict['SHIB'] = bbtGetMid(bb,'SHIB')
      spot_price = spotDict['SHIB'] / spotDict['USDT'] * 1000
    else:
      if ccy not in spotDict: spotDict[ccy] = bbtGetMid(bb,ccy)
      spot_price = spotDict[ccy] / spotDict['USDT']
    liq_price = tmp.loc[dominantSide, 'liq_price']
    liq = liq_price / spot_price
    unrealised_pnl = tmp['unrealised_pnl'].sum()
    df = df.append({'ccy': 'SHIB' if ccy=='SHIB1000' else ccy, # Special fix for SHIB
                    'position_value': position_value,
                    'spot_price': spot_price,
                    'liq_price': liq_price,
                    'liq': liq,
                    'unrealised_pnl': unrealised_pnl,
                    'size': tmp.loc[dominantSide, 'size'],
                    'entry_price': tmp.loc[dominantSide, 'entry_price'],
                    'leverage': tmp.loc[dominantSide, 'leverage'],
                    'mm': mmDict[tmp.loc[dominantSide, 'risk_id']]}, ignore_index=True)
  df = df.set_index('ccy')
  df['im_value'] = abs(df['size']) * (df['entry_price'] / df['leverage'])
  df['mm_value'] = (df['position_value'] * df['mm']).abs()
  df['delta_value'] = df['position_value'] + df['unrealised_pnl']
  return df[['position_value', 'delta_value', 'spot_price', 'liq_price', 'liq', 'unrealised_pnl', 'im_value', 'mm_value']]

@retry(wait_fixed=1000)
def bbtGetTradeExecutionList(bb,ccy):
  if ccy=='SHIB':
    myList=bbtGetTradeExecutionList(bb,'SHIB1000') # special fix for SHIB
    for i in range(len(myList)):
      myList[i]['symbol']='SHIBUSDT'
    return myList
  else:
    return bb.private_linear_get_trade_execution_list({'symbol': ccy + 'USDT', 'start_time': getYest() * 1000, 'exec_type': 'Funding', 'limit': 1000})['result']['data']

def bbtRelOrder(side,bb,ccy,trade_qty,maxChases=0,distance=0):
  @retry(wait_fixed=1000)
  def bbtGetOrder(bb, ticker, orderId):
    return bb.private_linear_get_order_search({'symbol': ticker, 'order_id': orderId})['result']
  # Do not use @retry
  def bbtGetFillPrice(bb, ticker, orderId):
    orderStatus = bbtGetOrder(bb, ticker, orderId)
    return float(orderStatus['cum_exec_value']) / float(orderStatus['cum_exec_qty'])
  #####
  if ccy=='SHIB': # Special fix for SHIB
    ccy='SHIB1000'
    trade_qty/=1000
  #####
  assertSide(side)
  ticker=ccy+'USDT'
  qty = round(trade_qty, 3)
  print(timeTag('Sending BBT ' + side + ' order of ' + ticker + ' (qty='+ str(qty)+') ....'))
  return bbRelOrderCore(side,bb,ccy,maxChases,distance,'bbt',ticker,qty,
                        bbtGetBid,bbtGetAsk,bbtGetOrder,bbtGetFillPrice,
                        bb.private_linear_post_order_replace,bb.private_linear_post_order_cancel)

#############################################################################################

####
# DB
####
@retry(wait_fixed=1000)
def dbGetFutPos(db,ccy):
  return float(db.private_get_get_position({'instrument_name': ccy + '-PERPETUAL'})['result']['size'])

@retry(wait_fixed=1000)
def dbGetSpotPos(db,ccy):
  return float(db.private_get_get_account_summary({'currency': ccy})['result']['equity'])

@retry(wait_fixed=1000)
def dbGetEstFunding(db,ccy,mins=15):
  now=datetime.datetime.now()
  start_timestamp = int(datetime.datetime.timestamp(now - pd.DateOffset(minutes=mins)))*1000
  end_timestamp = int(datetime.datetime.timestamp(now))*1000
  return float(db.public_get_get_funding_rate_value({'instrument_name': ccy+'-PERPETUAL', 'start_timestamp': start_timestamp, 'end_timestamp': end_timestamp})['result'])*(60/mins)*24*365

def dbRelOrder(side,db,ccy,trade_notional,maxChases=0,distance=0):
  @retry(wait_fixed=1000)
  def dbGetOrder(db, orderId):
    return db.private_get_get_order_state({'order_id': orderId})['result']
  # Do not use @retry
  def dbEditOrder(db, orderId, trade_notional, limitPrice):
    if dbGetOrder(db, orderId)['order_state'] == 'filled':
      return False
    try:
      db.private_get_edit({'order_id': orderId, 'amount': trade_notional, 'price': limitPrice})
      return True
    except:
      return False
  #####
  assertSide(side)
  if ccy == 'BTC':
    trade_notional = round(trade_notional, -1)
  elif ccy == 'ETH':
    trade_notional = round(trade_notional)
  else:
    sys.exit(1)
  ticker = ccy + '-PERPETUAL'
  print(timeTag('Sending DB ' + side + ' order of ' + ticker + ' (notional=$' + str(trade_notional) + ') ....'))
  if side == 'BUY':
    refPrice = dbGetBid(db, ccy)
    limitPrice = roundPrice(db, 'db', ccy, refPrice, side=side, distance=distance)
    orderId = db.private_get_buy({'instrument_name': ticker, 'amount': trade_notional, 'type': 'limit', 'price': limitPrice})['result']['order']['order_id']
  else:
    refPrice = dbGetAsk(db, ccy)
    limitPrice = roundPrice(db, 'db', ccy, refPrice, side=side, distance=distance)
    orderId = db.private_get_sell({'instrument_name': ticker, 'amount': trade_notional, 'type': 'limit', 'price': limitPrice})['result']['order']['order_id']
  print(timeTag('[DEBUG: orderId=' + orderId + '; price=' + str(limitPrice) + '] '))
  refTime = time.time()
  nChases = 0
  while True:
    if dbGetOrder(db, orderId)['order_state'] == 'filled':
      break
    if side == 'BUY':
      newRefPrice = dbGetBid(db, ccy)
    else:
      newRefPrice = dbGetAsk(db, ccy)
    if (side == 'BUY' and newRefPrice > refPrice) or (side == 'SELL' and newRefPrice < refPrice) or ((time.time() - refTime) > CT_CONFIGS_DICT['DB_MAX_WAIT_TIME']):
      refPrice = newRefPrice
      nChases += 1
      orderStatus = dbGetOrder(db, orderId)
      if orderStatus['order_state'] == 'filled':
        break
      if nChases > maxChases and float(orderStatus['filled_amount']) == 0:
        mult = .98 if side == 'BUY' else 1.02
        farPrice = roundPrice(db, 'db', ccy, refPrice * mult)
        if not dbEditOrder(db, orderId, trade_notional, farPrice):
          break
        if float(dbGetOrder(db, orderId)['filled_amount']) == 0:
          db.private_get_cancel({'order_id': orderId})
          print(timeTag('Cancelled'))
          return 0
      else:
        refTime = time.time()
        newLimitPrice = roundPrice(db, 'db', ccy, refPrice, side=side, distance=distance)
        if ((side == 'BUY' and newLimitPrice > limitPrice) or (side == 'SELL' and newLimitPrice < limitPrice)) and limitPrice!=refPrice:
          print(timeTag('[DEBUG: replace order; nChases=' + str(nChases) + '; price=' + str(limitPrice) + '->' + str(newLimitPrice) + ']'))
          limitPrice = newLimitPrice
          if not dbEditOrder(db, orderId, trade_notional, limitPrice):
            break
        else:
          print(timeTag('[DEBUG: leave order alone; nChases=' + str(nChases) + '; price=' + str(limitPrice) + ']'))
    time.sleep(1)
  fill = float(dbGetOrder(db, orderId)['average_price'])
  print(timeTag('Filled at ' + str(round(fill, 6))))
  return fill

#############################################################################################

####
# KF
####
def kfCcyToSymbol(ccy,isIndex=False):
  suffix ='XBT' if ccy=='BTC' else ccy
  suffix = '_'+suffix.lower()+'usd'
  if isIndex:
    return 'in'+suffix
  else:
    return 'pi'+suffix

@retry(wait_fixed=1000)
def kfGetFutPos(kf,ccy):
  symbol=kfCcyToSymbol(ccy)
  return kf.query('accounts')['accounts']['f'+symbol[1:]]['balances'][symbol]

@retry(wait_fixed=1000)
def kfGetSpotPos(kf,ccy,isIncludeHoldingWallets=False):
  accounts = kf.query('accounts')['accounts']
  ccy2 = 'xbt' if ccy == 'BTC' else ccy.lower()
  pos = accounts['fi_' + ccy2 + 'usd']['auxiliary']['pv']
  if isIncludeHoldingWallets: pos+=accounts['cash']['balances'][ccy2]
  return pos

@retry(wait_fixed=1000)
def kfGetTickers(kf):
  return pd.DataFrame(kf.query('tickers')['tickers']).set_index('symbol')

@retry(wait_fixed=1000)
def kfGetEstFunding1(kf,ccy,kfTickers=None):
  if kfTickers is None: kfTickers=kfGetTickers(kf)
  symbol=kfCcyToSymbol(ccy)
  return kfTickers.loc[symbol,'fundingRate']*kfTickers.loc[symbol,'markPrice']*24*365

@retry(wait_fixed=1000)
def kfGetEstFunding2(kf, ccy,kfTickers=None):
  if kfTickers is None: kfTickers = kfGetTickers(kf)
  symbol = kfCcyToSymbol(ccy)
  return kfTickers.loc[symbol, 'fundingRatePrediction']*kfTickers.loc[symbol,'markPrice']*24*365

def kfRelOrder(side,kf,ccy,trade_notional,maxChases=0,distance=0):
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
  assertSide(side)
  symbol=kfCcyToSymbol(ccy)
  trade_notional = round(trade_notional)
  print(timeTag('Sending KF ' + side + ' order of ' + symbol + ' (notional=$' + str(trade_notional) + ') ....'))
  if side == 'BUY':
    refPrice = kfGetBid(kf, ccy)
  else:
    refPrice = kfGetAsk(kf, ccy)
  limitPrice = roundPrice(kf,'kf',ccy,refPrice,side=side,distance=distance)
  orderId=kf.query('sendorder',{'orderType':'lmt','symbol':symbol,'side':side.lower(),'size':trade_notional,'limitPrice':limitPrice})['sendStatus']['order_id']
  print(timeTag('[DEBUG: orderId=' + orderId + '; price=' + str(limitPrice) + '] '))
  refTime=time.time()
  nChases=0
  while True:
    orderStatus=kfGetOrderStatus(kf,orderId)
    if orderStatus is None:  # If order doesn't exist, it means all executed
      break
    if side=='BUY':
      newRefPrice=kfGetBid(kf,ccy)
    else:
      newRefPrice=kfGetAsk(kf,ccy)
    if (side=='BUY' and newRefPrice > refPrice) or (side=='SELL' and newRefPrice < refPrice) or ((time.time()-refTime)>CT_CONFIGS_DICT['KF_MAX_WAIT_TIME']):
      refPrice=newRefPrice
      nChases+=1
      orderStatus = kfGetOrderStatus(kf, orderId)
      if orderStatus is None:  # If order doesn't exist, it means all executed
        break
      if nChases>maxChases and float(orderStatus['filledSize'])==0:
        mult = .98 if side == 'BUY' else 1.02
        farPrice = roundPrice(kf,'kf', ccy,refPrice * mult)
        try:
          kf.query('editorder',{'orderId':orderId,'limitPrice':farPrice})
        except:
          break
        orderStatus = kfGetOrderStatus(kf, orderId)
        if orderStatus is None:  # If order doesn't exist, it means all executed
          break
        if float(orderStatus['filledSize']) == 0:
          kf.query('cancelorder',{'order_id':orderId})
          print(timeTag('Cancelled'))
          return 0
      else:
        refTime=time.time()
        newLimitPrice = roundPrice(kf,'kf',ccy,refPrice,side=side,distance=distance)
        if ((side=='BUY' and newLimitPrice > limitPrice) or (side=='SELL' and newLimitPrice < limitPrice)) and limitPrice!=refPrice:
          print(timeTag('[DEBUG: replace order; nChases=' + str(nChases) + '; price=' + str(limitPrice) + '->' + str(newLimitPrice) + ']'))
          limitPrice=newLimitPrice
          try:
            kf.query('editorder', {'orderId': orderId, 'limitPrice': limitPrice})
          except:
            break
        else:
          print(timeTag('[DEBUG: leave order alone; nChases=' + str(nChases) + '; price=' + str(limitPrice) + ']'))
    time.sleep(1)
  fill=kfGetFillPrice(kf, orderId)
  print(timeTag('Filled at ' + str(round(fill, 6))))
  return fill

#############################################################################################

#####
# KUT
#####
def kutGetCcy(ccy):
  ccy2 = 'XBT' if ccy == 'BTC' else ccy
  return ccy2

@retry(wait_fixed=1000)
def kutGetPos(kut, ccy):
  return kut.futuresPrivate_get_position({'symbol': kutGetCcy(ccy) + 'USDTM'})['data']

@retry(wait_fixed=1000)
def kutGetPositions(kut):
  return pd.DataFrame(kut.futuresPrivate_get_positions()['data']).set_index('symbol')

def kutGetFutPos(kut, ccy):
  return float(kutGetPos(kut,ccy)['currentQty'])

@retry(wait_fixed=1000)
def kutGetEstFunding1(kut, ccy):
  return float(kut.futuresPublic_get_funding_rate_symbol_current({'symbol': '.' + kutGetCcy(ccy) + 'USDTMFPI8H'})['data']['value']) * 3 * 365

@retry(wait_fixed=1000)
def kutGetEstFunding2(kut, ccy):
  return float(kut.futuresPublic_get_funding_rate_symbol_current({'symbol': '.' + kutGetCcy(ccy) + 'USDTMFPI8H'})['data']['predictedValue']) * 3 * 365

@retry(wait_fixed=1000)
def kutGetEstFundings(kut, ccy):
  data=kut.futuresPublic_get_funding_rate_symbol_current({'symbol': '.' + kutGetCcy(ccy) + 'USDTMFPI8H'})['data']
  return float(data['value']) * 3 * 365, float(data['predictedValue']) * 3 * 365

@retry(wait_fixed=1000)
def kutGetRiskLimit(kut,ccy,isAllowOverrides=True):
  if isAllowOverrides:
    if ccy in SHARED_ETC_DICT['KUT_RISKLIMIT_OVERRIDE']:
      return SHARED_ETC_DICT['KUT_RISKLIMIT_OVERRIDE'][ccy]
  return kut.futuresPublic_get_contracts_symbol({'symbol': kutGetCcy(ccy) + 'USDTM'})['data']['maxRiskLimit']

@retry(wait_fixed=1000)
def kutGetUSDTDict(kut):
  return kut.futuresPrivate_get_account_overview({'currency': 'USDT'})['data']

def kutGetRiskDf(kut,availableBalance=None):
  if availableBalance is None:
    availableBalance = float(kutGetUSDTDict(kut)['availableBalance'])
  df = kutGetPositions(kut)
  df = df[['markPrice','markValue','maintMargin','liquidationPrice']].astype(float)
  df['liqRaw'] = df['liquidationPrice'] / df['markPrice']
  df['liq'] = df['liqRaw'] - (availableBalance / df['markValue'])
  df['ratio'] = df['maintMargin'] / df['markValue']
  df=df[['liqRaw','liq','maintMargin','markValue','ratio']]
  return df

@retry(wait_fixed=1000)
def kutGetTickSize(kut, ccy):
  key='kutTickSize'
  df=cache('r',key)
  if df is None:
    df = pd.DataFrame(kut.futuresPublic_get_contracts_active()['data']).set_index('symbol')
  return float(df.loc[kutGetCcy(ccy)+'USDTM','tickSize'])

@retry(wait_fixed=1000)
def kutGetMult(kut, ccy):
  key='kutMult'
  df=cache('r',key)
  if df is None:
    df = pd.DataFrame(kut.futuresPublic_get_contracts_active()['data']).set_index('symbol')
  return float(df.loc[kutGetCcy(ccy)+'USDTM','multiplier'])

@retry(wait_fixed=1000)
def kutGetMaxLeverage(kut, ccy):
  key='kutMaxLeverage'
  df=cache('r',key)
  if df is None:
    df = pd.DataFrame(kut.futuresPublic_get_contracts_active()['data']).set_index('symbol')
    #df.loc['ADAUSDTM','maxLeverage']=10 # Special fix for ADA
  return float(df.loc[kutGetCcy(ccy)+'USDTM','maxLeverage'])

@retry(wait_fixed=1000)
def kutGetOrder(kut, orderId):
  return kut.futuresPrivate_get_orders_order_id({'order-id': orderId})['data']

def kutPlaceOrder(kut, ticker, side, qty, limitPrice, ccy):
  isOk=False
  for i in range(3):
    try:
      result=kut.futuresPrivate_post_orders({'clientOid': uuid.uuid4().hex, 'side': side.lower(), 'symbol': ticker, 'type': 'limit', 'leverage': kutGetMaxLeverage(kut, ccy), 'price': limitPrice, 'size': qty})
      isOk=True
      break
    except ccxt.RateLimitExceeded:
      print(timeTag('KUT rate limit exceeded; trying to recover ....'))
      time.sleep(3)
    except:
      print(traceback.print_exc())
      sys.exit(1)
  if not isOk:
    sys.exit(1)
  #####
  try:
    return result['data']['orderId']
  except:
    print(result)
    sys.exit(1)

def kutCancelOrder(kut, orderId):
  try:
    kut.futuresPrivate_delete_orders_order_id({'order-id': orderId})
  except:
    pass
  while True:
    orderStatus = kutGetOrder(kut, orderId)
    if orderStatus['status'] == 'done': return float(orderStatus['size']) - float(orderStatus['filledSize'])
    time.sleep(1)

def kutCalcFill(orderStatus,mult):
  filledSize = float(orderStatus['filledSize'])
  filledValue = float(orderStatus['filledValue'])
  if filledSize == 0:
    return 0
  else:
    return filledValue / filledSize / mult

def kutRelOrder(side, kut, ccy, trade_qty, maxChases=0, distance=0):
  assertSide(side)
  ticker=kutGetCcy(ccy)+'USDTM'
  mult=kutGetMult(kut, ccy)
  qty=round(trade_qty/mult)
  print(timeTag('Sending KUT '+side+' order of '+ticker+' (qty='+str(qty)+'; mult='+str(mult)+') ....'))
  if side == 'BUY':
    refPrice = kutGetBid(kut, ccy)
  else:
    refPrice = kutGetAsk(kut, ccy)
  limitPrice = roundPrice(kut, 'kut', ccy, refPrice, side=side, distance=distance)
  orderId=kutPlaceOrder(kut, ticker, side, qty, limitPrice, ccy)
  print(timeTag('[DEBUG: orderId=' + orderId + '; price=' + str(limitPrice) + '] '))
  refTime = time.time()
  nChases=0
  while True:
    orderStatus = kutGetOrder(kut, orderId)
    if orderStatus['status']=='done': break
    if side=='BUY':
      newRefPrice=kutGetBid(kut, ccy)
    else:
      newRefPrice=kutGetAsk(kut, ccy)
    if (side == 'BUY' and newRefPrice > refPrice) or (side == 'SELL' and newRefPrice < refPrice) or ((time.time() - refTime) > CT_CONFIGS_DICT['KUT_MAX_WAIT_TIME']):
      refPrice=newRefPrice
      nChases+=1
      orderStatus = kutGetOrder(kut, orderId)
      if orderStatus['status'] == 'done': break
      if nChases > maxChases and float(orderStatus['size'])==qty and float(orderStatus['filledSize']) == 0:
        leavesQty = kutCancelOrder(kut, orderId)
        if leavesQty == 0: break
        print(timeTag('Cancelled'))
        return 0
      else:
        refTime = time.time()
        newLimitPrice = roundPrice(kut, 'kut', ccy, refPrice, side=side, distance=distance)
        if ((side == 'BUY' and newLimitPrice > limitPrice) or (side == 'SELL' and newLimitPrice < limitPrice)) and limitPrice!=refPrice:
          print(timeTag('[DEBUG: replace order; nChases=' + str(nChases) + '; price=' + str(limitPrice) + '->' + str(newLimitPrice) + ']'))
          limitPrice = newLimitPrice
          leavesQty = kutCancelOrder(kut, orderId)
          if leavesQty == 0: break
          orderId = kutPlaceOrder(kut, ticker, side, leavesQty, limitPrice, ccy)
        else:
          print(timeTag('[DEBUG: leave order alone; nChases=' + str(nChases) + '; price=' + str(limitPrice) + ']'))
    time.sleep(1)
  orderStatus = kutGetOrder(kut, orderId)
  return kutCalcFill(orderStatus,mult)

def kutCrossOrder(kutNB, kutNS, ccy, trade_qty, distance=0):
  @retry(wait_fixed=1000)
  def getData(kut,ticker):
    return kut.futuresPublic_get_ticker({'symbol': ticker})['data']
  #####
  if kutNB==kutNS:
    print('Cannot cross against oneself!')
    sys.exit(1)
  kutB=kutCCXTInit(kutNB)
  kutS=kutCCXTInit(kutNS)
  ticker=kutGetCcy(ccy)+'USDTM'
  mult=kutGetMult(kutB, ccy)
  qty=round(trade_qty/mult)
  print(timeTag('Monitoring '+ticker+' in KUT ....'))
  tickSize=kutGetTickSize(kutB, ccy)
  prevMid=0
  stableCount = 0
  while True:
    data = getData(kutB,ticker)
    bid = float(data['bestBidPrice'])
    ask = float(data['bestAskPrice'])
    mid = roundPrice(kutB, 'kut', ccy, (bid+ask)/2, side='BUY', distance=0)
    spread = round((ask-bid)/tickSize)
    if bid < prevMid < ask:
      stableCount+=1
    else:
      stableCount=0
    prevMid = mid
    print(timeTag('Spread='+str(spread)+'; stable count='+str(stableCount)))
    if spread>=2 and stableCount >=2: break
    time.sleep(2)
  suffix = ' (qty=' + str(qty) + '; mult=' + str(mult) + ') ....'
  print(timeTag('Sending buy order in KUT' + str(kutNB) + suffix))
  print(timeTag('Sending sell order in KUT' + str(kutNS) + suffix))
  buyOrderId = kutPlaceOrder(kutB, ticker, 'BUY', qty, mid, ccy)
  print(timeTag('[DEBUG: buyOrderId=' + buyOrderId + '; price=' + str(mid) + '] '))
  sellOrderId = kutPlaceOrder(kutS, ticker, 'SELL', qty, mid, ccy)
  print(timeTag('[DEBUG: sellOrderId=' + sellOrderId + '; price=' + str(mid) + '] '))
  time.sleep(3)
  leavesQtyB=kutCancelOrder(kutB,buyOrderId)
  leavesQtyS=kutCancelOrder(kutS,sellOrderId)
  fillB1 = kutCalcFill(kutGetOrder(kutB, buyOrderId), mult)
  fillS1 = kutCalcFill(kutGetOrder(kutS, sellOrderId), mult)
  print(timeTag('[DEBUG: leavesQtyB='+str(round(leavesQtyB))+'; fillB1=' + str(fillB1) + ']'))
  print(timeTag('[DEBUG: leavesQtyS='+str(round(leavesQtyS))+'; fillS1='+str(fillS1)+']'))
  if leavesQtyB==0 and leavesQtyS==0:
    print(timeTag('[DEBUG: clean cross!]'))
    return 0 # zero slippage
  elif leavesQtyB>0 and leavesQtyS==0:
    fillB2=kutRelOrder('BUY', kutB, ccy, leavesQtyB*mult, maxChases=888, distance=distance)
    print(timeTag('[DEBUG: fillB2=' + str(fillB2) + ']'))
    fillBAvg=(fillB1*(qty-leavesQtyB) + fillB2*leavesQtyB)/qty
    fillSAvg=fillS1
  elif leavesQtyB==0 and leavesQtyS>0:
    fillS2=kutRelOrder('SELL', kutS, ccy, leavesQtyS*mult, maxChases=888, distance=distance)
    print(timeTag('[DEBUG: fillS2=' + str(fillS2) + ']'))
    fillSAvg = (fillS1 * (qty - leavesQtyS) + fillS2 * leavesQtyS) / qty
    fillBAvg=fillB1
  else: # partial fills for both
    print('kutCrossOrder abnormal termination!')
    sys.exit(1)
  print(timeTag('[DEBUG: fillBAvg=' + str(fillBAvg) + ']'))
  print(timeTag('[DEBUG: fillSAvg=' + str(fillSAvg) + ']'))
  return fillBAvg / fillSAvg - 1 # slippage

#############################################################################################

####################
# Smart basis models
####################
def getFundingDict(apiDict,ccy):
  ftx = apiDict['ftx']
  bb = apiDict['bb']
  db = apiDict['db']
  kf = apiDict['kf']
  kut = apiDict['kut']
  #####
  borrowS = ftxGetEstBorrow(ftx)
  d=dict()
  d['ftxEstBorrowUSD'] = borrowS['USD']
  d['ftxEstBorrowUSDT'] = borrowS['USDT']
  #####
  # Ccy-specific
  d['Ccy'] = ccy
  validExchs=getValidExchs(ccy)
  if 'ftx' in validExchs: d['ftxEstFunding'] = ftxGetEstFunding(ftx, ccy)
  if 'bb' in validExchs:
    d['bbEstFunding1'] = bbGetEstFunding1(bb, ccy)
    d['bbEstFunding2'] = bbGetEstFunding2(bb, ccy)
  if 'bbt' in validExchs:
    d['bbtEstFunding1'] = bbtGetEstFunding1(bb, ccy)
    d['bbtEstFunding2'] = bbtGetEstFunding2(bb, ccy)
  if 'db' in validExchs: d['dbEstFunding'] = dbGetEstFunding(db, ccy)
  if 'kf' in validExchs:
    kfTickers = kfGetTickers(kf)
    d['kfEstFunding1'] = kfGetEstFunding1(kf, ccy, kfTickers)
    d['kfEstFunding2'] = kfGetEstFunding2(kf, ccy, kfTickers)
  if 'kut' in validExchs:
    d['kutEstFunding1'],d['kutEstFunding2'] = kutGetEstFundings(kut, ccy)
  return d

#############################################################################################

def getOneDayShortSpotEdge(fundingDict):
  return getOneDayDecayedMean(fundingDict['ftxEstBorrowUSD'], SMB_DICT['BASE_RATE'], SMB_DICT['HALF_LIFE_HOURS']) / 365

def getOneDayUSDTCollateralBleed(fundingDict):
  return -getOneDayDecayedMean(fundingDict['ftxEstBorrowUSDT'], SMB_DICT['BASE_RATE'], SMB_DICT['HALF_LIFE_HOURS']) / 365 * SMB_DICT['USDT_COLLATERAL_COVERAGE']

def getOneDayShortFutEdge(hoursInterval,basis,snapFundingRate,estFundingRate,pctElapsedPower=1,prevFundingRate=None,isKF=False,isKU=False):
  # gain on projected basis mtm after 1 day
  edge=basis-getOneDayDecayedValues(basis, SMB_DICT['BASE_BASIS'], SMB_DICT['HALF_LIFE_HOURS'])[-1]

  # gain on coupon from previous reset
  hoursAccountedFor=0
  if not prevFundingRate is None:
    if isKF:
      pctToCapture = 1 - getPctElapsed(hoursInterval,isKU=isKU)
    else:
      pctToCapture = 1
    edge += prevFundingRate / 365 / (24 / hoursInterval) * pctToCapture
    hoursAccountedFor += hoursInterval * pctToCapture

  # gain on coupon from elapsed time
  pctElapsed = getPctElapsed(hoursInterval,isKU=isKU) ** pctElapsedPower
  edge += estFundingRate / 365 / (24 / hoursInterval) * pctElapsed
  hoursAccountedFor+=hoursInterval*pctElapsed

  # gain on projected funding pickup
  nMinutes = 1440 - round(hoursAccountedFor * 60)
  edge+= getOneDayDecayedMean(snapFundingRate, SMB_DICT['BASE_RATE'], SMB_DICT['HALF_LIFE_HOURS'], nMinutes=nMinutes) / 365 * (nMinutes / 1440)

  return edge

#############################################################################################

@retry(wait_fixed=1000)
def ftxGetOneDayShortFutEdge(ftx, fundingDict, basis):
  keySnap='ftxEMASnap'+fundingDict['Ccy']
  if cache('r',keySnap) is None:
    cache('w',keySnap,fundingDict['ftxEstFunding'])
  d=ftxGetFuture(ftx,fundingDict['Ccy'])
  snapFundingRate=(float(d['mark']) / float(d['index']) - 1)*365
  smoothedSnapFundingRate = getEMANow(snapFundingRate, cache('r',keySnap), CT_CONFIGS_DICT['EMA_K'])
  cache('w',keySnap,smoothedSnapFundingRate)
  return getOneDayShortFutEdge(1,basis,smoothedSnapFundingRate, fundingDict['ftxEstFunding'])

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
  ccy=fundingDict['Ccy']
  if ccy=='SHIB': ccy='SHIB1000' # Special fix for SHIB
  premIndex=np.mean([float(n) for n in pd.DataFrame(bb.public_linear_get_premium_index_kline({'symbol':ccy+'USDT','interval':1,'from':start_time})['result'])['close']])
  premIndexClamped  = premIndex + np.clip(0.0001 - premIndex, -0.0005, 0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['bbtEstFunding2'], prevFundingRate=fundingDict['bbtEstFunding1']) - getOneDayUSDTCollateralBleed(fundingDict)

@retry(wait_fixed=1000)
def dbGetOneDayShortFutEdge(db, fundingDict, basis):
  edge = basis - getOneDayDecayedValues(basis, SMB_DICT['BASE_BASIS'], SMB_DICT['HALF_LIFE_HOURS'])[-1] # basis
  edge += getOneDayDecayedMean(fundingDict['dbEstFunding'], SMB_DICT['BASE_RATE'], SMB_DICT['HALF_LIFE_HOURS']) / 365 # funding
  return edge

@retry(wait_fixed=1000)
def kfGetOneDayShortFutEdge(kf, kfTickers, fundingDict, basis):
  est2=fundingDict['kfEstFunding2']
  mid = kfGetMid(kf, fundingDict['Ccy'], kfTickers=kfTickers)
  premIndexClipped = np.clip(mid / kfTickers.loc[kfCcyToSymbol(fundingDict['Ccy'], isIndex=True), 'last'] - 1, -0.008, 0.008)
  snap = premIndexClipped * 365 * 3
  #####
  keySnap='kfEMASnap'+fundingDict['Ccy']
  if cache('r',keySnap) is None: cache('w',keySnap,est2) # seed with est2
  smoothedSnapFundingRate = getEMANow(snap, cache('r', keySnap), CT_CONFIGS_DICT['EMA_K'])
  cache('w', keySnap, smoothedSnapFundingRate)
  return getOneDayShortFutEdge(4, basis, smoothedSnapFundingRate, est2, pctElapsedPower=4, prevFundingRate=fundingDict['kfEstFunding1'], isKF=True)

@retry(wait_fixed=1000)
def kutGetOneDayShortFutEdge(kut, fundingDict, basis):
  premIndex=pd.DataFrame(kut.futuresPublic_get_premium_query({'symbol': '.' + kutGetCcy(fundingDict['Ccy']) + 'USDTMPI', 'maxCount':15})['data']['dataList'])['value'].astype(float).mean()
  premIndexClamped  = premIndex + np.clip(0.0001 - premIndex, -0.0005, 0.0005)
  snapFundingRate=premIndexClamped*365*3
  return getOneDayShortFutEdge(8, basis, snapFundingRate, fundingDict['kutEstFunding2'], prevFundingRate=fundingDict['kutEstFunding1'],isKU=True) - getOneDayUSDTCollateralBleed(fundingDict)

#############################################################################################

def getSmartBasisDict(apiDict, ccy, fundingDict, isSkipAdj=False):
  ftx = apiDict['ftx']
  bb = apiDict['bb']
  db = apiDict['db']
  kf = apiDict['kf']
  kut = apiDict['kut']
  #####
  validExchs = getValidExchs(ccy)
  objs=[]
  if 'ftx' in validExchs:
    ftxPrices = getPrices('ftx', ftx, ccy)
    objs.append(ftxPrices)
  if 'bbt' in validExchs:
    bbtPrices = getPrices('bbt', bb, ccy)
    objs.append(bbtPrices)
  if 'bb' in validExchs:
    bbPrices = getPrices('bb', bb, ccy)
    objs.append(bbPrices)
  if 'db' in validExchs:
    dbPrices = getPrices('db', db, ccy)
    objs.append(dbPrices)
  if 'kf' in validExchs:
    kfPrices = getPrices('kf', kf, ccy)
    objs.append(kfPrices)
  if 'kut' in validExchs:
    kutPrices = getPrices('kut',kut,ccy)
    objs.append(kutPrices)
  parallelRun(objs)
  #####
  d = dict()
  oneDayShortSpotEdge = getOneDayShortSpotEdge(fundingDict)
  if 'ftx' in validExchs:
    ftxAdj = 0 if isSkipAdj else (CT_CONFIGS_DICT['SPOT_' + ccy][1] - CT_CONFIGS_DICT['FTX_' + ccy][1]) / 10000
    d['ftxBasis'] = ftxPrices.fut / ftxPrices.spot - 1
    d['ftxSmartBasis'] = ftxGetOneDayShortFutEdge(ftx,fundingDict, d['ftxBasis']) - oneDayShortSpotEdge + ftxAdj
  if 'bb' in validExchs:
    bbAdj = 0 if isSkipAdj else (CT_CONFIGS_DICT['SPOT_' + ccy][1] - CT_CONFIGS_DICT['BB_' + ccy][1]) / 10000
    d['bbBasis'] = bbPrices.fut / ftxPrices.spot - 1
    d['bbSmartBasis'] = bbGetOneDayShortFutEdge(bb,fundingDict, d['bbBasis']) - oneDayShortSpotEdge + bbAdj
  if 'bbt' in validExchs:
    bbtAdj = 0 if isSkipAdj else (CT_CONFIGS_DICT['SPOT_' + ccy][1] - CT_CONFIGS_DICT['BBT_' + ccy][1]) / 10000
    d['bbtBasis'] = bbtPrices.fut * ftxPrices.spotUSDT / ftxPrices.spot - 1
    d['bbtSmartBasis'] = bbtGetOneDayShortFutEdge(bb, fundingDict, d['bbtBasis']) - oneDayShortSpotEdge + bbtAdj
  if 'db' in validExchs:
    dbAdj = 0 if isSkipAdj else (CT_CONFIGS_DICT['SPOT_' + ccy][1] - CT_CONFIGS_DICT['DB_' + ccy][1]) / 10000
    d['dbBasis'] = dbPrices.fut / ftxPrices.spot - 1
    d['dbSmartBasis'] = dbGetOneDayShortFutEdge(db, fundingDict, d['dbBasis']) - oneDayShortSpotEdge + dbAdj
  if 'kf' in validExchs:
    kfAdj = 0 if isSkipAdj else (CT_CONFIGS_DICT['SPOT_' + ccy][1] - CT_CONFIGS_DICT['KF_' + ccy][1]) / 10000
    d['kfBasis']= kfPrices.fut / ftxPrices.spot - 1
    d['kfSmartBasis'] = kfGetOneDayShortFutEdge(kf, kfPrices.kfTickers,fundingDict, d['kfBasis']) - oneDayShortSpotEdge + kfAdj
  if 'kut' in validExchs:
    kutAdj = 0 if isSkipAdj else (CT_CONFIGS_DICT['SPOT_' + ccy][1] - CT_CONFIGS_DICT['KUT_' + ccy][1]) / 10000
    d['kutBasis'] = kutPrices.fut * ftxPrices.spotUSDT / ftxPrices.spot - 1
    d['kutSmartBasis'] = kutGetOneDayShortFutEdge(kut, fundingDict, d['kutBasis']) - oneDayShortSpotEdge + kutAdj

  return d

#############################################################################################

###############
# CryptoAlerter
###############
def caRun(ccy, color):
  def process(exch, fundingDict, smartBasisDict, isEst2, color):
    smartBasisBps = smartBasisDict[exch + 'SmartBasis'] * 10000
    basisBps = smartBasisDict[exch + 'Basis'] * 10000
    if isEst2:
      est1=fundingDict[exch+'EstFunding1']
      est2=fundingDict[exch+'EstFunding2']
      n=23
    else:
      est1=fundingDict[exch+'EstFunding']
      n=20
    z = exch.upper() + ':' + str(round(smartBasisBps)) + '/' + str(round(basisBps)) + 'bps(' + str(round(est1 * 100))
    if isEst2: z = z + '/' + str(round(est2 * 100))
    z += ')'
    print(termcolor.colored(z.ljust(n), color), end='')
  #####
  printHeader(ccy+'a')
  col1N = 20
  print('Column 1:'.ljust(col1N)+'USD borrow rate / USDT borrow rate')
  print('Columns 2+:'.ljust(col1N)+'Smart basis / raw basis (est. funding rate)')
  print()
  #####
  validExchs=getValidExchs(ccy)
  apiDict = getApiDict()
  #####
  while True:
    fundingDict = getFundingDict(apiDict,ccy)
    smartBasisDict = getSmartBasisDict(apiDict,ccy, fundingDict, isSkipAdj=True)
    print(getCurrentTime(isCondensed=True).ljust(10),end='')
    print(termcolor.colored((str(round(fundingDict['ftxEstBorrowUSD'] * 100))+'/'+str(round(fundingDict['ftxEstBorrowUSDT'] * 100))).ljust(col1N-10),'red'),end='')
    for exch in validExchs:
      process(exch, fundingDict, smartBasisDict, exch in ['bb', 'bbt', 'kf', 'kut'], color)
    print()
    time.sleep(2)

#############################################################################################

##############
# CryptoTrader
##############
def ctInit(ccy, notional, tgtBps):
  apiDict = getApiDict()
  spot = ftxGetMid(apiDict['ftx'], ccy+'/USD')
  maxNotional = CT_CONFIGS_DICT['MAX_NOTIONAL_USD']
  notional = min(notional, maxNotional)
  qty = notional / spot
  printHeader(ccy+'t')
  print('Per Trade Notional: $'+str(notional))
  print('Per Trade Quantity: '+str(round(qty, 6)))
  print('Target:             '+str(round(tgtBps))+'bps')
  print()
  if CT_CONFIGS_DICT['IS_BBT_STEPPER']: cache('w','bbtStepperDict',None)    
  if CT_CONFIGS_DICT['IS_KUT_STEPPER']: cache('w','kutStepperDict',None)
  return apiDict,qty,notional,spot

def ctGetPosUSD(apiDict,exch, ccy, spot):
  if exch == 'ftx':
    return ftxGetFutPos(apiDict['ftx'], ccy) * spot
  elif exch == 'bb':
    return bbGetFutPos(apiDict['bb'], ccy)
  elif exch == 'bbt':
    return bbtGetFutPos(apiDict['bbtCurrent'], ccy) * spot
  elif exch == 'db':
    return dbGetFutPos(apiDict['db'], ccy)
  elif exch == 'kf':
    return kfGetFutPos(apiDict['kf'], ccy)
  elif exch == 'kut':
    return kutGetFutPos(apiDict['kutCurrent'], ccy) * kutGetMult(apiDict['kutCurrent'], ccy) * spot
  elif exch == 'spot':
    return ftxGetWallet(apiDict['ftx']).loc[ccy,'usdValue']
  else:
    sys.exit(1)

def ctGetSuffix(i, realizedSlippageBps):
  z= 'Program '+str(i+1)
  if len(realizedSlippageBps) > 0:
    z += ' / Avg realized slippage = ' + str(round(np.mean(realizedSlippageBps))) + 'bps'
  return termcolor.colored(z,'red')

def ctTooFewCandidates(i, realizedSlippageBps, color):
  print((getCurrentTime() + ':').ljust(23) + termcolor.colored('************ Too few candidates ************'.ljust(65), color) + ctGetSuffix(i,realizedSlippageBps))
  chosenLong = ''
  return chosenLong

def ctStreakEnded(i, realizedSlippageBps, color):
  print((getCurrentTime() + ':').ljust(23) + termcolor.colored('*************** Streak ended ***************'.ljust(65), color) + ctGetSuffix(i,realizedSlippageBps))
  prevSmartBasis = []
  chosenLong = ''
  chosenShort = ''
  return prevSmartBasis, chosenLong, chosenShort

def ctAssertNoStepper():
  if CT_CONFIGS_DICT['IS_BBT_STEPPER'] or CT_CONFIGS_DICT['IS_KUT_STEPPER']:
    print('Cannot use more than two parameters while using steppers!')
    sys.exit(1)

def ctBBTStepper(side, ccy, trade_qty):
  print((getCurrentTime() + ':').ljust(20) + ' Searching for the correct BBT account ... ',end='')
  buySell = 1 if side == 'BUY' else -1
  key='bbtStepperDict'
  d=cache('r',key)
  if d is None:
    d=dict()
    d['n']=CT_CONFIGS_DICT['CURRENT_BBT']
    d['isBuild'] = None
  while True:
    bb = bbCCXTInit(d['n'])
    pos = bbtGetFutPos(bb, ccy)
    posSim = pos + trade_qty * buySell
    # first iteration
    if d['isBuild'] is None:
      d['isBuild'] = pos==0 or (pos*buySell>0)
    # branches
    if not d['isBuild'] and posSim*buySell>=0:
      d['n']+=1
      if d['n'] > SHARED_EXCH_DICT['bbt']:
        print('No more unwind opportunities!')
        sys.exit(1)
      else:
        continue
    else:
      print('BBT' + str(d['n']))
      cache('w', key, d)
      break
  return bb

def ctKUTStepper(side, ccy, trade_qty):
  print((getCurrentTime() + ':').ljust(20) + ' Searching for the correct KUT account ... ',end='')
  buySell = 1 if side == 'BUY' else -1
  key='kutStepperDict'
  d=cache('r',key)
  if d is None:
    d=dict()
    d['n']=CT_CONFIGS_DICT['CURRENT_KUT']
    d['isBuild'] = None
  while True:
    kut = kutCCXTInit(d['n'])
    posData=kutGetPos(kut, ccy)
    pos = posData['currentQty'] * kutGetMult(kut, ccy)
    posSim = pos + trade_qty * buySell
    # first iteration
    if d['isBuild'] is None:
      d['isBuild'] = pos==0 or (pos*buySell>0)
      d['riskLimit'] = kutGetRiskLimit(kut, ccy)
      d['mid'] = kutGetMid(kut, ccy)
    # branches
    if d['isBuild'] and trade_qty>(d['riskLimit']-abs(posData['posCost'])-1000)/d['mid']:
      d['n'] +=1
      if d['n'] > SHARED_EXCH_DICT['kut']:
        print('No more build opportunities!')
        sys.exit(1)
      else:
        continue
    elif not d['isBuild'] and posSim*buySell>=0:
      d['n']+=1
      if d['n'] > SHARED_EXCH_DICT['kut']:
        print('No more unwind opportunities!')
        sys.exit(1)
      else:
        continue
    else:
      print('KUT' + str(d['n']))
      cache('w', key, d)
      break
  return kut

def ctGetMaxChases(completedLegs):
  if completedLegs == 0:
    return 2
  else:
    return 888

def ctGetDistance(prefix,completedLegs):
  return CT_CONFIGS_DICT[prefix+'_LEG1_DISTANCE_TICKS'] if completedLegs == 0 else CT_CONFIGS_DICT[prefix+'_LEG2_DISTANCE_TICKS']

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
  print(getCurrentTime() +   ': '+ termcolor.colored('Realized slippage = '+str(round(s))+'bps','red'))
  realizedSlippageBps.append(s)
  return realizedSlippageBps

def ctRun(ccy, notional, tgtBps, color):
  apiDict, trade_qty, trade_notional, spot = ctInit(ccy, notional, tgtBps)
  ftx = apiDict['ftx']
  bb = apiDict['bb']
  bbtCurrent = apiDict['bbtCurrent']
  db = apiDict['db']
  kf = apiDict['kf']
  kutCurrent = apiDict['kutCurrent']
  #####
  realizedSlippageBps = []
  for i in range(CT_CONFIGS_DICT['NPROGRAMS']):
    prevSmartBasis = []
    chosenLong = ''
    chosenShort = ''
    while True:
      time.sleep(2)
      fundingDict=getFundingDict(apiDict, ccy)
      smartBasisDict = getSmartBasisDict(apiDict ,ccy, fundingDict)
      smartBasisDict['spotSmartBasis'] = 0
      smartBasisDict['spotBasis'] = 0

      # Remove disabled instruments
      for exch in SHARED_CCY_DICT[ccy]['futExch'] + ['spot']:
        if CT_CONFIGS_DICT[exch.upper() + '_' + ccy][0] == 0:
          safeDel(smartBasisDict,exch + 'SmartBasis')
          safeDel(smartBasisDict,exch+'Basis')

      # Remove spots when high spot rate
      if CT_CONFIGS_DICT['IS_HIGH_USD_RATE_PAUSE'] and fundingDict['ftxEstBorrowUSD'] >= 1:
        for key in filterDict(smartBasisDict, 'spot'):
          del smartBasisDict[key]

      # Filter dictionary
      d = filterDict(smartBasisDict, 'SmartBasis')

      # Check for too few candidates
      if len(d.keys())<2:
        chosenLong = ctTooFewCandidates(i, realizedSlippageBps, color)
        continue  # to next iteration in While True loop

      # If pair not lock-in yet
      if chosenLong=='':

        # Pick pair to trade
        isTooFewCandidates = False
        while True:
          if len(d.keys()) < 2:
            isTooFewCandidates=True
            break
          keyMax=max(d.items(), key=operator.itemgetter(1))[0]
          keyMin=min(d.items(), key=operator.itemgetter(1))[0]
          smartBasisBps=(d[keyMax]-d[keyMin])*10000
          chosenLong = keyMin[:len(keyMin) - 10]
          chosenShort = keyMax[:len(keyMax) - 10]
          #####
          dLong = CT_CONFIGS_DICT[chosenLong.upper() + '_' + ccy]
          if len(dLong) > 2:
            ctAssertNoStepper()
            posUSDLong = ctGetPosUSD(apiDict, chosenLong, ccy, spot)
            if posUSDLong >= dLong[2]:
              del d[chosenLong + 'SmartBasis']
              continue
          #####
          dShort = CT_CONFIGS_DICT[chosenShort.upper() + '_' + ccy]
          if len(dShort) > 2:
            ctAssertNoStepper()
            posUSDShort = ctGetPosUSD(apiDict, chosenShort, ccy, spot)
            if posUSDShort <= -dShort[2]:
              del d[chosenShort + 'SmartBasis']
              continue
          #####
          break

        ###############

        # If too few candidates ....
        if isTooFewCandidates:
          chosenLong = ctTooFewCandidates(i, realizedSlippageBps, color)
          continue  # to next iteration in While True loop

        # If target not reached yet ....
        if smartBasisBps<tgtBps:
          z = (getCurrentTime() + ':').ljust(23)
          z += termcolor.colored((ccy+' (buy ' + chosenLong + '/sell '+chosenShort+') smart basis: '+str(round(smartBasisBps))+'bps').ljust(65),color)
          z += ctGetSuffix(i,realizedSlippageBps)
          print(z)
          chosenLong = ''
          continue # to next iteration in While True loop
        else:
          status=0

      # Maintenance
      try:
        smartBasisBps = (smartBasisDict[chosenShort+'SmartBasis'] - smartBasisDict[chosenLong+'SmartBasis'])* 10000
      except:
        prevSmartBasis, chosenLong, chosenShort = ctStreakEnded(i, realizedSlippageBps, color)
        continue # to next iteration in While True Loop
      basisBps      = (smartBasisDict[chosenShort+'Basis']      - smartBasisDict[chosenLong+'Basis'])*10000
      prevSmartBasis.append(smartBasisBps)
      prevSmartBasis= prevSmartBasis[-CT_CONFIGS_DICT['STREAK']:]
      isStable= (np.max(prevSmartBasis)-np.min(prevSmartBasis)) <= CT_CONFIGS_DICT['STREAK_RANGE_BPS']

      # If target reached ....
      if smartBasisBps>=tgtBps:
        status+=1
      else:
        prevSmartBasis, chosenLong, chosenShort = ctStreakEnded(i, realizedSlippageBps, color)
        continue # to next iteration in While True Loop

      # Chosen long/short legs
      z = (getCurrentTime() + ':').ljust(20) + termcolor.colored(str(status).rjust(2), 'red') + ' '
      z += termcolor.colored((ccy + ' (buy ' + chosenLong + '/sell '+chosenShort+') smart/raw basis: ' + str(round(smartBasisBps)) + '/' + str(round(basisBps)) + 'bps').ljust(65), color)
      print(z + ctGetSuffix(i,realizedSlippageBps))

      if abs(status) >= CT_CONFIGS_DICT['STREAK'] and isStable:
        print()
        speak('Go')
        completedLegs = 0
        isCancelled=False

        # Steppers
        if CT_CONFIGS_DICT['IS_BBT_STEPPER']:
          if 'bbt' == chosenLong:
            bbtCurrent = ctBBTStepper('BUY', ccy, trade_qty)
          if 'bbt' == chosenShort:
            bbtCurrent = ctBBTStepper('SELL', ccy, trade_qty)
        if CT_CONFIGS_DICT['IS_KUT_STEPPER']:
          if 'kut' == chosenLong:
            kutCurrent = ctKUTStepper('BUY', ccy, trade_qty)
          if 'kut' == chosenShort:
            kutCurrent = ctKUTStepper('SELL', ccy, trade_qty)

        # RelOrders
        if 'bbt' == chosenLong and not isCancelled:
          distance = ctGetDistance('BBT', completedLegs)
          longFill = bbtRelOrder('BUY', bbtCurrent, ccy, trade_qty,maxChases=ctGetMaxChases(completedLegs),distance=distance) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs,isCancelled=ctProcessFill(longFill,completedLegs,isCancelled)
        if 'bbt' == chosenShort and not isCancelled:
          distance = ctGetDistance('BBT', completedLegs)
          shortFill = bbtRelOrder('SELL', bbtCurrent, ccy, trade_qty,maxChases=ctGetMaxChases(completedLegs),distance=distance) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs,isCancelled=ctProcessFill(shortFill,completedLegs,isCancelled)
        if 'bb' == chosenLong and not isCancelled:
          distance = ctGetDistance('BB', completedLegs)
          longFill = bbRelOrder('BUY', bb, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs), distance=distance)
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'bb' == chosenShort and not isCancelled:
          distance = ctGetDistance('BB', completedLegs)
          shortFill = bbRelOrder('SELL', bb, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs), distance=distance)
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'kf' == chosenLong and not isCancelled:
          distance = ctGetDistance('KF', completedLegs)
          longFill = kfRelOrder('BUY', kf, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'kf' == chosenShort and not isCancelled:
          distance = ctGetDistance('KF', completedLegs)
          shortFill = kfRelOrder('SELL', kf, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'db' == chosenLong and not isCancelled:
          distance = ctGetDistance('DB', completedLegs)
          longFill = dbRelOrder('BUY', db, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'db' == chosenShort and not isCancelled:
          distance = ctGetDistance('DB', completedLegs)
          shortFill = dbRelOrder('SELL', db, ccy, trade_notional, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'spot' == chosenLong and not isCancelled:
          distance = ctGetDistance('SPOT', completedLegs)
          longFill = ftxRelOrder('BUY', ftx, ccy + '/USD', trade_qty, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'spot' == chosenShort and not isCancelled:
          distance = ctGetDistance('SPOT', completedLegs)
          shortFill = ftxRelOrder('SELL', ftx, ccy + '/USD', trade_qty, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'ftx' == chosenLong and not isCancelled:
          distance = ctGetDistance('FTX', completedLegs)
          longFill = ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_qty, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'ftx' == chosenShort and not isCancelled:
          distance = ctGetDistance('FTX', completedLegs)
          shortFill = ftxRelOrder('SELL', ftx, ccy + '-PERP', trade_qty, maxChases=ctGetMaxChases(completedLegs),distance=distance)
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if 'kut' == chosenLong and not isCancelled:
          distance = ctGetDistance('KUT', completedLegs)
          longFill = kutRelOrder('BUY', kutCurrent, ccy, trade_qty, maxChases=ctGetMaxChases(completedLegs), distance=distance) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs, isCancelled = ctProcessFill(longFill, completedLegs, isCancelled)
        if 'kut' == chosenShort and not isCancelled:
          distance = ctGetDistance('KUT', completedLegs)
          shortFill = kutRelOrder('SELL', kutCurrent, ccy, trade_qty, maxChases=ctGetMaxChases(completedLegs), distance=distance) * ftxGetMid(ftx, 'USDT/USD')
          completedLegs, isCancelled = ctProcessFill(shortFill, completedLegs, isCancelled)
        if isCancelled:
          status=(min(abs(status),CT_CONFIGS_DICT['STREAK'])-1)*np.sign(status)
          print()
          speak('Cancelled')
          continue # to next iteration in While True loop
        else:
          realizedSlippageBps = ctPrintTradeStats(longFill, shortFill, basisBps, realizedSlippageBps)
          print(timeTag('Done'))
          print()
          speak('Done')
          break # Go to next program
  print(timeTag(termcolor.colored('Avg realized slippage = ' + str(round(np.mean(realizedSlippageBps))) + 'bps', 'red')))
  print(timeTag('All done'))
  speak('All done')

#############################################################################################

#####
# Etc
#####
# Add unique item to list
def appendUnique(myList,item):
  if item not in myList:
    myList.append(item)

# Assert side for RelOrder functions
def assertSide(side):
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)

# Cache items in memory
def cache(mode,key,value=None):
  if not hasattr(cache, 'cacheDict'):
    cache.cacheDict=dict()
  if mode=='w':
    cache.cacheDict[key]=value
  elif mode=='r':
    try:
      return cache.cacheDict[key]
    except:
      return None

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

# Format number as percentage (string)
def fmtPct(n, ndigits=1):
  return str(round(n * 100, ndigits))+'%'

# Get max abs position USD (bb/db/kf only)
def getMaxAbsPosUSD(exch, ccy, spotDeltaUSDAdj=0, posMult=3, negMult=6):
  if exch=='bb':
    bb = bbCCXTInit()
    spot = bbGetMid(bb,ccy)
    spotPos = bbGetSpotPos(bb,ccy)
    futPos = bbGetFutPos(bb,ccy)
  elif exch=='db':
    db = dbCCXTInit()
    spot = dbGetMid(db, ccy)
    spotPos = dbGetSpotPos(db, ccy)
    futPos = dbGetFutPos(db, ccy)
  elif exch=='kf':
    kf = kfApophisInit()
    spot = kfGetMid(kf, ccy)
    spotPos = kfGetSpotPos(kf,ccy,isIncludeHoldingWallets=False)
    futPos = kfGetFutPos(kf,ccy)
  else:
    sys.exit(1)
  notional=(spot*spotPos)+spotDeltaUSDAdj
  if np.sign(futPos)>=0:
    notional*=posMult
  else:
    notional*=negMult
  return notional

# Get current time
def getCurrentTime(isCondensed=False,offsetH=0):
  t=datetime.datetime.today()
  if offsetH!=0:
    t=t+datetime.timedelta(hours=offsetH)
  if isCondensed:
    return t.strftime('%H:%M:%S')
  else:
    return t.strftime('%Y-%m-%d %H:%M:%S')

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
def getPctElapsed(hoursInterval,isKU=False):
  utcNow = datetime.datetime.utcnow()
  n = (utcNow.hour * 3600 + utcNow.minute * 60 + utcNow.second) % (hoursInterval * 3600) / (hoursInterval * 3600)
  if isKU:
    return (n + 0.5) % 1
  else:
    return n

# Get valid currencies for a futures exchange
def getValidCcys(futExch):
  myL = []
  for ccy in SHARED_CCY_DICT.keys():
    if futExch in SHARED_CCY_DICT[ccy]['futExch']:
      myL.append(ccy)
  return myL

# Get valid exchanges for a currency
def getValidExchs(ccy):
  myL=[]
  for futExch in SHARED_CCY_DICT[ccy]['futExch']:
    if SHARED_EXCH_DICT[futExch]>=1:
      myL.append(futExch)
  return myL

# Get yesterday's timestamp
def getYest():
  return int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))))

# Trigger parallel run for objects
def parallelRun(objs):
  Parallel(n_jobs=len(objs), backend='threading')(delayed(obj.run)() for obj in objs)

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

# Print list in wrapped format
def printListWrapped(items, n):
  items = list(items)
  lines = []
  for i in range(0, len(items), n):
    chunk = items[i:i + n]
    line = ', '.join(map(repr, chunk))
    lines.append(line)
  print('[{}]'.format(',\n '.join(lines)))

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

# Safer del function
def safeDel(d, key):
  if key in d.keys(): del d[key]

# Trigger serial run for objects
def serialRun(objs):
  for obj in objs: obj.run()

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

# Tag message with time
def timeTag(msg):
  return getCurrentTime()+': '+msg