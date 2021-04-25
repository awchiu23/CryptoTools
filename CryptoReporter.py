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
def getDummyFutures():
  return pd.DataFrame([['BTC', 0], ['ETH', 0]], columns=['Ccy', 'FutDelta']).set_index('Ccy')

def get_EXTERNAL_EUR_NAV(spotEUR):
  return (spotEUR-EXTERNAL_EUR_REF)*EXTERNAL_EUR_DELTA

def getYest():
  return int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))))

def printDeltas(ccy,spot,spotDelta,futDelta):
  netDelta=spotDelta+futDelta
  print((ccy+' spot/fut/net delta: ').rjust(41)+(str(round(spotDelta,1))+'/'+str(round(futDelta,1))+'/'+str(round(netDelta,1))).ljust(27) + \
    '($' + str(round(spotDelta * spot/1000)) + 'K/$' + str(round(futDelta * spot/1000)) + 'K/$' + str(round(netDelta * spot/1000)) + 'K)')

def printEURDeltas(spot,spotDelta):
  netDelta=spotDelta+EXTERNAL_EUR_DELTA
  print('EUR ext/impl/net delta: '.rjust(41) + (str(round(EXTERNAL_EUR_DELTA/1000)) + 'K/' + str(round(spotDelta/1000)) + 'K/' + str(round(netDelta/1000))+'K').ljust(27) + \
    '($' + str(round(EXTERNAL_EUR_DELTA * spot/1000)) + 'K/$' + str(round(spotDelta * spot/1000)) + 'K/$' + str(round(netDelta * spot/1000)) + 'K)')

####################################################################################################

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

