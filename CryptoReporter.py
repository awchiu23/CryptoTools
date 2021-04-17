from CryptoParams import *
import CryptoLib as cl
from joblib import Parallel, delayed
import pandas as pd
import datetime
import termcolor
import sys

###########
# Functions
###########
def get_EXTERNAL_EUR_NAV(spotEUR):
  return (spotEUR-EXTERNAL_EUR_REF)*EXTERNAL_EUR_DELTA

def getYest():
  return int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))))

def printDeltas(ccy,spot,spotDelta,futDelta):
  netDelta=spotDelta+futDelta
  print((ccy+' spot/fut/net delta: ').rjust(41)+str(round(spotDelta,1))+'/'+str(round(futDelta,1))+'/'+str(round(netDelta,1)) + \
    ' ($' + str(round(spotDelta * spot)) + '/$' + str(round(futDelta * spot)) + '/$' + str(round(netDelta * spot)) + ')')

def printEURDeltas(spot,spotDelta):
  netDelta=spotDelta+EXTERNAL_EUR_DELTA
  print('EUR ext/impl/net delta: '.rjust(41) + str(round(EXTERNAL_EUR_DELTA)) + '/' + str(round(spotDelta)) + '/' + str(round(netDelta)) + \
    ' ($' + str(round(EXTERNAL_EUR_DELTA * spot)) + '/$' + str(round(spotDelta * spot)) + '/$' + str(round(netDelta * spot)) + ')')

####################################################################################################

def ftxInit(ftx,spotBTC,spotETH):
  def cleanBorrows(ccy, df):
    dummy = pd.DataFrame([[0,0,0,0,0,0]], columns=['time','coin', 'size', 'rate', 'cost', 'proceeds'])
    if len(df)==0:
      return dummy
    df2 = df.copy()
    df2 = df2[df2['coin'] == ccy]
    if len(df2)==0:
      return dummy
    df2=df2.set_index('time').sort_index()
    return df2
  ######
  def getBorrowsLoans(ftxWallet,ccy):
    start_time=getYest()
    borrows = cleanBorrows(ccy, pd.DataFrame(ftx.private_get_spot_margin_borrow_history({'limit': 1000,'start_time':start_time})['result']))
    loans = cleanBorrows(ccy, pd.DataFrame(ftx.private_get_spot_margin_lending_history({'limit': 1000, 'start_time': start_time})['result']))
    cl.dfSetFloat(borrows, 'cost')
    cl.dfSetFloat(loans, 'proceeds')
    prevBorrow = borrows.iloc[-1]['cost']
    prevLoan = loans.iloc[-1]['proceeds']
    prevFlows = prevLoan - prevBorrow
    absBalance = abs(ftxWallet.loc[ccy, 'total'])
    prevFlowsAnnRet = prevFlows * 24 * 365 / absBalance
    oneDayFlows = loans['proceeds'].sum() - borrows['cost'].sum()
    oneDayFlowsAnnRet = oneDayFlows * 365 / absBalance
    return prevFlows,prevFlowsAnnRet,oneDayFlows,oneDayFlowsAnnRet
  #####
  info = ftx.private_get_account()['result']
  ######
  wallet=cl.ftxGetWallet(ftx)
  wallet['SpotDelta']=wallet['total']
  spotFTT = wallet.loc['FTT','spot']
  spotDeltaBTC = wallet.loc['BTC','SpotDelta']
  spotDeltaETH = wallet.loc['ETH','SpotDelta']
  spotDeltaFTT = wallet.loc['FTT','SpotDelta']
  ######
  futures = pd.DataFrame(info['positions'])
  cl.dfSetFloat(futures, 'size')
  futures['Ccy'] = [z[:3] for z in futures['future']]
  futures=futures.set_index('Ccy').loc[['BTC','ETH','FTT']]
  futures['FutDelta']=futures['size']
  futures.loc[futures['side']=='sell','FutDelta']*=-1
  futures['FutDeltaUSD'] = futures['FutDelta']
  futures.loc['BTC', 'FutDeltaUSD'] *= spotBTC
  futures.loc['ETH', 'FutDeltaUSD'] *= spotETH
  futures.loc['FTT', 'FutDeltaUSD'] *= spotFTT
  notional=futures['FutDeltaUSD'].abs().sum()
  ######
  payments = pd.DataFrame(ftx.private_get_funding_payments({'limit':1000,'start_time':getYest()})['result'])
  payments = payments.set_index('future',drop=False).loc[['BTC-PERP','ETH-PERP','FTT-PERP']].set_index('time')
  cl.dfSetFloat(payments, ['payment','rate'])
  payments=payments.sort_index()
  #####
  prevIncome = -payments.loc[payments.index[-1]]['payment'].sum()
  prevAnnRet = prevIncome * 24 * 365 / notional
  oneDayIncome = -payments['payment'].sum()
  oneDayAnnRet = oneDayIncome * 365 / notional
  #####
  prevUSDFlows,prevUSDFlowsAnnRet,oneDayUSDFlows,oneDayUSDFlowsAnnRet=getBorrowsLoans(wallet,  'USD')
  prevUSDTFlows,prevUSDTFlowsAnnRet,oneDayUSDTFlows,oneDayUSDTFlowsAnnRet=getBorrowsLoans(wallet, 'USDT')
  prevBTCFlows, prevBTCFlowsAnnRet, oneDayBTCFlows, oneDayBTCFlowsAnnRet = getBorrowsLoans(wallet, 'BTC')
  prevETHFlows, prevETHFlowsAnnRet, oneDayETHFlows, oneDayETHFlowsAnnRet = getBorrowsLoans(wallet, 'ETH')
  oneDayBTCFlows *= spotBTC
  oneDayETHFlows*=spotETH
  #####
  nav = wallet['usdValue'].sum()
  mf = float(info['marginFraction'])
  mmReq = float(info['maintenanceMarginRequirement'])
  totalPositionNotional = nav / mf
  cushion = (mf - mmReq) * totalPositionNotional
  totalDelta = wallet.loc[['BTC','ETH', 'FTT'], 'usdValue'].sum() + futures['FutDeltaUSD'].sum()
  liq = 1-cushion/totalDelta
  freeCollateral = float(info['freeCollateral'])
  #####
  return spotDeltaBTC, spotDeltaETH, spotDeltaFTT, wallet,futures,payments, \
         prevIncome,prevAnnRet,oneDayIncome,oneDayAnnRet, \
         prevUSDFlows,prevUSDFlowsAnnRet,oneDayUSDFlows,oneDayUSDFlowsAnnRet, \
         prevUSDTFlows, prevUSDTFlowsAnnRet, oneDayUSDTFlows, oneDayUSDTFlowsAnnRet, \
         prevBTCFlows, prevBTCFlowsAnnRet, oneDayBTCFlows, oneDayBTCFlowsAnnRet, \
         prevETHFlows,prevETHFlowsAnnRet,oneDayETHFlows,oneDayETHFlowsAnnRet, \
         nav,liq,mf,mmReq,freeCollateral, \
         spotFTT

