import SimonLib as sl
import pandas as pd
import ccxt
import numpy as np
import time

########
# Params
########
TRADE_BTC_NOTIONAL = 10000
TRADE_ETH_NOTIONAL = 5000
TRADE_FTT_NOTIONAL = 2000

########
# Limits
########
MAX_NOTIONAL = 50000
MAX_BTC = 0.5
MAX_ETH = 10
MAX_FTT = 100

###########
# Functions
###########
def ftxRelOrder(side,ftx,ticker,trade_coin):
  def ftxGetBid(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['bid']
  def ftxGetAsk(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['ask']
  if side != 'BUY' and side != 'SELL':
    sl.stop()
  print(sl.getCurrentTime()+': Sending FTX '+side+' order of '+ticker+' (qty='+str(round(trade_coin,6))+') ....')
  if side=='BUY':
    limitPrice = ftxGetBid(ftx, ticker)
    orderId = ftx.create_limit_buy_order(ticker, trade_coin, limitPrice)['info']['id']
  else:
    limitPrice = ftxGetAsk(ftx, ticker)
    orderId = ftx.create_limit_sell_order(ticker, trade_coin, limitPrice)['info']['id']
  while True:
    if ftx.private_get_orders_order_id({'order_id': orderId})['result']['remainingSize'] == 0:
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

def bnMarketOrder(side,bn,ccy,trade_usd):
  if side != 'BUY' and side != 'SELL':
    sl.stop()
  ticker=ccy+'USD_PERP'
  print(sl.getCurrentTime() + ': Sending BN ' + side + ' order of ' + ticker + ' (notional=$'+ str(round(trade_usd))+') ....')
  if ccy=='BTC':
    qty=int(trade_usd/100)
  elif ccy=='ETH':
    qty=int(trade_usd/10)
  else:
    sl.stop()
  bn.dapiPrivate_post_order({'symbol': ticker, 'side': side, 'type': 'MARKET', 'quantity': qty})

def bbRelOrder(side,bb,ccy,trade_usd):
  def bbGetBid(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['bid_price'])
  def bbGetAsk(bb,ticker):
    return float(bb.fetch_ticker(ticker)['info']['ask_price'])
  if side != 'BUY' and side != 'SELL':
    sl.stop()
  ticker1=ccy+'/USD'
  ticker2=ccy+'USD'
  print(sl.getCurrentTime() + ': Sending BB ' + side + ' order of ' + ticker1 + ' (notional=$'+ str(round(trade_usd))+') ....')
  if side=='BUY':
    limitPrice = bbGetBid(bb, ticker1)
    orderId = bb.create_limit_buy_order(ticker1, trade_usd, limitPrice)['info']['order_id']
  else:
    limitPrice = bbGetAsk(bb, ticker1)
    orderId = bb.create_limit_sell_order(ticker1, trade_usd, limitPrice)['info']['order_id']
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
        bb.v2_private_post_order_replace({'symbol':ticker2,'order_id':orderId, 'p_r_price': limitPrice})
    time.sleep(1)

######
# Init
######
API_KEY_FTX = sl.jLoad('API_KEY_FTX')
API_SECRET_FTX = sl.jLoad('API_SECRET_FTX')
API_KEY_BINANCE = sl.jLoad('API_KEY_BINANCE')
API_SECRET_BINANCE = sl.jLoad('API_SECRET_BINANCE')
API_KEY_BYBIT = sl.jLoad('API_KEY_BYBIT')
API_SECRET_BYBIT = sl.jLoad('API_SECRET_BYBIT')
API_KEY_CB = sl.jLoad('API_KEY_CB')
API_SECRET_CB = sl.jLoad('API_SECRET_CB')
ftx=ccxt.ftx({'apiKey': API_KEY_FTX, 'secret': API_SECRET_FTX, 'enableRateLimit': True})
bn = ccxt.binance({'apiKey': API_KEY_BINANCE, 'secret': API_SECRET_BINANCE, 'enableRateLimit': True})
bb = ccxt.bybit({'apiKey': API_KEY_BYBIT, 'secret': API_SECRET_BYBIT, 'enableRateLimit': True})
cb=ccxt.coinbase({'apiKey': API_KEY_CB, 'secret': API_SECRET_CB, 'enableRateLimit': True})
ftxWallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main'])
ftxWallet['Ccy']=ftxWallet['coin']
ftxWallet['SpotDelta']=ftxWallet['total']
ftxWallet=ftxWallet.set_index('Ccy').loc[['BTC','ETH','FTT','USD']]
spotBTC = ftxWallet.loc['BTC', 'usdValue'] / ftxWallet.loc['BTC', 'total']
spotETH = ftxWallet.loc['ETH', 'usdValue'] / ftxWallet.loc['ETH', 'total']
spotFTT = ftxWallet.loc['FTT', 'usdValue'] / ftxWallet.loc['FTT', 'total']
trade_btc = np.min([np.min([TRADE_BTC_NOTIONAL,MAX_NOTIONAL])/spotBTC,MAX_BTC])
trade_eth = np.min([np.min([TRADE_ETH_NOTIONAL,MAX_NOTIONAL])/spotETH,MAX_ETH])
trade_ftt = np.min([np.min([TRADE_FTT_NOTIONAL,MAX_NOTIONAL])/spotFTT,MAX_FTT])
trade_btc_notional = trade_btc*spotBTC
trade_eth_notional = trade_eth*spotETH
trade_ftt_notional = trade_ftt*spotFTT

sl.printHeader('CryptoTrader')
print('Target BTC: '+str(round(trade_btc,6))+' ($'+str(round(trade_btc_notional))+')')
print('Target ETH: '+str(round(trade_eth,6))+' ($'+str(round(trade_eth_notional))+')')
print('Target FTT: '+str(round(trade_ftt,6))+' ($'+str(round(trade_ftt_notional))+')')

######
# Main
######
if False:
  ##########################
  ccy = 'FTT'  # <----------
  ##########################
  if ccy=='BTC':
    trade_coin=trade_btc
    trade_usd=trade_btc_notional
  elif ccy=='ETH':
    trade_coin=trade_eth
    trade_usd = trade_eth_notional
  elif ccy=='FTT':
    trade_coin=trade_ftt
    trade_usd = trade_ftt_notional
  else:
    sl.stop()

  #ftxRelOrder('BUY', ftx, ccy+'/USD', trade_coin) # FTX Spot Buy (Maker)
  ftxRelOrder('SELL', ftx, ccy+'/USD', trade_coin) # FTX Spot Sell (Maker)

  ftxRelOrder('BUY', ftx, ccy + '-PERP', trade_coin)  # FTX Fut Buy (Maker)
  #ftxRelOrder('SELL', ftx, ccy+'-PERP', trade_coin) # FTX Fut Sell (Maker)

  # bnMarketOrder('BUY', bn, ccy, trade_usd) # Binance Fut Buy (Taker)
  #bnMarketOrder('SELL', bn, ccy, trade_usd)  # Binance Fut Sell (Taker)

  #bbRelOrder('BUY', bb, ccy, trade_usd) # Bybit Fut Buy (Maker)
  #bbRelOrder('SELL', bb, ccy, trade_usd) # Bybit Fut Sell (Maker)

  print(sl.getCurrentTime()+': Done')