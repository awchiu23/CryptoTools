import CryptoLib as cl
from CryptoParams import *
import pandas as pd
import sys
import time
from retrying import retry

########
# Params
########
nPrograms=1
notional=5000                # USD notional
qtyOverRide=None             # Use in place of notional unless None

ccy='AXS'
side='BUY'                   # 'BUY', 'SELL'
hedgeExchange='ftxperp'      # 'ftxspot', 'ftxperp', 'bbt', 'bnt', 'none'

CT_CONFIGS_DICT['BNS_MAX_WAIT_TIME'] = 10

###########
# Functions
###########
@retry(wait_fixed=1000)
def bnsGetBid(bn, ccy):
  return float(bn.publicGetTickerBookTicker({'symbol': ccy+'USDT'})['bidPrice'])

@retry(wait_fixed=1000)
def bnsGetAsk(bn, ccy):
  return float(bn.publicGetTickerBookTicker({'symbol': ccy+'USDT'})['askPrice'])

@retry(wait_fixed=1000)
def bnsGetTickSize(bn,ccy):
  key='bnsTickSize'
  df=cl.cache('r',key)
  if df is None:
    df=pd.DataFrame(bn.public_get_exchangeinfo()['symbols']).set_index('symbol')
    cl.cache('w',key,df)
  return float(df.loc[ccy+'USDT','filters'][0]['tickSize'])

@retry(wait_fixed=1000)
def bnsGetLotSize(bn,ccy):
  key='bnsLotSize'
  df=cl.cache('r',key)
  if df is None:
    df=pd.DataFrame(bn.public_get_exchangeinfo()['symbols']).set_index('symbol')
    cl.cache('w',key,df)
  return float(df.loc[ccy+'USDT','filters'][2]['stepSize'])

def bnsRoundPrice(api, exch, ccyOrTicker, price, side=None, distance=None):
  tickSize = bnsGetTickSize(api, ccyOrTicker)
  adjPrice = round(price / tickSize) * tickSize
  if not side is None:
    if side == 'BUY':
      adjPrice += tickSize * distance
    elif side == 'SELL':
      adjPrice -= tickSize * distance
    else:
      sys.exit(1)
  return round(adjPrice,6)

def bnsRoundQty(api, ccyOrTicker, qty):
  lotSize = bnsGetLotSize(api, ccyOrTicker)
  return round(round(qty / lotSize) * lotSize, 6)

def bnsRelOrder(side, bn, ccy, trade_qty, maxChases=0,distance=0):
  @retry(wait_fixed=1000)
  def bnsGetOrder(bn, ticker, orderId):
    return bn.private_get_order({'symbol': ticker, 'orderId': orderId})
  # Do not use @retry
  def bnsPlaceOrder(bn, ticker, side, qty, limitPrice):
    return bn.private_post_order({'symbol': ticker, 'side': side, 'type': 'LIMIT', 'quantity': qty, 'price': limitPrice, 'timeInForce': 'GTC'})['orderId']
  # Do not use @retry
  def bnsCancelOrder(bn, ticker, orderId):
    try:
      orderStatus=bn.private_delete_order({'symbol': ticker, 'orderId': orderId})
      if orderStatus['status']!='CANCELED':
        print('Order cancellation failed!')
        sys.exit(1)
      return orderStatus,float(orderStatus['origQty'])-float(orderStatus['executedQty'])
    except:
      orderStatus=bnsGetOrder(bn, ticker, orderId)
      return orderStatus,0
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  ticker=ccy+'USDT'
  qty = bnsRoundQty(bn,ccy,trade_qty)
  print(cl.getCurrentTime()+': Sending BNS '+side+' order of '+ticker+' (qty='+str(qty)+') ....')
  if side == 'BUY':
    refPrice = bnsGetBid(bn, ccy)
  else:
    refPrice = bnsGetAsk(bn, ccy)
  limitPrice = bnsRoundPrice(bn,'bns',ccy,refPrice,side=side,distance=distance)
  orderId=bnsPlaceOrder(bn, ticker, side, qty, limitPrice)
  print(cl.getCurrentTime() + ': [DEBUG: orderId=' + orderId + '; price=' + str(limitPrice) + '] ')
  refTime = time.time()
  nChases=0
  while True:
    orderStatus = bnsGetOrder(bn, ticker, orderId)
    if orderStatus['status']=='FILLED': break
    if side=='BUY':
      newRefPrice=bnsGetBid(bn,ccy)
    else:
      newRefPrice=bnsGetAsk(bn,ccy)
    if (side == 'BUY' and newRefPrice > refPrice) or (side == 'SELL' and newRefPrice < refPrice) or ((time.time() - refTime) > CT_CONFIGS_DICT['BNS_MAX_WAIT_TIME']):
      refPrice=newRefPrice
      nChases+=1
      orderStatus = bnsGetOrder(bn, ticker, orderId)
      if orderStatus['status'] == 'FILLED': break
      if nChases > maxChases and float(orderStatus['executedQty']) == 0:
        orderStatus, leavesQty = bnsCancelOrder(bn, ticker, orderId)
        if leavesQty == 0: break
        print(cl.getCurrentTime() + ': Cancelled')
        return 0
      else:
        refTime = time.time()
        newLimitPrice = bnsRoundPrice(bn, 'bns', ccy, refPrice, side=side, distance=distance)
        if (side == 'BUY' and newLimitPrice > limitPrice) or (side == 'SELL' and newLimitPrice < limitPrice):
          print(cl.getCurrentTime() + ': [DEBUG: replace order; nChases=' + str(nChases) + '; price=' + str(limitPrice) + '->' + str(newLimitPrice) + ']')
          limitPrice = newLimitPrice
          orderStatus, leavesQty = bnsCancelOrder(bn, ticker, orderId)
          if leavesQty == 0: break
          orderId = bnsPlaceOrder(bn, ticker, side, bnsRoundQty(bn, ccy, leavesQty), limitPrice)
        else:
          print(cl.getCurrentTime() + ': [DEBUG: leave order alone; nChases=' + str(nChases) + '; price=' + str(limitPrice) + ']')
    time.sleep(1)
  orderStatus = bnsGetOrder(bn, ticker, orderId)
  fill=float(orderStatus['price'])
  print(cl.getCurrentTime() + ': Filled at ' + str(round(fill, 6)))
  return fill

######
# Init
######
ftx,bb,bn,db,kf,qty,notional,spot = cl.ctInit(ccy,notional,0)
if qtyOverRide is not None:
  qty = qtyOverRide
  notional = qty * spot
if side == 'BUY':
  oppSide = 'SELL'
elif side == 'SELL':
  oppSide = 'BUY'
else:
  sys.exit(1)

######
# Main
######
cl.printHeader('BNSTrader')
bn = cl.bnCCXTInit()
for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  if hedgeExchange == 'ftxspot':
    cl.ftxRelOrder(oppSide, ftx, ccy + '/USD', qty, maxChases=888)
  elif hedgeExchange=='ftxperp':
    cl.ftxRelOrder(oppSide, ftx, ccy + '-PERP', qty, maxChases=888)
  elif hedgeExchange=='bbt':
    cl.bbtRelOrder(oppSide, bb, ccy, qty, maxChases=888)
  elif hedgeExchange=='bnt':
    cl.bntRelOrder(oppSide, bn, ccy, qty, maxChases=888)
  elif hedgeExchange!='none':
    print('Bad exchange!')
    sys.exit(1)
  bnsRelOrder(side, bn, ccy, qty, maxChases=888)
  time.sleep(2)
cl.speak('BNSTrader has completed')