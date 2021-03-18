import SimonLib as sl
import pandas as pd
import ccxt
import numpy as np
import time

########
# Params
########
TRADE_USD = 2000 # <----------

########
# Limits
########
MAX_USD = 10000
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
  print(sl.getCurrentTime()+': Sending FTX '+side+' order for '+ticker+' ....')
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
  print(sl.getCurrentTime() + ': Sending BN ' + side + ' order for ' + ticker + ' ....')
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
  print(sl.getCurrentTime() + ': Sending BB ' + side + ' order for ' + ticker1 + ' ....')
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
trade_usd = np.clip(TRADE_USD,-MAX_USD,MAX_USD)
trade_btc = np.clip(TRADE_USD/spotBTC,-MAX_BTC,MAX_BTC)
trade_eth = np.clip(TRADE_USD/spotETH,-MAX_ETH,MAX_ETH)
trade_ftt = np.clip(TRADE_USD/spotFTT,-MAX_FTT,MAX_FTT)
sl.printHeader('CruptoTrader')
print('Trade $:'.rjust(12),round(trade_usd))
print('Trade BTC:'.rjust(12),round(trade_btc,6))
print('Trade ETH:'.rjust(12),round(trade_eth,6))
print('Trade FTT:'.rjust(12),round(trade_ftt,6))

######
# Main
######
if False:
  ##########################
  ccy = 'FTT'  # <----------
  ##########################
  if ccy=='BTC':
    trade_coin=trade_btc
  elif ccy=='ETH':
    trade_coin=trade_eth
  elif ccy=='FTT':
    trade_coin=trade_ftt
  else:
    sl.stop()

  #######
  # Maker
  #######
  ftxRelOrder('BUY', ftx, ccy+'/USD', trade_coin) # FTX Spot Buy (Maker)
  #ftxRelOrder('SELL', ftx, ccy+'/USD, trade_coin) # FTX Spot Sell (Maker)

  #ftxRelOrder('BUY', ftx, ccy + '/USD', trade_coin)  # FTX Fut Buy (Maker)
  ftxRelOrder('SELL', ftx, ccy+'-PERP', trade_coin) # FTX Fut Sell (Maker)

  #bbRelOrder('BUY', bb, ccy, trade_usd) # BB Fut Buy (Maker)
  #bbRelOrder('SELL', bb, ccy, trade_usd) # BB Fut Sell (Maker)

  #######
  # Taker
  #######
  #bnMarketOrder('BUY', bn, ccy, trade_usd) # BN Fut Buy (Taker)
  #bnMarketOrder('SELL', bn, ccy, trade_usd) # BN Fut Sell (Taker)

  #ftx.create_market_buy_order(ccy+'/USD', trade_coin) # FTX Spot Buy (Taker)
  #ftx.create_market_sell_order(ccy+'/USD', trade_coin) # FTX Spot Sell (Taker)

  #ftx.create_market_buy_order(ccy+'-PERP', trade_coin) # FTX Fut Buy (Taker)
  #ftx.create_market_sell_order(ccy+'-PERP', trade_coin) # FTX Fut Sell (Taker)

  ######
  # Done
  ######
  print(sl.getCurrentTime()+': Done')