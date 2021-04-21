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

account=2                # which Kraken account to use
side='SELL'              # 'BUY', 'SELL'
pair='XXBTZEUR'          # 'XXBTZUSD','XXBTZEUR'
hedgeExchange='bb'     # 'ftxspot', 'ftxperp', 'bb', 'bn', 'kf', 'none'
isMargin=True            # Margin trading?

###########
# Functions
###########
def krRelOrder(side,kr,pair,trade_qty,lev,maxChases=0):
  @retry(wait_fixed=1000)
  def krGetBid(kr, pair):
    return float(kr.public_get_ticker({'pair': pair})['result'][pair]['b'][0])
  @retry(wait_fixed=1000)
  def krGetAsk(kr, pair):
    return float(kr.public_get_ticker({'pair': pair})['result'][pair]['a'][0])
  # Do not use @retry!
  def krPlaceOrder(kr, pair, side, qty, limitPrice, lev):
    if lev==1:
      return kr.private_post_addorder({'pair': pair, 'type': side.lower(), 'ordertype': 'limit', 'price': limitPrice, 'volume': qty})['result']['txid'][0]
    else:
      return kr.private_post_addorder({'pair': pair, 'type': side.lower(), 'ordertype': 'limit', 'price': limitPrice, 'volume': qty, 'leverage': lev})['result']['txid'][0]
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
  orderId=krPlaceOrder(kr, pair, side, qty, limitPrice, lev)
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
        orderId=krPlaceOrder(kr, pair, side, leavesQty, limitPrice, lev)
    else:
      print('.',end='')
    time.sleep(3)
  print()
  orderStatus=krGetOrderStatus(kr,orderId)
  fill=float(orderStatus['price'])
  print(cl.getCurrentTime() + ': Filled at '+str(round(fill,6)))
  return fill

def krExec(side,kr,pair,qty,isMargin):
  lev=5 if isMargin else 1
  fill = krRelOrder(side, kr, pair, qty, lev, maxChases=888)
  if pair == 'XXBTZEUR':
    spotEUR = cl.ftxGetSpotEUR(ftx)
    print(cl.getCurrentTime() + ': Filled at ' + str(round(fill * spotEUR)) + ' in USD; f/x=' + str(round(spotEUR, 4)))

def getBal(bal, ccy):
  try:
    return float(bal[ccy])
  except:
    return 0

######
# Init
######
ftx = cl.ftxCCXTInit()
ftxWallet=cl.ftxGetWallet(ftx)
spotBTC=ftxWallet.loc['BTC','spot']
spotETH=ftxWallet.loc['ETH','spot']
trade_btc = np.min([np.min([targetUSD, cl.CT_MAX_NOTIONAL]) / spotBTC, cl.CT_MAX_BTC])
trade_eth = np.min([np.min([targetUSD, cl.CT_MAX_NOTIONAL]) / spotETH, cl.CT_MAX_ETH])
trade_btc_notional = trade_btc * spotBTC
trade_eth_notional = trade_eth * spotETH
if pair in ['XXBTZUSD', 'XXBTZEUR']:
  ccy='BTC'
  trade_qty=trade_btc
  trade_notional=trade_btc_notional
elif pair in ['XETHZUSD','XETHZEUR']:
  ccy='ETH'
  trade_qty=trade_eth
  trade_notional=trade_eth_notional
else:
  sys.exit(1)
#####
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
kr = cl.krCCXTInit(account)
for n in range(nPrograms):
  cl.printHeader('Program '+str(n+1))
  if hedgeExchange=='ftxspot':
    krExec(side, kr, pair, trade_qty, isMargin)
    fill=cl.ftxRelOrder(oppSide, ftx,ccy+'/USD', trade_qty, maxChases=888)
  elif hedgeExchange=='ftxperp':
    krExec(side, kr, pair, trade_qty, isMargin)
    fill=cl.ftxRelOrder(oppSide, ftx,ccy+'-PERP', trade_qty, maxChases=888)
  elif hedgeExchange=='bb':
    bb = cl.bbCCXTInit()
    fill=cl.bbRelOrder(oppSide, bb, ccy, trade_notional, maxChases=888)
    krExec(side, kr, pair, trade_qty, isMargin)
  elif hedgeExchange=='bn':
    krExec(side, kr, pair, trade_qty, isMargin)
    bn = cl.bnCCXTInit()
    fill=cl.bnRelOrder(oppSide, bn, ccy, trade_notional, maxChases=888)
  elif hedgeExchange=='kf':
    krExec(side, kr, pair, trade_qty, isMargin)
    kf = cl.kfInit()
    fill=cl.kfRelOrder(oppSide, kf, ccy, trade_notional, maxChases=888)
  elif hedgeExchange=='none':
    krExec(side, kr, pair, trade_qty, isMargin)
  else:
    print('Bad exchange!')
    sys.exit(1)
  time.sleep(3)

bal = kr.private_post_balance()['result']
spotDeltaUSD = getBal(bal, 'ZUSD')
spotDeltaEUR = getBal(bal, 'ZEUR')
print(cl.getCurrentTime()+': Cash balances post trade: $'+str(round(spotDeltaUSD))+' / €'+str(round(spotDeltaEUR)))
cl.speak('KrakenTrader has completed')