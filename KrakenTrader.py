import CryptoLib as cl
import numpy as np
import sys
import time
from retrying import retry

########
# Params
########
nPrograms=1
targetUSD=5000

account=1                # which Kraken account to use
side='SELL'              # 'BUY', 'SELL'
pair='XXBTZEUR'          # 'XXBTZUSD', 'XXBTZEUR'
hedgeExchange='bb'       # 'ftxspot', 'ftxperp', 'bb', 'bn', 'kf', 'none'

###########
# Functions
###########
def krRelOrder(side,kr,pair,trade_qty,maxChases=0):
  @retry(wait_fixed=1000)
  def krGetBid(kr, pair):
    return float(kr.public_get_ticker({'pair': pair})['result'][pair]['b'][0])
  @retry(wait_fixed=1000)
  def krGetAsk(kr, pair):
    return float(kr.public_get_ticker({'pair': pair})['result'][pair]['a'][0])
  # Do not use @retry!
  def krPlaceOrder(kr, pair, side, qty, limitPrice):
    return kr.private_post_addorder({'pair': pair, 'type': side.lower(), 'ordertype': 'limit', 'price': limitPrice, 'volume': qty, 'leverage': 5})['result']['txid'][0]
  # Do not use @retry!
  def krCancelOrder(kr, orderId):
    try:
      kr.private_post_cancelorder({'txid': orderId})
    except:
      pass
  @retry(wait_fixed=1000)
  def krGetOrderStatus(kr, orderId):
    return kr.private_post_queryorders({'txid': orderId})['result'][orderId]
  #####
  if side != 'BUY' and side != 'SELL':
    sys.exit(1)
  qty = round(trade_qty, 3)
  print(cl.getCurrentTime()+': Sending KR '+side+' order of '+pair+' (qty='+str(round(qty,6))+') ....')
  if side == 'BUY':
    limitPrice = krGetBid(kr, pair)
    z='Bidding'
  else:
    limitPrice = krGetAsk(kr, pair)
    z='Offering'
  print(cl.getCurrentTime() + ': ' + z + ' at ' + str(limitPrice) + ' (qty='+str(round(qty,6))+') ',end='')
  orderId=krPlaceOrder(kr, pair, side, qty, limitPrice)
  nChases=0
  while True:
    orderStatus=krGetOrderStatus(kr,orderId)
    if orderStatus['status'] == 'closed':
      break
    if side=='BUY':
      newPrice=krGetBid(kr,pair)
    else:
      newPrice=krGetAsk(kr,pair)
    if newPrice != limitPrice or orderStatus['status'] == 'canceled':
      limitPrice=newPrice
      nChases+=1
      krCancelOrder(kr, orderId)
      orderStatus = krGetOrderStatus(kr, orderId)
      leavesQty=float(orderStatus['vol'])-float(orderStatus['vol_exec'])
      if nChases>maxChases and leavesQty==qty:
        print(cl.getCurrentTime() + ': Cancelled')
        return 0
      elif leavesQty==0:
        break
      else:
        if side == 'BUY':
          print()
          z = 'Bidding' if side=='BUY' else 'Offering'
          print(cl.getCurrentTime() + ': '+z+' at ' + str(limitPrice) + ' (qty='+str(round(leavesQty,6))+') ',end='')
        orderId=krPlaceOrder(kr, pair, side, leavesQty, limitPrice)
    else:
      print('.',end='')
    time.sleep(3)
  print()
  orderStatus=krGetOrderStatus(kr,orderId)
  fill=float(orderStatus['price'])
  print(cl.getCurrentTime() + ': Filled at '+str(round(fill,6)))
  return fill

######
# Init
######
ftx = cl.ftxCCXTInit()
ftxWallet=cl.ftxGetWallet(ftx)
spotBTC=ftxWallet.loc['BTC','spot']
trade_btc = np.min([np.min([targetUSD, cl.CT_MAX_NOTIONAL]) / spotBTC, cl.CT_MAX_BTC])
trade_btc_notional = trade_btc * spotBTC
kr = cl.krCCXTInit(account)

if side == 'BUY':
  oppSide = 'SELL'
elif side == 'SELL':
  oppSide = 'BUY'
else:
  sys.exit(1)

######
# Main
######
cl.printHeader('KrakenTrader')

for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  fill=krRelOrder(side,kr,pair,trade_btc,maxChases=888)
  if hedgeExchange=='ftxspot':
    fill=cl.ftxRelOrder(oppSide,ftx,'BTC/USD',trade_btc,maxChases=888)
  if hedgeExchange=='ftxperp':
    fill=cl.ftxRelOrder(oppSide,ftx,'BTC-PERP',trade_btc,maxChases=888)
  elif hedgeExchange=='bb':
    bb = cl.bbCCXTInit()
    fill=cl.bbRelOrder(oppSide, bb, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='bn':
    bn = cl.bnCCXTInit()
    fill=cl.bnRelOrder(oppSide, bn, 'BTC', trade_btc_notional, maxChases=888)
  elif hedgeExchange=='kf':
    kf = cl.kfInit()
    fill=cl.kfRelOrder(oppSide, kf, 'BTC', trade_btc_notional, maxChases=888)
  time.sleep(3)

cl.speak('KrakenTrader has completed')