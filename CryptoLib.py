################
# Crypto Library
################
import pandas as pd
import numpy as np
import datetime
import termcolor
import winsound
import sys
import time
import ccxt

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
CT_CONFIGS_DICT['FTX_FTT_SELL']=['ftx','FTT',True,CT_DEFAULT_SELL_TGT_BPS+5]

CT_CONFIGS_DICT['FTX_BTC_BUY']=['ftx','BTC',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BN_BTC_BUY']=['bn','BTC',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BB_BTC_BUY']=['bb','BTC',False,CT_DEFAULT_BUY_TGT_BPS-10]
CT_CONFIGS_DICT['FTX_ETH_BUY']=['ftx','ETH',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BN_ETH_BUY']=['bn','ETH',False,CT_DEFAULT_BUY_TGT_BPS]
CT_CONFIGS_DICT['BB_ETH_BUY']=['bb','ETH',False,CT_DEFAULT_BUY_TGT_BPS-10]
CT_CONFIGS_DICT['FTX_FTT_BUY']=['ftx','FTT',False,CT_DEFAULT_BUY_TGT_BPS-5]

CT_NOBS = 3          # Number of observations through target before triggering
CT_NPROGRAMS = 10    # Number of programs (each program being a pair of trades)

CT_TRADE_BTC_NOTIONAL = 10000  # Per trade notional
CT_TRADE_ETH_NOTIONAL = 3000   # Per trade notional
CT_TRADE_FTT_NOTIONAL = 1000   # Per trade notional

CT_MAX_NOTIONAL = 50000        # Hard limit
CT_MAX_BTC = 0.5               # Hard limit
CT_MAX_ETH = 10                # Hard limit
CT_MAX_FTT = 100               # Hard limit

#############################################################################################

def ftxGetMid(ftxMarkets, name):
  df = ftxMarkets[ftxMarkets['name'] == name]
  return float((df['bid'] + df['ask']) / 2)

def ftxGetEstFunding(ftx, ccy):
  while True:
    try:
      ef = ftx.public_get_futures_future_name_stats({'future_name': ccy+'-PERP'})['result']['nextFundingRate'] * 24 * 365
    except:
      continue
    else:
      break
  return ef

def ftxGetEstBorrow(ftx):
  while True:
    try:
      eb = pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365
    except:
      continue
    else:
      break
  return eb

def ftxRelOrder(side,ftx,ticker,trade_qty):
  def ftxGetBid(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['bid']
  def ftxGetAsk(ftx,ticker):
    return ftx.publicGetMarketsMarketName({'market_name':ticker})['result']['ask']
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

def bnGetFut(bn,ccy):
  while True:
    try:
      bnBookTicker = bn.dapiPublicGetTickerBookTicker({'symbol': ccy + 'USD_PERP'})[0]
    except:
      continue
    else:
      break
  return (float(bnBookTicker['bidPrice']) + float(bnBookTicker['askPrice'])) / 2

def bnGetEstFunding(bn, ccy):
  while True:
    try:
      ef = float(pd.DataFrame(bn.dapiPublic_get_premiumindex({'symbol': ccy+'USD_PERP'}))['lastFundingRate']) * 3 * 365
    except:
      continue
    else:
      break
  return ef

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

def bbGetFut(bb,ccy):
  while True:
    try:
      bbTickers=bb.v2PublicGetTickers({'symbol':ccy+'USD'})['result'][0]
    except:
      continue
    else:
      break
  return (float(bbTickers['bid_price'])+float(bbTickers['ask_price']))/2

def bbGetEstFunding1(bb,ccy):
  while True:
    try:
      ef = float(bb.v2PrivateGetFundingPrevFundingRate({'symbol': ccy+'USD'})['result']['funding_rate']) * 3 * 365
    except:
      continue
    else:
      break
  return ef

def bbGetEstFunding2(bb, ccy):
  while True:
    try:
      ef2 = bb.v2PrivateGetFundingPredictedFunding({'symbol': ccy+'USD'})['result']['predicted_funding_rate'] * 3 * 365
    except:
      continue
    else:
      break
  return ef2

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
# Multi-exchange
################
def getPremDict(ftx,bn,bb):
  d=dict()
  ftxMarkets = pd.DataFrame(ftx.public_get_markets()['result'])
  spotBTC = ftxGetMid(ftxMarkets, 'BTC/USD')
  spotETH = ftxGetMid(ftxMarkets, 'ETH/USD')
  spotFTT = ftxGetMid(ftxMarkets, 'FTT/USD')
  ftxFutBTC = ftxGetMid(ftxMarkets, 'BTC-PERP')
  ftxFutETH = ftxGetMid(ftxMarkets, 'ETH-PERP')
  ftxFutFTT = ftxGetMid(ftxMarkets, 'FTT-PERP')
  d['ftxBTCPrem']=ftxFutBTC / spotBTC - 1
  d['ftxETHPrem']=ftxFutETH / spotETH - 1
  d['ftxFTTPrem']=ftxFutFTT / spotFTT - 1

  bnFutBTC = bnGetFut(bn, 'BTC')
  bnFutETH = bnGetFut(bn, 'ETH')
  d['bnBTCPrem'] = bnFutBTC / spotBTC - 1
  d['bnETHPrem'] = bnFutETH / spotETH - 1

  bbFutBTC = bbGetFut(bb, 'BTC')
  bbFutETH = bbGetFut(bb, 'ETH')
  d['bbBTCPrem'] = bbFutBTC / spotBTC - 1
  d['bbETHPrem'] = bbFutETH / spotETH - 1

  return d

#############################################################################################

######################
# CryptoTrader helpers
######################
def cryptoTraderInit(config):
  ftx=ccxt.ftx({'apiKey': API_KEY_FTX, 'secret': API_SECRET_FTX, 'enableRateLimit': True})
  bn = ccxt.binance({'apiKey': API_KEY_BINANCE, 'secret': API_SECRET_BINANCE, 'enableRateLimit': True})
  bb = ccxt.bybit({'apiKey': API_KEY_BYBIT, 'secret': API_SECRET_BYBIT, 'enableRateLimit': True})
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
        winsound.Beep(3888, 888)
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
        break
      time.sleep(5)

#############################################################################################

#####
# Etc
#####
# Get current time
def getCurrentTime():
  return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

# Print header
def printHeader(header=''):
  print()
  print('-' * 100)
  print()
  if len(header) > 0:
    print('['+header+']')
    print()