####################################################################################################

def bbInit(bb,spotBTC,spotETH):
  def getPayments(ccy):
    n=0
    df=pd.DataFrame()
    while True:
      n+=1
      tl=bb.v2_private_get_execution_list({'symbol': ccy + 'USD', 'start_time': getYest()*1000, 'limit': 1000, 'page':n})['result']['trade_list']
      if tl is None:
        break
      else:
        df=df.append(pd.DataFrame(tl))
    return df.set_index('symbol',drop=False)
  #####
  def getLiq(futures, ccy):
    liqPrice = float(futures.loc[ccy, 'liq_price'])
    markPrice = float(futures.loc[ccy, 'size']) / (float(futures.loc[ccy, 'position_value']) + float(futures.loc[ccy, 'unrealised_pnl']))
    return liqPrice/markPrice
  #####
  bal=bb.fetch_balance()
  spotDeltaBTC=bal['BTC']['total']
  spotDeltaETH=bal['ETH']['total']
  #####
  futures=bb.v2_private_get_position_list()['result']
  futures=pd.DataFrame([pos['data'] for pos in futures])
  cl.dfSetFloat(futures,'size')
  futures['Ccy'] = [z[:3] for z in futures['symbol']]
  futures=futures.set_index('Ccy').loc[['BTC','ETH']]
  futures['FutDeltaUSD']=futures['size']
  futures.loc[futures['side'] == 'Sell', 'FutDeltaUSD'] *= -1
  futures['FutDelta']=futures['FutDeltaUSD']
  futures.loc['BTC','FutDelta']/=spotBTC
  futures.loc['ETH','FutDelta']/=spotETH
  notional=futures['FutDeltaUSD'].abs().sum()
  #####
  payments=getPayments('BTC').append(getPayments('ETH'))
  cl.dfSetFloat(payments,['fee_rate','exec_fee'])
  payments['incomeUSD']=-payments['exec_fee']
  payments.loc['BTCUSD','incomeUSD']*=spotBTC
  payments.loc['ETHUSD','incomeUSD']*=spotETH
  payments=payments[payments['exec_type']=='Funding']
  payments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in payments['trade_time_ms']]
  payments=payments.set_index('date')
  #####
  prevIncome = payments.loc[payments.index[-1]]['incomeUSD'].sum()
  prevAnnRet = prevIncome * 3 * 365 / notional
  oneDayIncome = payments['incomeUSD'].sum()
  oneDayAnnRet = oneDayIncome * 365 / notional
  #####
  nav = spotDeltaBTC * spotBTC + spotDeltaETH * spotETH
  liqBTC = getLiq(futures,'BTC')
  liqETH = getLiq(futures,'ETH')
  #####
  return spotDeltaBTC, spotDeltaETH, futures, payments, \
         prevIncome, prevAnnRet, oneDayIncome, oneDayAnnRet, \
         nav,liqBTC,liqETH