#########
# Classes
#########
class core:
  def __init__(self, exch, spotBTC, spotETH, spotFTT=None, spotUSDT=None, spotEUR=None, n=None):
    self.exch = exch
    self.spotBTC = spotBTC
    self.spotETH = spotETH
    if spotFTT is not None: self.spotFTT = spotFTT
    if spotUSDT is not None: self.spotUSDT = spotUSDT
    if spotEUR is not None: self.spotEUR = spotEUR
    if n is not None: self.n = n

  def run(self):
    if self.exch=='ftx':
      self.api = cl.ftxCCXTInit()
      self.ftxInit()
    elif self.exch=='bb':
      self.api = cl.bbCCXTInit()
      self.bbInit()
    elif self.exch=='bn':
      self.api = cl.bnCCXTInit()
      self.bnInit()
    elif self.exch=='bt':
      self.api = cl.bnCCXTInit()
      self.btInit()
    elif self.exch=='db':
      self.api = cl.dbCCXTInit()
      self.dbInit()
    elif self.exch=='kf':
      self.api = cl.kfInit()
      self.kfInit()
    elif self.exch=='kr':
      self.api = cl.krCCXTInit(self.n)
      self.krInit()
    elif self.exch == 'cb':
      self.api = cl.cbCCXTInit()
      self.cbInit()

  def printIncomes(self):
    z1 = '$' + str(round(self.oneDayIncome)) + ' (' + str(round(self.oneDayAnnRet * 100)) + '% p.a.)'
    if self.exch == 'db':
      print(termcolor.colored('DB 24h funding income: '.rjust(41) + z1, 'blue'))
    else:
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
    elif self.exch=='bt':
      df = pd.DataFrame(self.api.fapiPublic_get_fundingrate({'symbol': ccy + 'USDT', 'startTime': getYest() * 1000}))
      cl.dfSetFloat(df, 'fundingRate')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
      df = df.set_index('date').sort_index()
      oneDayFunding = df['fundingRate'].mean() * 3 * 365
      prevFunding = df['fundingRate'][-1] * 3 * 365
      estFunding = cl.btGetEstFunding(self.api, ccy)
    elif self.exch=='db':
      oneDayFunding = cl.dbGetEstFunding(self.api, ccy, mins=60 * 24)
      prevFunding = cl.dbGetEstFunding(self.api, ccy, mins=60 * 8)
      estFunding = cl.dbGetEstFunding(self.api, ccy)
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
    #####
    prefix = self.exch.upper() + ' ' + ccy + ' 24h/'
    if self.exch=='db':
      prefix+='8h'
    else:
      prefix+='prev'
    prefix+='/est'
    if self.exch in ['bb', 'kf']:
      prefix += '1/est2'
    prefix += ' funding rate:'
    #####
    body = str(round(oneDayFunding * 100)) + '%/'
    body += str(round(prevFunding * 100)) + '%/'
    body += str(round(estFunding * 100)) + '%'
    if self.exch in ['bb', 'kf']:
      body += '/' + str(round(est2Funding * 100)) + '%'
    body += ' p.a.'
    #####
    if ccy=='BTC':
      spotDeltaUSD=self.spotDeltaBTC*self.spotBTC
    elif ccy=='ETH':
      spotDeltaUSD=self.spotDeltaETH*self.spotETH
    elif ccy=='FTT':
      spotDeltaUSD=self.spotDeltaFTT*self.spotFTT
    else:
      sys.exit(1)
    futDeltaUSD=self.futures.loc[ccy, 'FutDeltaUSD']
    netDeltaUSD=spotDeltaUSD+futDeltaUSD
    if self.exch=='bt':
      suffix = '(fut delta: $' + str(round(futDeltaUSD / 1000)) + 'K)'
    else:
      suffix = '(spot/fut/net delta: $' + str(round(spotDeltaUSD/1000)) + 'K/$' + str(round(futDeltaUSD/1000)) + 'K/$' + str(round(netDeltaUSD/1000))+'K)'
    print(prefix.rjust(40) + ' ' + body.ljust(27) + suffix)

  def printLiq(self):
    if self.exch=='ftx':
      z = 'never' if (self.liq <= 0 or self.liq > 10) else str(round(self.liq * 100)) + '% (of spot)'
      print(termcolor.colored('FTX liquidation (parallel shock): '.rjust(41) + z , 'red'))
      z= str(round(self.mf * 100, 1)) + '% (vs. ' + str(round(self.mmReq * 100, 1)) + '% limit) / $' + str(round(self.freeCollateral))
      print(termcolor.colored('FTX margin fraction/free collateral: '.rjust(41) + z, 'red'))
    else:
      zBTC = 'never' if (self.liqBTC <= 0 or self.liqBTC >= 10) else str(round(self.liqBTC * 100)) + '%'
      zETH = 'never' if (self.liqETH <= 0 or self.liqETH >= 10) else str(round(self.liqETH * 100)) + '%'
      print(termcolor.colored((self.exch.upper() + ' liquidation (BTC/ETH): ').rjust(41) + zBTC + '/' + zETH + ' (of spot)', 'red'))

  #####
  # FTX
  #####
  def ftxInit(self):
    def cleanBorrows(ccy, df):
      dummy = pd.DataFrame([[0, 0, 0, 0, 0, 0]], columns=['time', 'coin', 'size', 'rate', 'cost', 'proceeds'])
      if len(df) == 0:
        return dummy
      df2 = df.copy()
      df2 = df2[df2['coin'] == ccy]
      if len(df2) == 0:
        return dummy
      df2 = df2.set_index('time').sort_index()
      return df2
    ######
    def getBorrowsLoans(api, wallet, payments, ccy):
      start_time = getYest()
      borrows = cleanBorrows(ccy, pd.DataFrame(api.private_get_spot_margin_borrow_history({'limit': 1000, 'start_time': start_time})['result']))
      loans = cleanBorrows(ccy, pd.DataFrame(api.private_get_spot_margin_lending_history({'limit': 1000, 'start_time': start_time})['result']))
      cl.dfSetFloat(borrows, 'cost')
      cl.dfSetFloat(loans, 'proceeds')
      prevBorrow = borrows.iloc[-1]['cost'] if borrows.index[-1] == payments.index[-1] else 0
      prevLoan = loans.iloc[-1]['proceeds'] if loans.index[-1] == payments.index[-1] else 0
      prevFlows = prevLoan - prevBorrow
      absBalance = abs(wallet.loc[ccy, 'total'])
      prevFlowsAnnRet = prevFlows * 24 * 365 / absBalance
      oneDayFlows = loans['proceeds'].sum() - borrows['cost'].sum()
      oneDayFlowsAnnRet = oneDayFlows * 365 / absBalance
      return prevFlows, prevFlowsAnnRet, oneDayFlows, oneDayFlowsAnnRet
    #####    
    info = self.api.private_get_account()['result']
    ######
    wallet = cl.ftxGetWallet(ftx)
    wallet['SpotDelta'] = wallet['total']
    spotDeltaBTC = wallet.loc['BTC', 'SpotDelta']
    spotDeltaETH = wallet.loc['ETH', 'SpotDelta']
    spotDeltaFTT = wallet.loc['FTT', 'SpotDelta']
    ######
    futures = pd.DataFrame(info['positions'])
    cl.dfSetFloat(futures, 'size')
    futures['Ccy'] = [z[:3] for z in futures['future']]
    futures = futures.set_index('Ccy').loc[['BTC', 'ETH', 'FTT']]
    futures['FutDelta'] = futures['size']
    futures.loc[futures['side'] == 'sell', 'FutDelta'] *= -1
    futures['FutDeltaUSD'] = futures['FutDelta']
    futures.loc['BTC', 'FutDeltaUSD'] *= self.spotBTC
    futures.loc['ETH', 'FutDeltaUSD'] *= self.spotETH
    futures.loc['FTT', 'FutDeltaUSD'] *= self.spotFTT
    notional = futures['FutDeltaUSD'].abs().sum()
    ######
    payments = pd.DataFrame(self.api.private_get_funding_payments({'limit': 1000, 'start_time': getYest()})['result'])
    payments = payments.set_index('future', drop=False).loc[['BTC-PERP', 'ETH-PERP', 'FTT-PERP']].set_index('time')
    cl.dfSetFloat(payments, ['payment', 'rate'])
    payments = payments.sort_index()
    #####
    prevIncome = -payments.loc[payments.index[-1]]['payment'].sum()
    prevAnnRet = prevIncome * 24 * 365 / notional
    oneDayIncome = -payments['payment'].sum()
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    prevUSDFlows, prevUSDFlowsAnnRet, oneDayUSDFlows, oneDayUSDFlowsAnnRet = getBorrowsLoans(self.api,wallet, payments, 'USD')
    prevUSDTFlows, prevUSDTFlowsAnnRet, oneDayUSDTFlows, oneDayUSDTFlowsAnnRet = getBorrowsLoans(self.api,wallet, payments, 'USDT')
    prevBTCFlows, prevBTCFlowsAnnRet, oneDayBTCFlows, oneDayBTCFlowsAnnRet = getBorrowsLoans(self.api,wallet, payments, 'BTC')
    prevETHFlows, prevETHFlowsAnnRet, oneDayETHFlows, oneDayETHFlowsAnnRet = getBorrowsLoans(self.api,wallet, payments, 'ETH')
    oneDayBTCFlows *= self.spotBTC
    oneDayETHFlows *= self.spotETH
    #####
    nav = wallet['usdValue'].sum()
    mf = float(info['marginFraction'])
    mmReq = float(info['maintenanceMarginRequirement'])
    totalPositionNotional = nav / mf
    cushion = (mf - mmReq) * totalPositionNotional
    totalDelta = wallet.loc[['BTC', 'ETH', 'FTT'], 'usdValue'].sum() + futures['FutDeltaUSD'].sum()
    liq = 1 - cushion / totalDelta
    freeCollateral = float(info['freeCollateral'])
    #####
    self.spotDeltaBTC=spotDeltaBTC
    self.spotDeltaETH=spotDeltaETH
    self.spotDeltaFTT=spotDeltaFTT
    self.wallet=wallet
    self.futures=futures
    self.payments=payments
    self.prevIncome=prevIncome
    self.prevAnnRet=prevAnnRet
    self.oneDayIncome=oneDayIncome
    self.oneDayAnnRet=oneDayAnnRet
    self.prevUSDFlows=prevUSDFlows
    self.prevUSDFlowsAnnRet=prevUSDFlowsAnnRet
    self.oneDayUSDFlows=oneDayUSDFlows
    self.oneDayUSDFlowsAnnRet=oneDayUSDFlowsAnnRet
    self.prevUSDTFlows = prevUSDTFlows
    self.prevUSDTFlowsAnnRet = prevUSDTFlowsAnnRet
    self.oneDayUSDTFlows = oneDayUSDTFlows
    self.oneDayUSDTFlowsAnnRet = oneDayUSDTFlowsAnnRet
    self.prevBTCFlows = prevBTCFlows
    self.prevBTCFlowsAnnRet = prevBTCFlowsAnnRet
    self.oneDayBTCFlows = oneDayBTCFlows
    self.oneDayBTCFlowsAnnRet = oneDayBTCFlowsAnnRet
    self.prevETHFlows = prevETHFlows
    self.prevETHFlowsAnnRet = prevETHFlowsAnnRet
    self.oneDayETHFlows = oneDayETHFlows
    self.oneDayETHFlowsAnnRet = oneDayETHFlowsAnnRet
    self.nav=nav
    self.liq=liq
    self.mf=mf
    self.mmReq=mmReq
    self.freeCollateral=freeCollateral

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
    suffix = '($' + str(round(n/1000))+'K) '
    suffix += '(' + str(round(n/nav*100))+'%)'
    print(('FTX '+ccy+' est borrow/lending rate: ').rjust(41) + (str(round(estBorrow * 100)) + '%/' + str(round(estLending * 100))+ '% p.a. '+suffix).ljust(27))
  
  def ftxPrintCoinLending(self, ccy):
    estLending = float(pd.DataFrame(self.api.private_get_spot_margin_lending_rates()['result']).set_index('coin').loc[ccy, 'estimate']) * 24 * 365
    coinBalance = self.wallet.loc[ccy, 'usdValue']
    print(('FTX '+ccy+' est lending rate: ').rjust(41) + str(round(estLending * 100)) + '% p.a. ($' + str(round(coinBalance/1000)) + 'K)')

  ####
  # BB
  ####
  def bbInit(self):
    def getPayments(api,ccy):
      n = 0
      df = pd.DataFrame()
      while True:
        n += 1
        tl = api.v2_private_get_execution_list({'symbol': ccy + 'USD', 'start_time': getYest() * 1000, 'limit': 1000, 'page': n})['result']['trade_list']
        if tl is None:
          break
        else:
          df = df.append(pd.DataFrame(tl))
      return df.set_index('symbol', drop=False)
    #####
    def getLiq(futures, ccy):
      liqPrice = float(futures.loc[ccy, 'liq_price'])
      markPrice = float(futures.loc[ccy, 'size']) / (float(futures.loc[ccy, 'position_value']) + float(futures.loc[ccy, 'unrealised_pnl']))
      return liqPrice / markPrice
    #####    
    bal = self.api.fetch_balance()
    spotDeltaBTC = bal['BTC']['total']
    spotDeltaETH = bal['ETH']['total']
    #####
    futures = self.api.v2_private_get_position_list()['result']
    futures = pd.DataFrame([pos['data'] for pos in futures])
    cl.dfSetFloat(futures, 'size')
    futures['Ccy'] = [z[:3] for z in futures['symbol']]
    futures = futures.set_index('Ccy').loc[['BTC', 'ETH']]
    futures['FutDeltaUSD'] = futures['size']
    futures.loc[futures['side'] == 'Sell', 'FutDeltaUSD'] *= -1
    futures['FutDelta'] = futures['FutDeltaUSD']
    futures.loc['BTC', 'FutDelta'] /= self.spotBTC
    futures.loc['ETH', 'FutDelta'] /= self.spotETH
    notional = futures['FutDeltaUSD'].abs().sum()
    #####
    payments = getPayments(self.api,'BTC').append(getPayments(self.api,'ETH'))
    cl.dfSetFloat(payments, ['fee_rate', 'exec_fee'])
    payments['incomeUSD'] = -payments['exec_fee']
    payments.loc['BTCUSD', 'incomeUSD'] *= self.spotBTC
    payments.loc['ETHUSD', 'incomeUSD'] *= self.spotETH
    payments = payments[payments['exec_type'] == 'Funding']
    payments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in payments['trade_time_ms']]
    payments = payments.set_index('date')
    #####
    prevIncome = payments.loc[payments.index[-1]]['incomeUSD'].sum()
    prevAnnRet = prevIncome * 3 * 365 / notional
    oneDayIncome = payments['incomeUSD'].sum()
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    nav = spotDeltaBTC * self.spotBTC + spotDeltaETH * self.spotETH
    liqBTC = getLiq(futures, 'BTC')
    liqETH = getLiq(futures, 'ETH')
    #####
    self.spotDeltaBTC=spotDeltaBTC
    self.spotDeltaETH=spotDeltaETH
    self.futures=futures
    self.payments=payments
    self.prevIncome=prevIncome
    self.prevAnnRet=prevAnnRet
    self.oneDayIncome=oneDayIncome
    self.oneDayAnnRet=oneDayAnnRet
    self.nav=nav
    self.liqBTC=liqBTC
    self.liqETH=liqETH
  
  ####
  # BN
  ####
  def bnInit(self):
    bal = pd.DataFrame(self.api.dapiPrivate_get_balance())
    cl.dfSetFloat(bal, ['balance', 'crossUnPnl'])
    bal['Ccy'] = bal['asset']
    bal = bal.set_index('Ccy').loc[['BTC', 'ETH']]
    bal['SpotDelta'] = bal['balance'] + bal['crossUnPnl']
    spotDeltaBTC = bal.loc['BTC', 'SpotDelta']
    spotDeltaETH = bal.loc['ETH', 'SpotDelta']
    #####
    futures = pd.DataFrame(self.api.dapiPrivate_get_positionrisk())
    cl.dfSetFloat(futures, 'positionAmt')
    futures = futures[['USD_PERP' in z for z in futures['symbol']]]
    futures['Ccy'] = [z[:3] for z in futures['symbol']]
    futures = futures.set_index('Ccy').loc[['BTC', 'ETH']]
    futures['FutDeltaUSD'] = futures['positionAmt']
    futures.loc['BTC', 'FutDeltaUSD'] *= 100
    futures.loc['ETH', 'FutDeltaUSD'] *= 10
    futures['FutDelta'] = futures['FutDeltaUSD']
    futures.loc['BTC', 'FutDelta'] /= self.spotBTC
    futures.loc['ETH', 'FutDelta'] /= self.spotETH
    notional = futures['FutDeltaUSD'].abs().sum()
    #####
    payments = pd.DataFrame(self.api.dapiPrivate_get_income({'incomeType': 'FUNDING_FEE', 'startTime': getYest() * 1000}))
    if len(payments)==0:
      prevIncome = 0
      oneDayIncome = 0
    else:
      cl.dfSetFloat(payments, 'income')
      payments = payments[['USD_PERP' in z for z in payments['symbol']]]
      payments['Ccy'] = [z[:3] for z in payments['symbol']]
      payments = payments.set_index('Ccy').loc[['BTC', 'ETH']]
      payments['incomeUSD'] = payments['income']
      payments.loc['BTC', 'incomeUSD'] *= self.spotBTC
      payments.loc['ETH', 'incomeUSD'] *= self.spotETH
      payments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in payments['time']]
      payments = payments.set_index('date')
      prevIncome = payments.loc[payments.index[-1]]['incomeUSD'].sum()
      oneDayIncome = payments['incomeUSD'].sum()
    prevAnnRet = prevIncome * 3 * 365 / notional
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    nav = bal.loc['BTC', 'SpotDelta'] * self.spotBTC + bal.loc['ETH', 'SpotDelta'] * self.spotETH
    liqBTC = float(futures.loc['BTC', 'liquidationPrice']) / float(futures.loc['BTC', 'markPrice'])
    liqETH = float(futures.loc['ETH', 'liquidationPrice']) / float(futures.loc['ETH', 'markPrice'])
    #####
    self.spotDeltaBTC = spotDeltaBTC
    self.spotDeltaETH = spotDeltaETH
    self.futures = futures
    self.prevIncome = prevIncome
    self.prevAnnRet = prevAnnRet
    self.oneDayIncome = oneDayIncome
    self.oneDayAnnRet = oneDayAnnRet
    self.nav = nav
    self.liqBTC = liqBTC
    self.liqETH = liqETH

  ####
  # BT
  ####
  def btInit(self):
    futures = pd.DataFrame(self.api.fapiPrivate_get_positionrisk())
    cl.dfSetFloat(futures, ['positionAmt','unRealizedProfit'])
    futures = futures.set_index('symbol').loc[['BTCUSDT', 'ETHUSDT']]
    futures['Ccy'] = [z[:3] for z in futures.index]
    futures=futures.set_index('Ccy')
    futures['FutDelta'] = futures['FutDeltaUSD'] = futures['positionAmt']
    futures.loc['BTC', 'FutDeltaUSD'] *= self.spotBTC
    futures.loc['ETH', 'FutDeltaUSD'] *= self.spotETH
    notional = futures['FutDeltaUSD'].abs().sum()
    #####
    payments = pd.DataFrame(self.api.fapiPrivate_get_income({'incomeType': 'FUNDING_FEE', 'startTime': getYest() * 1000}))
    if len(payments)==0:
      prevIncome = 0
      oneDayIncome = 0
    else:
      cl.dfSetFloat(payments, 'income')
      payments = payments[['USD_PERP' in z for z in payments['symbol']]]
      payments['Ccy'] = [z[:3] for z in payments['symbol']]
      payments = payments.set_index('Ccy').loc[['BTC', 'ETH']]
      payments['incomeUSD'] = payments['income']
      payments.loc['BTC', 'incomeUSD'] *= self.spotBTC
      payments.loc['ETH', 'incomeUSD'] *= self.spotETH
      payments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in payments['time']]
      payments = payments.set_index('date')
      prevIncome = payments.loc[payments.index[-1]]['incomeUSD'].sum()
      oneDayIncome = payments['incomeUSD'].sum()
    prevAnnRet = prevIncome * 3 * 365 / notional
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    nav = float(pd.DataFrame(self.api.fapiPrivate_get_balance()).set_index('asset').loc['USDT', 'balance'])*self.spotUSDT + futures['unRealizedProfit'].sum()
    liqBTC = float(futures.loc['BTC', 'liquidationPrice']) / float(futures.loc['BTC', 'markPrice'])
    liqETH = float(futures.loc['ETH', 'liquidationPrice']) / float(futures.loc['ETH', 'markPrice'])
    #####
    self.spotDeltaBTC = 0
    self.spotDeltaETH = 0
    self.futures = futures
    self.prevIncome = prevIncome
    self.prevAnnRet = prevAnnRet
    self.oneDayIncome = oneDayIncome
    self.oneDayAnnRet = oneDayAnnRet
    self.nav = nav
    self.liqBTC = liqBTC
    self.liqETH = liqETH

  ####
  # DB
  ####
  def dbInit(self):
    def getOneDayIncome(api, ccy, spot):
      df = pd.DataFrame(api.private_get_get_settlement_history_by_currency({'currency': ccy})['result']['settlements'])
      if len(df) == 0: return 0
      cl.dfSetFloat(df, 'funding')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['timestamp']]
      df = df.set_index('date').sort_index()
      if df.index[-1] >= (datetime.datetime.now() - pd.DateOffset(days=1)):
        return df['funding'].iloc[-1] * spot
      else:
        return 0
    #####
    asBTC = self.api.private_get_get_account_summary({'currency': 'BTC'})['result']
    asETH = self.api.private_get_get_account_summary({'currency': 'ETH'})['result']
    spotDeltaBTC = float(asBTC['equity'])
    spotDeltaETH = float(asETH['equity'])
    futures = pd.DataFrame([['BTC', self.spotBTC, cl.dbGetFutPos(self.api, 'BTC')], ['ETH', self.spotETH, cl.dbGetFutPos(self.api, 'ETH')]], columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
    futures['FutDelta'] = futures['FutDeltaUSD'] / futures['Spot']
    notional = futures['FutDeltaUSD'].abs().sum()
    #####
    oneDayIncome = getOneDayIncome(self.api, 'BTC', self.spotBTC) + getOneDayIncome(self.api, 'ETH', self.spotETH)
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    nav = spotDeltaBTC * self.spotBTC + spotDeltaETH * self.spotETH
    liqBTC = float(asBTC['estimated_liquidation_ratio'])
    liqETH = float(asETH['estimated_liquidation_ratio'])
    #####
    self.spotDeltaBTC = spotDeltaBTC
    self.spotDeltaETH = spotDeltaETH
    self.futures = futures
    self.oneDayIncome = oneDayIncome
    self.oneDayAnnRet = oneDayAnnRet
    self.nav = nav
    self.liqBTC = liqBTC
    self.liqETH = liqETH

  ####
  # KF
  ####
  def kfInit(self):
    def getLog(api, futures):
      ffn = os.path.dirname(cl.__file__) + '\\data\kfLog.csv'
      api.get_account_log(ffn)
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
    accounts = self.api.query('accounts')['accounts']
    spotDeltaBTC = accounts['fi_xbtusd']['auxiliary']['pv'] + accounts['cash']['balances']['xbt']
    spotDeltaETH = accounts['fi_ethusd']['auxiliary']['pv'] + accounts['cash']['balances']['eth']
    futures = pd.DataFrame([['BTC', self.spotBTC, accounts['fi_xbtusd']['balances']['pi_xbtusd']], \
                            ['ETH', self.spotETH, accounts['fi_ethusd']['balances']['pi_ethusd']]], \
                           columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
    futures['FutDelta'] = futures['FutDeltaUSD'] / futures['Spot']
    notional = futures['FutDeltaUSD'].abs().sum()
    #####
    if IS_IP_WHITELIST:
      log = getLog(self.api, futures)
      prevIncome = log.loc[log.index[-1]]['fundingUSD'].sum()
      oneDayIncome = log['fundingUSD'].sum()
    else:
      log = None
      tickers = cl.kfGetTickers(self.api)
      oneDayIncome = -futures.loc['BTC', 'FutDeltaUSD'] * cl.kfGetEstFunding1(self.api, 'BTC', tickers) / 365
      oneDayIncome -= futures.loc['ETH', 'FutDeltaUSD'] * cl.kfGetEstFunding1(self.api, 'ETH', tickers) / 365
      prevIncome = oneDayIncome / 6
    prevAnnRet = prevIncome * 6 * 365 / notional
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    nav = spotDeltaBTC * self.spotBTC + spotDeltaETH * self.spotETH
    liqBTC = accounts['fi_xbtusd']['triggerEstimates']['im'] / self.spotBTC
    liqETH = accounts['fi_ethusd']['triggerEstimates']['im'] / self.spotETH
    #####
    self.spotDeltaBTC = spotDeltaBTC
    self.spotDeltaETH = spotDeltaETH
    self.futures = futures
    self.log=log
    self.prevIncome=prevIncome
    self.prevAnnRet=prevAnnRet
    self.oneDayIncome = oneDayIncome
    self.oneDayAnnRet = oneDayAnnRet
    self.nav = nav
    self.liqBTC = liqBTC
    self.liqETH = liqETH
    
  ####
  # KR
  ####
  def krInit(self):
    def getBal(bal, ccy):
      try:
        return float(bal[ccy])
      except:
        return 0
    #####
    bal = self.api.private_post_balance()['result']
    spotDeltaBTC = getBal(bal, 'XXBT')
    spotDeltaETH = getBal(bal, 'XETH')
    spotDeltaEUR = getBal(bal, 'ZEUR')
    spotDf = pd.DataFrame([['BTC', spotDeltaBTC * self.spotBTC], ['ETH', spotDeltaETH * self.spotETH]], columns=['Ccy', 'SpotUSD']).set_index('Ccy')
    #####
    positions = pd.DataFrame(self.api.private_post_openpositions()['result']).transpose().set_index('pair')
    if not all([z in ['XXBTZUSD', 'XXBTZEUR'] for z in positions.index]):
      print('Invalid Kraken pair detected!')
      sys.exit(1)
    cl.dfSetFloat(positions, ['vol', 'vol_closed', 'time'])
    positions['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in positions['time']]
    positions['volNetBTC'] = positions['vol'] - positions['vol_closed']
    positions['volNetUSD'] = positions['volNetBTC'] * self.spotBTC
    spotDeltaBTC += positions['volNetBTC'].sum()
    if 'XXBTZEUR' in positions.index:
      spotDeltaEUR -= positions.loc['XXBTZEUR', 'volNetBTC'].sum() * float(self.api.public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
    notional = positions['volNetUSD'].abs().sum()
    #####
    # mdbUSD=Margin Delta BTC in USD
    xxbtzeur_volNetUSD_sum = positions.loc['XXBTZEUR', 'volNetUSD'].sum() if 'XXBTZEUR' in positions.index else 0
    mdbUSDDf = pd.DataFrame([['USD', positions.loc['XXBTZUSD', 'volNetUSD'].sum()], ['EUR', xxbtzeur_volNetUSD_sum]], columns=['Ccy', 'MDBU']).set_index('Ccy')
    #####
    oneDayIncome = -mdbUSDDf['MDBU'].sum() * 0.0006
    oneDayAnnRet = oneDayIncome * 365 / notional
    #####
    tradeBal = self.api.private_post_tradebalance()['result']
    nav = float(tradeBal['e'])
    #####
    freeMargin = float(tradeBal['mf'])
    liqBTC = 1 - freeMargin / (spotDeltaBTC * self.spotBTC)
    #####
    self.spotDeltaBTC = spotDeltaBTC
    self.spotDeltaETH = spotDeltaETH
    self.spotDeltaEUR = spotDeltaEUR
    self.spotDf=spotDf
    self.mdbUSDDf=mdbUSDDf
    self.futures = getDummyFutures()
    self.oneDayIncome = oneDayIncome
    self.oneDayAnnRet = oneDayAnnRet
    self.nav = nav
    self.liqBTC = liqBTC

  def krPrintBorrow(self, nav):
    zPctNAV = '('+str(round(-self.mdbUSDDf['MDBU'].sum() / nav*100))+'%)'
    suffix='(spot BTC/ETH: $'
    suffix+= str(round(self.spotDf.loc['BTC', 'SpotUSD'] / 1000)) + 'K/$'
    suffix += str(round(self.spotDf.loc['ETH', 'SpotUSD'] / 1000)) + 'K; XXBTZUSD/XXBTZEUR: $'
    suffix += str(round(self.mdbUSDDf.loc['USD','MDBU']/1000))+'K/$'
    suffix += str(round(self.mdbUSDDf.loc['EUR','MDBU']/1000))+'K)'
    print(('KR' + str(self.n) + ' USD/EUR est borrow rate: ').rjust(41) + ('22% p.a. ($' + str(round(-self.mdbUSDDf['MDBU'].sum()/1000)) + 'K) '+zPctNAV).ljust(27)+suffix)

  ####
  # CB
  ####
  def cbInit(self):
    bal = self.api.fetch_balance()
    spotDeltaBTC = bal['BTC']['total']
    spotDeltaETH = bal['ETH']['total']
    nav = spotDeltaBTC * spotBTC + spotDeltaETH * spotETH
    self.spotDeltaBTC=spotDeltaBTC
    self.spotDeltaETH=spotDeltaETH
    self.futures = getDummyFutures()
    self.oneDayIncome = 0
    self.nav=nav

####################################################################################################

######
# Init
######
cl.printHeader('CryptoReporter')
ftx=cl.ftxCCXTInit()
ftxWallet=cl.ftxGetWallet(ftx)
spotBTC = ftxWallet.loc['BTC','spot']
spotETH = ftxWallet.loc['ETH','spot']
spotFTT = ftxWallet.loc['FTT','spot']
spotUSDT = ftxWallet.loc['USDT','spot']
spotEUR = cl.ftxGetSpotEUR(ftx)
#####
ftxCore = core('ftx',spotBTC,spotETH,spotFTT=spotFTT)
bbCore = core('bb',spotBTC,spotETH)
cbCore = core('cb',spotBTC,spotETH)
objs=[ftxCore,bbCore,cbCore]
if CR_IS_ADVANCED:
  bnCore = core('bn', spotBTC, spotETH)
  btCore = core('bt', spotBTC, spotETH,spotUSDT=spotUSDT)
  dbCore = core('db', spotBTC, spotETH)
  kfCore = core('kf', spotBTC, spotETH)
  krCores = []
  for i in range(CR_N_KR_ACCOUNTS):
    krCores.append(core('kr',spotBTC, spotETH,spotEUR=spotEUR,n=i+1))
  objs.extend([bnCore,btCore,dbCore,kfCore]+krCores)
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
  externalEURNAV = get_EXTERNAL_EUR_NAV(spotEUR)
  nav+=externalEURNAV

########
# Output
########
z=('NAV as of '+cl.getCurrentTime()+': $').rjust(42)+str(round(nav))
z+=' (FTX: $' + str(round(ftxCore.nav/1000)) + 'K'
z+=' / BB: $' + str(round(bbCore.nav/1000)) + 'K'
if CR_IS_ADVANCED:
  z+=' / BN: $' + str(round(bnCore.nav/1000)) + 'K'
  z+=' / BT: $' + str(round(btCore.nav/1000)) + 'K'
  z += ' / DB: $' + str(round(dbCore.nav / 1000)) + 'K'
  z += ' / KF: $' + str(round(kfCore.nav / 1000)) + 'K'
  for krCore in krCores:
    z+= ' / KR' + str(krCore.n)+': $'+str(round(krCore.nav/1000))+'K'
z+=' / CB: $' + str(round(cbCore.nav/1000)) + 'K'
if CR_IS_ADVANCED:
  z+=' / EUR: $' + str(round(externalEURNAV/1000))+'K'
z+=')'
print(termcolor.colored(z,'blue'))
#####
z='BTC='+str(round(spotBTC,1))+ ' / ETH='+str(round(spotETH,1))+ ' / FTT='+str(round(spotFTT,1)) + ' / USDT=' + str(round(spotUSDT,4))
if CR_IS_ADVANCED:
  z+=' / EUR='+str(round(spotEUR,4))
print(termcolor.colored('24h income: $'.rjust(42)+(str(round(oneDayIncome))+' ('+str(round(oneDayIncome*365/nav*100))+'% p.a.)').ljust(27),'blue')+z)
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
  btCore.printIncomes()
  btCore.printFunding('BTC')
  btCore.printFunding('ETH')
  btCore.printLiq()
  print()
  #####
  dbCore.printIncomes()
  dbCore.printFunding('BTC')
  dbCore.printFunding('ETH')
  dbCore.printLiq()
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
if CR_IS_ADVANCED:
  spotDeltaEUR=0
  for krCore in krCores:
    spotDeltaEUR+=krCore.spotDeltaEUR
  printEURDeltas(spotEUR,spotDeltaEUR)