####################################################################################################

def bnInit(bn,spotBTC,spotETH):
  bal = pd.DataFrame(bn.dapiPrivate_get_balance())
  cl.dfSetFloat(bal, ['balance', 'crossUnPnl'])
  bal['Ccy']=bal['asset']
  bal=bal.set_index('Ccy').loc[['BTC','ETH']]
  bal['SpotDelta']=bal['balance']+bal['crossUnPnl']
  spotDeltaBTC=bal.loc['BTC','SpotDelta']
  spotDeltaETH=bal.loc['ETH','SpotDelta']
  #####
  futures = pd.DataFrame(bn.dapiPrivate_get_positionrisk())
  cl.dfSetFloat(futures, 'positionAmt')
  futures = futures[['USD_PERP' in z for z in futures['symbol']]]
  futures['Ccy'] = [z[:3] for z in futures['symbol']]
  futures=futures.set_index('Ccy').loc[['BTC','ETH']]
  futures['FutDeltaUSD']=futures['positionAmt']
  futures.loc['BTC', 'FutDeltaUSD'] *= 100
  futures.loc['ETH', 'FutDeltaUSD'] *= 10
  futures['FutDelta']=futures['FutDeltaUSD']
  futures.loc['BTC','FutDelta']/=spotBTC
  futures.loc['ETH','FutDelta']/=spotETH
  bnNotional=futures['FutDeltaUSD'].abs().sum()
  #####
  payments = pd.DataFrame(bn.dapiPrivate_get_income({'incomeType': 'FUNDING_FEE','startTime':getYest()*1000}))
  cl.dfSetFloat(payments, 'income')
  payments = payments[['USD_PERP' in z for z in payments['symbol']]]
  payments['Ccy'] = [z[:3] for z in payments['symbol']]
  payments = payments.set_index('Ccy').loc[['BTC','ETH']]
  payments['incomeUSD'] = payments['income']
  payments.loc['BTC', 'incomeUSD'] *= spotBTC
  payments.loc['ETH', 'incomeUSD'] *= spotETH
  payments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in payments['time']]
  payments = payments.set_index('date')
  #####
  prevIncome = payments.loc[payments.index[-1]]['incomeUSD'].sum()
  prevAnnRet = prevIncome * 3 * 365 / bnNotional
  oneDayIncome = payments['incomeUSD'].sum()
  oneDayAnnRet = oneDayIncome * 365 / bnNotional
  #####
  nav = bal.loc['BTC','SpotDelta'] * spotBTC +  bal.loc['ETH', 'SpotDelta'] * spotETH
  liqBTC=float(futures.loc['BTC', 'liquidationPrice']) / float(futures.loc['BTC', 'markPrice'])
  liqETH=float(futures.loc['ETH', 'liquidationPrice']) / float(futures.loc['ETH', 'markPrice'])
  #####
  return spotDeltaBTC, spotDeltaETH, bal, futures, payments, \
         prevIncome, prevAnnRet, oneDayIncome, oneDayAnnRet, \
         nav, liqBTC, liqETH

####################################################################################################

def kfInit(kf,spotBTC,spotETH):
  def getLog(kf, futures):
    ffn = os.path.dirname(cl.__file__) + '\\data\kfLog.csv'
    kf.get_account_log(ffn)
    df = pd.read_csv(ffn, index_col=0, parse_dates=True)
    df = df[df['type'] == 'funding rate change'].set_index('symbol')
    df.loc['xbt', 'Ccy'] = 'BTC'
    df.loc['eth', 'Ccy'] = 'ETH'
    df.loc['xbt', 'Spot'] = futures.loc['BTC', 'Spot']
    df.loc['eth', 'Spot'] = futures.loc['ETH', 'Spot']
    df.loc['xbt', 'FutDeltaUSD'] = futures.loc['BTC', 'FutDeltaUSD']
    df.loc['eth', 'FutDeltaUSD'] = futures.loc['ETH', 'FutDeltaUSD']
    df['date'] = [datetime.datetime.strptime(z, '%Y-%m-%d %H:%M:%S') for z in df['dateTime']]
    df['date'] += pd.DateOffset(hours=8)  # Convert from UTC to HK Time
    df = df[df['date'] >= datetime.datetime.now() - pd.DateOffset(days=1)]
    df['fundingRate'] = df['funding rate'] * df['Spot'] * 24 * 365
    df['fundingUSD'] = -df['fundingRate'] * df['FutDeltaUSD'] / 365 / 6
    return df.set_index('date').sort_index()
  #####
  accounts = kf.query('accounts')['accounts']
  spotDeltaBTC=accounts['fi_xbtusd']['auxiliary']['pv']+accounts['cash']['balances']['xbt']
  spotDeltaETH=accounts['fi_ethusd']['auxiliary']['pv']+accounts['cash']['balances']['eth']
  futures = pd.DataFrame([['BTC', spotBTC, accounts['fi_xbtusd']['balances']['pi_xbtusd']], \
                            ['ETH', spotETH, accounts['fi_ethusd']['balances']['pi_ethusd']]], \
                           columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
  futures['FutDelta'] = futures['FutDeltaUSD'] / futures['Spot']
  notional=futures['FutDeltaUSD'].abs().sum()
  #####
  if IS_IP_WHITELIST:
    log=getLog(kf,futures)
    prevIncome = log.loc[log.index[-1]]['fundingUSD'].sum()
    oneDayIncome = log['fundingUSD'].sum()
  else:
    log=None
    tickers = cl.kfGetTickers(kf)
    oneDayIncome = -futures.loc['BTC', 'FutDeltaUSD'] * cl.kfGetEstFunding1(kf, 'BTC', tickers) / 365
    oneDayIncome -= futures.loc['ETH', 'FutDeltaUSD'] * cl.kfGetEstFunding1(kf, 'ETH', tickers) / 365
    prevIncome = oneDayIncome/6
  prevAnnRet = prevIncome * 6 * 365 / notional
  oneDayAnnRet = oneDayIncome * 365 / notional
  #####
  nav = spotDeltaBTC * spotBTC + spotDeltaETH * spotETH
  liqBTC = accounts['fi_xbtusd']['triggerEstimates']['im']/spotBTC
  liqETH = accounts['fi_ethusd']['triggerEstimates']['im']/spotETH
  #####
  return spotDeltaBTC, spotDeltaETH, futures, log, \
         prevIncome, prevAnnRet, oneDayIncome, oneDayAnnRet, \
         nav, liqBTC, liqETH

####################################################################################################

def krInit(kr, spotBTC):
  def getBal(bal, ccy):
    try:
      return float(bal[ccy])
    except:
      return 0
  #####
  bal=kr.private_post_balance()['result']
  spotDeltaBTC = getBal(bal,'XXBT')
  spotDeltaETH = getBal(bal,'XETH')
  spotDeltaEUR = getBal(bal,'ZEUR')
  #####
  positions = pd.DataFrame(kr.private_post_openpositions()['result']).transpose().set_index('pair')
  if not all([z in ['XXBTZUSD','XXBTZEUR'] for z in positions.index]):
    print('Invalid Kraken pair detected!')
    sys.exit(1)
  cl.dfSetFloat(positions, ['vol', 'vol_closed', 'time'])
  positions['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in positions['time']]
  positions['volNetBTC'] = positions['vol']- positions['vol_closed']
  positions['volNetUSD'] = positions['volNetBTC']*spotBTC
  spotDeltaBTC += positions['volNetBTC'].sum()
  btcMarginDeltaUSD = positions['volNetUSD'].sum()
  notional = positions['volNetUSD'].abs().sum()
  #####
  spot_xxbtzeur=float(kr.public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
  spot_xxbtzusd=float(kr.public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
  spotEUR = spot_xxbtzusd/spot_xxbtzeur
  spotDeltaEUR -= positions.loc['XXBTZEUR','volNetBTC'].sum()*spot_xxbtzeur
  #####
  oneDayIncome=-btcMarginDeltaUSD*0.0006
  oneDayAnnRet = oneDayIncome * 365 / notional
  #####
  tradeBal = kr.private_post_tradebalance()['result']
  nav = float(tradeBal['e'])
  #####
  freeMargin = float(tradeBal['mf'])
  liqBTC = 1 - freeMargin / (spotDeltaBTC * spotBTC)
  #####
  return spotDeltaBTC, spotDeltaETH, spotDeltaEUR, btcMarginDeltaUSD, \
         oneDayIncome, oneDayAnnRet, \
         nav, liqBTC, spotEUR

def krPrintIncomes(krCores):
  zs=[]
  prefixes=[]
  for krCore in krCores:
    zs.append('$' + str(round(krCore.oneDayIncome)) + ' (' + str(round(krCore.oneDayAnnRet * 100)) + '% p.a.)')
    prefixes.append('KR' + str(krCore.n))
  print(termcolor.colored(('/'.join(prefixes) + ' 24h rollover fees: ').rjust(41) + ' / '.join(zs), 'blue'))

def krPrintLiq(krCores):
  zs=[]
  prefixes=[]
  for krCore in krCores:
    zs.append('never' if (krCore.liqBTC <= 0 or krCore.liqBTC > 10) else str(round(krCore.liqBTC * 100)) + '%')
    prefixes.append('KR' + str(krCore.n))
  print(termcolor.colored(('/'.join(prefixes) + ' liquidation (BTC): ').rjust(41) + '/'.join(zs) + ' (of spot)', 'red'))

####################################################################################################

def cbInit(cb,spotBTC,spotETH):
  bal=cb.fetch_balance()
  spotDeltaBTC=bal['BTC']['total']
  spotDeltaETH=bal['ETH']['total']
  nav=spotDeltaBTC*spotBTC+spotDeltaETH*spotETH
  return spotDeltaBTC,spotDeltaETH,nav

####################################################################################################

#########
# Classes
#########
class core:
  def __init__(self, exch, spotBTC, spotETH, n=None):
    self.exch = exch
    self.spotBTC = spotBTC
    self.spotETH = spotETH
    if n is not None:
      self.n = n

  def run(self):
    if self.exch=='ftx':
      self.api = cl.ftxCCXTInit()
      self.spotDeltaBTC, self.spotDeltaETH, self.spotDeltaFTT, self.wallet, self.futures, self.payments, \
      self.prevIncome, self.prevAnnRet, self.oneDayIncome, self.oneDayAnnRet, \
      self.prevUSDFlows, self.prevUSDFlowsAnnRet, self.oneDayUSDFlows, self.oneDayUSDFlowsAnnRet, \
      self.prevUSDTFlows, self.prevUSDTFlowsAnnRet, self.oneDayUSDTFlows, self.oneDayUSDTFlowsAnnRet, \
      self.prevBTCFlows, self.prevBTCFlowsAnnRet, self.oneDayBTCFlows, self.oneDayBTCFlowsAnnRet, \
      self.prevETHFlows, self.prevETHFlowsAnnRet, self.oneDayETHFlows, self.oneDayETHFlowsAnnRet, \
      self.nav, self.liq, self.mf, self.mmReq, self.freeCollateral, \
      self.spotFTT = ftxInit(self.api,self.spotBTC,self.spotETH)
    elif self.exch=='bb':
      self.api = cl.bbCCXTInit()
      self.spotDeltaBTC, self.spotDeltaETH, self.futures, self.payments, \
      self.prevIncome, self.prevAnnRet, self.oneDayIncome, self.oneDayAnnRet, \
      self.nav, self.liqBTC, self.liqETH = bbInit(self.api, self.spotBTC, self.spotETH)
    elif self.exch=='bn':
      self.api = cl.bnCCXTInit()
      self.spotDeltaBTC, self.spotDeltaETH, self.bal, self.futures, self.payments, \
      self.prevIncome, self.prevAnnRet, self.oneDayIncome, self.oneDayAnnRet, \
      self.nav, self.liqBTC, self.liqETH = bnInit(self.api, self.spotBTC, self.spotETH)
    elif self.exch=='kf':
      self.api = cl.kfInit()
      self.spotDeltaBTC, self.spotDeltaETH, self.futures, self.log, \
      self.prevIncome, self.prevAnnRet, self.oneDayIncome, self.oneDayAnnRet, \
      self.nav, self.liqBTC, self.liqETH = kfInit(self.api, self.spotBTC, self.spotETH)
    elif self.exch=='kr':
      self.api = cl.krCCXTInit(self.n)
      self.spotDeltaBTC, self.spotDeltaETH, self.spotDeltaEUR, self.btcMarginDeltaUSD, \
      self.oneDayIncome, self.oneDayAnnRet, \
      self.nav, self.liqBTC, self.spotEUR = krInit(self.api, self.spotBTC)
      self.futures = pd.DataFrame([['BTC',0],['ETH',0]],columns=['Ccy','FutDelta']).set_index('Ccy')
    elif self.exch == 'cb':
      self.api = cl.cbCCXTInit()
      self.spotDeltaBTC, self.spotDeltaETH, self.nav = cbInit(self.api, self.spotBTC, self.spotETH)
      self.oneDayIncome=0
      self.futures = pd.DataFrame([['BTC', 0], ['ETH', 0]], columns=['Ccy', 'FutDelta']).set_index('Ccy')

  def printIncomes(self):
    z1 = '$' + str(round(self.oneDayIncome)) + ' (' + str(round(self.oneDayAnnRet * 100)) + '% p.a.)'
    z2 = '$' + str(round(self.prevIncome)) + ' (' + str(round(self.prevAnnRet * 100)) + '% p.a.)'
    print(termcolor.colored((self.exch.upper() + ' 24h/prev funding income: ').rjust(41) + z1 + ' / ' + z2, 'blue'))

  def printFunding(self,ccy):
    if self.exch=='ftx':
      df = self.payments[self.payments['future'] == ccy + '-PERP']
      oneDayFunding = df['rate'].mean() * 24 * 365
      prevFunding = df['rate'][-1] * 24 * 365
      estFunding = cl.ftxGetEstFunding(self.api, ccy)
    elif self.exch=='bb':
      df = self.payments[self.payments['symbol'] == ccy + 'USD'].copy()
      for i in range(len(df)):
        if 'Sell' in df.iloc[i]['order_id']:
          df.loc[df.index[i], 'fee_rate'] *= -1
      oneDayFunding = df['fee_rate'].mean() * 3 * 365
      prevFunding = df['fee_rate'][-1] * 3 * 365
      estFunding = cl.bbGetEstFunding1(self.api, ccy)
      est2Funding = cl.bbGetEstFunding2(self.api, ccy)
    elif self.exch=='bn':
      df = pd.DataFrame(self.api.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP', 'startTime': getYest() * 1000}))
      cl.dfSetFloat(df, 'fundingRate')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
      df = df.set_index('date').sort_index()
      oneDayFunding = df['fundingRate'].mean() * 3 * 365
      prevFunding = df['fundingRate'][-1] * 3 * 365
      estFunding = cl.bnGetEstFunding(self.api, ccy)
    elif self.exch=='kf':
      if self.log is None:
        prevFunding = self.prevAnnRet
        oneDayFunding = self.oneDayAnnRet
      else:
        df = self.log[self.log['Ccy'] == ccy].copy()
        prevFunding = df['fundingRate'][-1]
        oneDayFunding = df['fundingRate'].mean()
      tickers = cl.kfGetTickers(self.api)
      estFunding = cl.kfGetEstFunding1(self.api, ccy, tickers)
      est2Funding = cl.kfGetEstFunding2(self.api, ccy, tickers)
    prefix = self.exch.upper() + ' ' + ccy + ' 24h/prev/est'
    if self.exch in ['bb', 'kf']:
      prefix += '1/est2'
    prefix += ' funding rate:'
    suffix = str(round(oneDayFunding * 100)) + '%/' + str(round(prevFunding * 100)) + '%/' + str(round(estFunding * 100)) + '%'
    if self.exch in ['bb', 'kf']:
      suffix += '/' + str(round(est2Funding * 100)) + '%'
    suffix += ' p.a. ($' + str(round(self.futures.loc[ccy, 'FutDeltaUSD'])) + ')'
    print(prefix.rjust(40) + ' ' + suffix)

  def printLiq(self):
    if self.exch=='ftx':
      z = 'never' if (self.liq <= 0 or self.liq > 10) else str(round(self.liq * 100)) + '%'
      print(termcolor.colored('FTX liquidation (parallel shock): '.rjust(41) + z + ' (of spot)', 'red'))
      print(termcolor.colored('FTX margin fraction: '.rjust(41) + str(round(self.mf * 100, 1)) + '% (vs. ' + str(round(self.mmReq * 100, 1)) + '% limit)', 'red'))
      print(termcolor.colored('FTX free collateral: $'.rjust(42) + str(round(self.freeCollateral)), 'red'))
    else:
      zBTC = 'never' if (self.liqBTC <= 0 or self.liqBTC >= 10) else str(round(self.liqBTC * 100)) + '%'
      zETH = 'never' if (self.liqETH <= 0 or self.liqETH >= 10) else str(round(self.liqETH * 100)) + '%'
      print(termcolor.colored((self.exch.upper() + ' liquidation (BTC/ETH): ').rjust(41) + zBTC + '/' + zETH + ' (of spot)', 'red'))

  def ftxPrintFlowsSummary(self,ccy):
    if ccy=='USD':
      oneDayFlows=self.oneDayUSDFlows
      oneDayFlowsAnnRet=self.oneDayUSDFlowsAnnRet
      prevFlows=self.prevUSDFlows
      prevFlowsAnnRet=self.prevUSDFlowsAnnRet      
    elif ccy=='USDT':
      oneDayFlows = self.oneDayUSDTFlows
      oneDayFlowsAnnRet = self.oneDayUSDTFlowsAnnRet
      prevFlows = self.prevUSDTFlows
      prevFlowsAnnRet = self.prevUSDTFlowsAnnRet
    elif ccy=='BTC':
      oneDayFlows = self.oneDayBTCFlows
      oneDayFlowsAnnRet = self.oneDayBTCFlowsAnnRet
      prevFlows = self.prevBTCFlows*self.spotBTC
      prevFlowsAnnRet = self.prevBTCFlowsAnnRet
    elif ccy=='ETH':
      oneDayFlows = self.oneDayETHFlows
      oneDayFlowsAnnRet = self.oneDayETHFlowsAnnRet
      prevFlows = self.prevETHFlows*self.spotETH
      prevFlowsAnnRet = self.prevETHFlowsAnnRet      
    else:
      sys.exit(1)
    z1 = '$' + str(round(oneDayFlows)) + ' (' + str(round(oneDayFlowsAnnRet * 100)) + '% p.a.)'
    z2 = '$' + str(round(prevFlows)) + ' (' + str(round(prevFlowsAnnRet * 100)) + '% p.a.)'
    print(termcolor.colored(('FTX 24h/prev '+ccy+' flows: ').rjust(41) + z1 + ' / ' + z2, 'blue'))
  
  def ftxPrintBorrowLending(self, ccy, nav):
    estBorrow = cl.ftxGetEstBorrow(self.api,ccy)
    estLending = cl.ftxGetEstLending(self.api,ccy)
    n = self.wallet.loc[ccy, 'usdValue']
    z1 = '($' + str(round(n))+')'
    z2 = '(' + str(round(n/nav*100))+'% of NAV)'
    print(('FTX '+ccy+' est borrow/lending rate: ').rjust(41) + str(round(estBorrow * 100)) + '%/' + str(round(estLending * 100))+ '% p.a. '+ z1+' '+z2)
  
  def ftxPrintCoinLending(self, ccy):
    estLending = float(pd.DataFrame(self.api.private_get_spot_margin_lending_rates()['result']).set_index('coin').loc[ccy, 'estimate']) * 24 * 365
    coinBalance = self.wallet.loc[ccy, 'usdValue']
    print(('FTX '+ccy+' est lending rate: ').rjust(41) + str(round(estLending * 100)) + '% p.a. ($' + str(round(coinBalance)) + ')')

  def krPrintBorrow(self, nav):
    z = '($' + str(round(-self.btcMarginDeltaUSD)) + ') '
    z += '(' + str(round(-self.btcMarginDeltaUSD / nav * 100)) + '% of NAV)'
    print(('KR' + str(self.n) + ' USD/EUR est borrow rate: ').rjust(41) + '22% p.a. ' + z)

####################################################################################################

######
# Init
######
cl.printHeader('CryptoReporter')
ftxWallet=cl.ftxGetWallet(cl.ftxCCXTInit())
spotBTC = ftxWallet.loc['BTC','spot']
spotETH = ftxWallet.loc['ETH','spot']
#####
ftxCore = core('ftx',spotBTC,spotETH)
bbCore = core('bb',spotBTC,spotETH)
cbCore = core('cb',spotBTC,spotETH)
objs=[ftxCore,bbCore,cbCore]
if CR_IS_ADVANCED:
  bnCore = core('bn', spotBTC, spotETH)
  kfCore = core('kf', spotBTC, spotETH)
  krCores = []
  for i in range(CR_N_KR_ACCOUNTS):
    krCores.append(core('kr',spotBTC, spotETH,i+1))
  objs.extend([bnCore,kfCore]+krCores)
Parallel(n_jobs=len(objs), backend='threading')(delayed(obj.run)() for obj in objs)

#############
# Aggregation
#############
nav=0
oneDayIncome=0
spotDeltaBTC=0
spotDeltaETH=0
futDeltaBTC=0
futDeltaETH=0
for obj in objs:
  nav+=obj.nav
  oneDayIncome+=obj.oneDayIncome
  spotDeltaBTC+=obj.spotDeltaBTC
  spotDeltaETH+=obj.spotDeltaETH
  futDeltaBTC+=obj.futures.loc['BTC','FutDelta']
  futDeltaETH+=obj.futures.loc['ETH','FutDelta']
oneDayIncome+=ftxCore.oneDayUSDFlows+ftxCore.oneDayUSDTFlows+ftxCore.oneDayBTCFlows+ftxCore.oneDayETHFlows
if CR_IS_ADVANCED:
  nav+=get_EXTERNAL_EUR_NAV(krCores[0].spotEUR)
spotDeltaFTT=ftxCore.spotDeltaFTT
futDeltaFTT=ftxCore.futures.loc['FTT','FutDelta']

########
# Output
########
z=('NAV as of '+cl.getCurrentTime()+': $').rjust(42)+str(round(nav))
z+=' (FTX: $' + str(round(ftxCore.nav/1000)) + 'K'
z+=' / BB: $' + str(round(bbCore.nav/1000)) + 'K'
if CR_IS_ADVANCED:
  z+=' / BN: $' + str(round(bnCore.nav/1000)) + 'K'
  z += ' / KF: $' + str(round(kfCore.nav / 1000)) + 'K'
  for krCore in krCores:
    z+= ' / KR' + str(krCore.n)+': $'+str(round(krCore.nav/1000))+'K'
z+=' / CB: $' + str(round(cbCore.nav/1000)) + 'K)'
print(termcolor.colored(z,'blue'))
print(termcolor.colored('24h income: $'.rjust(42)+str(round(oneDayIncome))+' ('+str(round(oneDayIncome*365/nav*100))+'% p.a.)','blue'))
print()
#####
ftxCore.ftxPrintFlowsSummary('USD')
ftxCore.ftxPrintFlowsSummary('USDT')
ftxCore.ftxPrintBorrowLending('USD',nav)
ftxCore.ftxPrintBorrowLending('USDT',nav)
print()
#####
if CR_IS_SHOW_COIN_LENDING:
  ftxCore.ftxPrintFlowsSummary('BTC')
  ftxCore.ftxPrintFlowsSummary('ETH')
  ftxCore.ftxPrintCoinLending('BTC')
  ftxCore.ftxPrintCoinLending('ETH')
  print()
#####
ftxCore.printIncomes()
ftxCore.printFunding('BTC')
ftxCore.printFunding('ETH')
ftxCore.printFunding('FTT')
ftxCore.printLiq()
print()
#####
bbCore.printIncomes()
bbCore.printFunding('BTC')
bbCore.printFunding('ETH')
bbCore.printLiq()
print()
#####
if CR_IS_ADVANCED:
  bnCore.printIncomes()
  bnCore.printFunding('BTC')
  bnCore.printFunding('ETH')
  bnCore.printLiq()
  print()
  #####
  kfCore.printIncomes()
  kfCore.printFunding('BTC')
  kfCore.printFunding('ETH')
  kfCore.printLiq()
  print()
  #####
  krPrintIncomes(krCores)
  for krCore in krCores:
    krCore.krPrintBorrow(nav)
  krPrintLiq(krCores)
  print()
#####
printDeltas('BTC',spotBTC,spotDeltaBTC,futDeltaBTC)
printDeltas('ETH',spotETH,spotDeltaETH,futDeltaETH)
printDeltas('FTT',ftxCore.spotFTT,spotDeltaFTT,futDeltaFTT)
if CR_IS_ADVANCED:
  spotDeltaEUR=0
  for krCore in krCores:
    spotDeltaEUR+=krCore.spotDeltaEUR
  printEURDeltas(krCores[0].spotEUR,spotDeltaEUR)
