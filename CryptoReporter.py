from CryptoParams import *
import CryptoLib as cl
from joblib import Parallel, delayed
import pandas as pd
import numpy as np
import datetime
import time
import termcolor
import sys

#########
# Configs
#########
MAIN_CCY_DICT =dict({'BTC':1,'ETH':1,'XRP':4,'FTT':1,'USDT':4,'EUR':4})                               # Values are nDigits for display
AG_CCY_DICT = dict({'BTC': EXTERNAL_BTC_DELTA, 'ETH': EXTERNAL_ETH_DELTA, 'XRP': EXTERNAL_XRP_DELTA}) # Values are external deltas
FTX_FLOWS_CCYS = ['BTC','ETH','XRP','USD','USDT']

###########
# Functions
###########
def getNAVStr(name, nav):
  return name + ': $' + str(round(nav/1000)) + 'K'

def getYest():
  return int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))))

def krPrintAll(krCores,nav):
  # Incomes
  zs = []
  prefixes = []
  for krCore in krCores:
    zs.append('$' + str(round(krCore.oneDayIncome)) + ' (' + str(round(krCore.oneDayAnnRet * 100)) + '% p.a.)')
    prefixes.append('KR' + str(krCore.n))
  print(termcolor.colored(('/'.join(prefixes) + ' 24h rollover fees: ').rjust(41) + ' / '.join(zs), 'blue'))
  #####
  # Borrows
  for krCore in krCores:
    krCore.krPrintBorrow(nav)
  #####
  # Liq
  zs = []
  prefixes = []
  for krCore in krCores:
    zs.append('never' if (krCore.liqBTC <= 0 or krCore.liqBTC > 10) else str(round(krCore.liqBTC * 100)) + '%')
    prefixes.append('KR' + str(krCore.n))
  print(termcolor.colored(('/'.join(prefixes) + ' liquidation (BTC): ').rjust(41) + '/'.join(zs) + ' (of spot)', 'red'))
  print()

def printAllDual(core1, core2):
  if core1.exch == 'dummy' and core2.exch == 'dummy': return
  if core1.exch == 'dummy':
    core2.printAll()
  elif core2.exch == 'dummy':
    core1.printAll()
  else:
    n=120
    print(core1.incomesStr.ljust(n+9) + core2.incomesStr)
    for ccy in sorted(set(core1.validCcys).intersection(core2.validCcys)):
      print(core1.fundingStrDict[ccy].ljust(n) + core2.fundingStrDict[ccy])
    for ccy in sorted(np.setdiff1d(core1.validCcys, core2.validCcys)):  # In core1 but not core2
      print(core1.fundingStrDict[ccy])
    for ccy in sorted(np.setdiff1d(core2.validCcys, core1.validCcys)):  # In core2 but not core1
      print(''.ljust(n) + core2.fundingStrDict[ccy])
    print(core1.liqStr.ljust(n+9) + core2.liqStr)
    print()

def printDeltas(ccy,spotDict,spotDelta,futDelta):
  spot = spotDict[ccy]
  netDelta=spotDelta+futDelta
  nDigits=None if ccy=='XRP' else 1
  z=(ccy+' spot/fut/net delta: ').rjust(41)+(str(round(spotDelta,nDigits))+'/'+str(round(futDelta,nDigits))+'/'+str(round(netDelta,nDigits))).ljust(27) + \
    '($' + str(round(spotDelta * spot/1000)) + 'K/$' + str(round(futDelta * spot/1000)) + 'K/$' + str(round(netDelta * spot/1000)) + 'K)'
  print(termcolor.colored(z,'red'))

def printEURDeltas(krCores, spotDict):
  spotDelta=0
  for krCore in krCores:
    spotDelta+=krCore.spots.loc['EUR','SpotDelta']
  if spotDelta == 0 and EXTERNAL_EUR_DELTA == 0: return
  netDelta=spotDelta+EXTERNAL_EUR_DELTA
  z='EUR ext/impl/net delta: '.rjust(41) + (str(round(EXTERNAL_EUR_DELTA/1000)) + 'K/' + str(round(spotDelta/1000)) + 'K/' + str(round(netDelta/1000))+'K').ljust(27) + \
    '($' + str(round(EXTERNAL_EUR_DELTA * spotDict['EUR'] / 1000)) + 'K/$' + str(round(spotDelta * spotDict['EUR'] / 1000)) + 'K/$' + str(round(netDelta * spotDict['EUR'] / 1000)) + 'K)'
  print(termcolor.colored(z,'red'))

def printUSDTDeltas(ftxCore,spotDict,usdtCoreList):
  realDelta_USD=ftxCore.wallet.loc['USDT','usdValue']+EXTERNAL_USDT_DELTA*spotDict['USDT']
  implDelta_USD=0
  for core in usdtCoreList:
    realDelta_USD+=core.nav
    implDelta_USD-=core.futures['FutDeltaUSD'].sum()
  netDelta_USD=realDelta_USD+implDelta_USD
  realDelta=realDelta_USD/spotDict['USDT']
  implDelta=implDelta_USD/spotDict['USDT']
  netDelta=realDelta+implDelta
  z1=str(round(realDelta/1000))+'K/'+str(round(implDelta/1000))+'K/'+str(round(netDelta/1000))+'K'
  z2='($'+str(round(realDelta_USD/1000))+'K/$'+str(round(implDelta_USD/1000))+'K/$'+ str(round(netDelta_USD/1000))+'K)'
  print(termcolor.colored('USDT real/impl/net delta: '.rjust(41)+z1.ljust(27)+z2, 'red'))

####################################################################################################

#########
# Classes
#########
class core:
  def __init__(self, exch, spotDict, n=None):
    self.exch = exch
    self.name = exch.upper()
    self.spotDict = spotDict
    if n is not None:
      self.n = n
      self.name += str(n)
    #####
    self.validCcys = []
    for ccy in INT_CCY_DICT.keys():
      if exch in INT_CCY_DICT[ccy]['exch']:
        self.validCcys.append(ccy)
    #####
    ccyList = list(INT_CCY_DICT.keys())
    if exch=='kr': ccyList.append('EUR')
    zeroes = [0] * len(ccyList)
    self.spots = pd.DataFrame({'Ccy': ccyList, 'SpotDelta': zeroes, 'SpotDeltaUSD':zeroes}).set_index('Ccy')
    self.futures = pd.DataFrame({'Ccy':ccyList, 'FutDelta': zeroes, 'FutDeltaUSD':zeroes}).set_index('Ccy')
    self.oneDayIncome = 0
    self.nav = 0

  def run(self):
    if self.exch=='dummy': return
    if self.exch=='ftx':
      self.ftxInit()
    elif self.exch=='bb':
      self.bbInit()
    elif self.exch=='bbt':
      self.bbtInit()
    elif self.exch=='bn':
      self.bnInit()
    elif self.exch=='bnt':
      self.bntInit()
    elif self.exch=='db':
      self.dbInit()
    elif self.exch=='kf':
      self.kfInit()
    elif self.exch=='kr':
      self.krInit()
    if not self.exch == 'kr':
      self.incomesStr = self.getIncomesStr()
      self.fundingStrDict=dict()
      for ccy in self.validCcys:
        self.fundingStrDict[ccy] = self.getFundingStr(ccy)
      self.liqStr = self.getLiqStr()

  def calcSpotDeltaUSD(self):
    for ccy in self.validCcys:
      self.spots.loc[ccy,'SpotDeltaUSD']=self.spots.loc[ccy,'SpotDelta']*self.spotDict[ccy]

  def calcFuturesDeltaUSD(self):
    for ccy in self.validCcys:
      self.futures.loc[ccy, 'FutDeltaUSD'] = self.futures.loc[ccy, 'FutDelta'] * self.spotDict[ccy]
    self.futNotional = self.futures['FutDeltaUSD'].abs().sum()

  def getIncomesStr(self):
    z1 = '$' + str(round(self.oneDayIncome)) + ' (' + str(round(self.oneDayAnnRet * 100)) + '% p.a.)'
    if self.exch == 'db':
      return termcolor.colored('DB 24h funding income: '.rjust(41) + z1, 'blue')
    else:
      zPrev  = '4h' if self.exch == 'kf' else 'prev'
      z2 = '$' + str(round(self.prevIncome)) + ' (' + str(round(self.prevAnnRet * 100)) + '% p.a.)'
      return termcolor.colored((self.exch.upper() + ' 24h/'+zPrev+' funding income: ').rjust(41) + z1 + ' / ' + z2, 'blue')

  def getFundingStr(self,ccy):
    def calcFunding(s,mult):
      oneDayFunding = s.mean() * mult
      prevFunding = s[-1] * mult
      return oneDayFunding,prevFunding
    #####
    def bbClean(df):
      for i in range(len(df)):
        if 'Sell' in df.iloc[i]['order_id']:
          df.loc[df.index[i], 'fee_rate'] *= -1
      return df
    #####
    if self.exch=='ftx':
      oneDayFunding,prevFunding=calcFunding(self.payments[self.payments['future'] == ccy + '-PERP']['rate'],24*365)
    elif self.exch == 'bb':
      df = bbClean(self.payments[self.payments['symbol'] == ccy + 'USD'].copy())
      oneDayFunding,prevFunding=calcFunding(df['fee_rate'],3*365)
    elif self.exch =='bbt':
      df = bbClean(self.payments[self.payments['symbol'] == ccy + 'USDT'].copy())
      oneDayFunding, prevFunding = calcFunding(df['fee_rate'], 3 * 365)
    elif self.exch=='bn':
      oneDayFunding,prevFunding=calcFunding(self.payments[self.payments['symbol'] == ccy + 'USD_PERP']['fundingRate'],3*365)
    elif self.exch=='bnt':
      oneDayFunding, prevFunding = calcFunding(self.payments[self.payments['symbol'] == ccy + 'USDT']['fundingRate'], 3 * 365)
    elif self.exch=='db':
      oneDayFunding = self.estFundingDict[ccy+'24H']
      prevFunding = self.estFundingDict[ccy+'8H']
    elif self.exch=='kf':
      oneDayFunding, prevFunding = calcFunding(self.payments[self.payments['Ccy'] == ccy]['rate'],3*365)
    #####
    prefix = self.exch.upper() + ' ' + ccy + ' 24h/'
    if self.exch=='db':
      prefix+='8h'
    else:
      prefix+='prev'
    prefix+='/est'
    if self.exch in ['bb','bbt','kf']:
      prefix += '1/est2'
    prefix += ' funding rate:'
    #####
    body = str(round(oneDayFunding * 100)) + '%/'
    body += str(round(prevFunding * 100)) + '%/'
    body += str(round(self.estFundingDict[ccy] * 100)) + '%'
    if self.exch in ['bb','bbt','kf']:
      body += '/' + str(round(self.estFunding2Dict[ccy] * 100)) + '%'
    body += ' p.a.'
    #####
    spotDeltaUSD=self.spots.loc[ccy,'SpotDeltaUSD']
    futDeltaUSD=self.futures.loc[ccy, 'FutDeltaUSD']
    netDeltaUSD=spotDeltaUSD+futDeltaUSD
    if self.exch in ['bbt','bnt']:
      suffix = '(fut delta: $' + str(round(futDeltaUSD / 1000)) + 'K)'
    else:
      suffix = '(spot/fut/net delta: $' + str(round(spotDeltaUSD/1000)) + 'K/$' + str(round(futDeltaUSD/1000)) + 'K/$' + str(round(netDeltaUSD/1000))+'K)'
    return prefix.rjust(40) + ' ' + body.ljust(27) + suffix

  def getLiqStr(self):
    if self.exch in ['ftx','bbt','bnt']:
      z = 'never' if (self.liq <= 0 or self.liq > 10) else str(round(self.liq * 100)) + '% (of spot)'
      zRet=termcolor.colored((self.exch.upper()+' liquidation (parallel shock): ').rjust(41) + z, 'red')
      if self.exch=='ftx':
        z = str(round(self.mf * 100, 1)) + '% (vs. ' + str(round(self.mmReq * 100, 1)) + '% limit) / $' + str(round(self.freeCollateral))
        zRet+='\n'+termcolor.colored('FTX margin fraction/free collateral: '.rjust(41) + z, 'red')
    else:
      zBTC = 'never' if (self.liqDict['BTC'] <= 0 or self.liqDict['BTC'] >= 10) else str(round(self.liqDict['BTC'] * 100)) + '%'
      zETH = 'never' if (self.liqDict['ETH'] <= 0 or self.liqDict['ETH'] >= 10) else str(round(self.liqDict['ETH'] * 100)) + '%'
      if 'XRP' in self.validCcys:
        zXRP = 'never' if (self.liqDict['XRP'] <= 0 or self.liqDict['XRP'] >= 10) else str(round(self.liqDict['XRP'] * 100)) + '%'
        zRet = termcolor.colored((self.exch.upper() + ' liquidation (BTC/ETH/XRP): ').rjust(41) + zBTC + '/' + zETH + '/' + zXRP + ' (of spot)', 'red')
      else:
        zRet = termcolor.colored((self.exch.upper() + ' liquidation (BTC/ETH): ').rjust(41) + zBTC + '/' + zETH + ' (of spot)', 'red')
    return zRet

  def printAll(self):
    if self.exch=='dummy': return
    print(self.incomesStr)
    for ccy in self.validCcys:
      print(self.fundingStrDict[ccy])
    print(self.liqStr)
    print()

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
    def getBorrowsLoans(ccy):
      start_time = getYest()
      borrows = cleanBorrows(ccy, pd.DataFrame(self.api.private_get_spot_margin_borrow_history({'limit': 1000, 'start_time': start_time})['result']))
      loans = cleanBorrows(ccy, pd.DataFrame(self.api.private_get_spot_margin_lending_history({'limit': 1000, 'start_time': start_time})['result']))
      cl.dfSetFloat(borrows, 'cost')
      cl.dfSetFloat(loans, 'proceeds')
      prevBorrow = borrows.iloc[-1]['cost'] if borrows.index[-1] == self.payments.index[-1] else 0
      prevLoan = loans.iloc[-1]['proceeds'] if loans.index[-1] == self.payments.index[-1] else 0
      prevFlows = (prevLoan - prevBorrow) * self.spotDict[ccy]
      absBalance = abs(self.wallet.loc[ccy, 'total'])
      prevFlowsAnnRet = prevFlows * 24 * 365 / absBalance
      oneDayFlows = (loans['proceeds'].sum() - borrows['cost'].sum()) * self.spotDict[ccy]
      oneDayFlowsAnnRet = oneDayFlows * 365 / absBalance
      d=dict()
      d['prevFlows']=prevFlows
      d['prevFlowsAnnRet']=prevFlowsAnnRet
      d['oneDayFlows']=oneDayFlows
      d['oneDayFlowsAnnRet']=oneDayFlowsAnnRet
      return d
    ######
    self.api = cl.ftxCCXTInit()
    self.wallet = cl.ftxGetWallet(ftx)
    for ccy in self.validCcys:
      self.spots.loc[ccy,'SpotDelta'] = self.wallet.loc[ccy,'total']
    self.calcSpotDeltaUSD()
    ######
    info = self.api.private_get_account()['result']
    futs = pd.DataFrame(info['positions']).set_index('future')
    cl.dfSetFloat(futs, 'size')
    for ccy in self.validCcys:
      ccy2=ccy+'-PERP'
      mult = -1 if futs.loc[ccy2, 'side']=='sell' else 1
      self.futures.loc[ccy,'FutDelta']=futs.loc[ccy2,'size']*mult
    self.calcFuturesDeltaUSD()
    ######
    pmts = pd.DataFrame(self.api.private_get_funding_payments({'limit': 1000, 'start_time': getYest()})['result'])
    pmts = pmts.set_index('future', drop=False).loc[[z+'-PERP' for z in self.validCcys]].set_index('time')
    cl.dfSetFloat(pmts, ['payment', 'rate'])
    pmts = pmts.sort_index()
    self.payments = pmts
    #####
    self.prevIncome = -self.payments.loc[self.payments.index[-1]]['payment'].sum()
    self.prevAnnRet = self.prevIncome * 24 * 365 / self.futNotional
    self.oneDayIncome = -self.payments['payment'].sum()
    self.oneDayAnnRet = self.oneDayIncome * 365 / self.futNotional
    #####
    self.oneDayFlows=0
    self.flowsDict=dict()
    for ccy in FTX_FLOWS_CCYS:
      d=getBorrowsLoans(ccy)
      self.flowsDict[ccy]=d
      self.oneDayFlows+=d['oneDayFlows']
    #####
    self.nav = self.wallet['usdValue'].sum()
    self.mf = float(info['marginFraction'])
    self.mmReq = float(info['maintenanceMarginRequirement'])
    totalPositionNotional = self.nav / self.mf
    cushion = (self.mf - self.mmReq) * totalPositionNotional
    totalDelta = self.wallet.loc[self.validCcys, 'usdValue'].sum() + self.futures['FutDeltaUSD'].sum()
    self.liq = 1 - cushion / totalDelta
    self.freeCollateral = float(info['freeCollateral'])
    #####    
    self.estFundingDict=dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.ftxGetEstFunding(self.api, ccy)

  def ftxPrintFlowsSummary(self,ccy):
    d = self.flowsDict[ccy]
    z1 = '$' + str(round(d['oneDayFlows'])) + ' (' + str(round(d['oneDayFlowsAnnRet'] * 100)) + '% p.a.)'
    z2 = '$' + str(round(d['prevFlows'])) + ' (' + str(round(d['prevFlowsAnnRet'] * 100)) + '% p.a.)'
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
    def getPayments(ccy):
      n = 0
      df = pd.DataFrame()
      while True:
        n += 1
        tl = self.api.v2_private_get_execution_list({'symbol': ccy + 'USD', 'start_time': getYest() * 1000, 'limit': 1000, 'page': n})['result']['trade_list']
        if tl is None:
          break
        else:
          df = df.append(pd.DataFrame(tl))
      return df.set_index('symbol', drop=False)
    #####
    self.api = cl.bbCCXTInit()
    self.wallet=pd.DataFrame(self.api.v2_private_get_wallet_balance()['result']).transpose()
    cl.dfSetFloat(self.wallet,'equity')
    for ccy in self.validCcys:
      self.spots.loc[ccy,'SpotDelta']=self.wallet.loc[ccy,'equity']
    self.calcSpotDeltaUSD()
    #####
    self.liqDict=dict()
    futs = self.api.v2_private_get_position_list()['result']
    futs = pd.DataFrame([pos['data'] for pos in futs]).set_index('symbol')
    cl.dfSetFloat(futs, ['size','liq_price','position_value','unrealised_pnl'])
    for ccy in self.validCcys:
      ccy2=ccy+'USD'
      mult = -1 if futs.loc[ccy2,'side']=='Sell' else 1
      self.futures.loc[ccy, 'FutDelta'] = futs.loc[ccy2, 'size'] * mult / self.spotDict[ccy]
      self.liqDict[ccy] = futs.loc[ccy2,'liq_price'] / cl.bbGetMid(self.api,ccy)
    self.calcFuturesDeltaUSD()
    #####
    pmts = pd.DataFrame()
    for ccy in self.validCcys:
      pmts = pmts.append(getPayments(ccy))
    cl.dfSetFloat(pmts, ['fee_rate', 'exec_fee'])
    pmts['incomeUSD'] = -pmts['exec_fee']
    for ccy in self.validCcys:
      pmts.loc[ccy+'USD', 'incomeUSD'] *= self.spotDict[ccy]
    pmts = pmts[pmts['exec_type'] == 'Funding']
    pmts['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in pmts['trade_time_ms']]
    pmts = pmts.set_index('date')
    self.payments = pmts
    #####
    self.prevIncome = self.payments.loc[self.payments.index[-1]]['incomeUSD'].sum()
    self.prevAnnRet = self.prevIncome * 3 * 365 / self.futNotional
    self.oneDayIncome = self.payments['incomeUSD'].sum()
    self.oneDayAnnRet = self.oneDayIncome * 365 / self.futNotional
    #####
    self.nav=self.spots['SpotDeltaUSD'].sum()
    #####
    self.estFundingDict = dict()
    self.estFunding2Dict = dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.bbGetEstFunding1(self.api, ccy)
      self.estFunding2Dict[ccy] = cl.bbGetEstFunding2(self.api, ccy)

  #####
  # BBT
  #####
  def bbtInit(self):
    self.api = cl.bbCCXTInit()
    for ccy in self.validCcys:
      self.futures.loc[ccy, 'FutDelta']=cl.bbtGetFutPos(self.api,ccy)
    self.calcFuturesDeltaUSD()
    #####
    pmts=pd.DataFrame()
    for ccy in self.validCcys:
      pmts=pmts.append(pd.DataFrame(self.api.private_linear_get_trade_execution_list({'symbol': ccy + 'USDT', 'start_time': getYest() * 1000, 'exec_type':'Funding', 'limit': 1000})['result']['data']).set_index('symbol',drop=False))
    cl.dfSetFloat(pmts, ['fee_rate', 'exec_fee'])
    pmts['incomeUSD'] = -pmts['exec_fee'] * self.spotDict['USDT']
    pmts['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in pmts['trade_time_ms']]
    pmts = pmts.set_index('date').sort_index()
    self.payments = pmts
    #####
    self.prevIncome = self.payments.loc[self.payments.index[-1]]['incomeUSD'].sum()
    self.prevAnnRet = self.prevIncome * 3 * 365 / self.futNotional
    self.oneDayIncome = self.payments['incomeUSD'].sum()
    self.oneDayAnnRet = self.oneDayIncome * 365 / self.futNotional
    #####
    walletUSDT = self.api.v2_private_get_wallet_balance({'coin': 'USDT'})['result']['USDT']
    self.nav=float(walletUSDT['equity'])*self.spotDict['USDT']
    cushion=float(walletUSDT['available_balance'])*self.spotDict['USDT']
    totalDelta = self.futures['FutDeltaUSD'].sum()
    self.liq = 1 - cushion / totalDelta
    #####
    self.estFundingDict = dict()
    self.estFunding2Dict = dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.bbtGetEstFunding1(self.api, ccy)
      self.estFunding2Dict[ccy] = cl.bbtGetEstFunding2(self.api, ccy)

  ####
  # BN
  ####
  def bnInit(self):
    def getPayments(ccy):
      df = pd.DataFrame(self.api.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP', 'startTime': getYest() * 1000}))
      cl.dfSetFloat(df, 'fundingRate')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
      df = df.set_index('date').sort_index()
      return df
    #####
    def getIncomes():
      df = pd.DataFrame(self.api.dapiPrivate_get_income({'incomeType': 'FUNDING_FEE', 'startTime': getYest() * 1000}))
      cl.dfSetFloat(df, 'income')
      df = df[['USD_PERP' in z for z in df['symbol']]]
      df['Ccy'] = [z[:3] for z in df['symbol']]
      df = df.set_index('Ccy').loc[self.validCcys]
      df['incomeUSD'] = df['income']
      for ccy in self.validCcys:
        df.loc[ccy, 'incomeUSD'] *= self.spotDict[ccy]
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['time']]
      df = df.set_index('date')
      prevIncome = df.loc[df.index[-1]]['incomeUSD'].sum()
      oneDayIncome = df['incomeUSD'].sum()
      return prevIncome,oneDayIncome
    #####
    self.api = cl.bnCCXTInit()
    bal = pd.DataFrame(self.api.dapiPrivate_get_balance())
    cl.dfSetFloat(bal, ['balance', 'crossUnPnl'])
    bal = bal.set_index('asset').loc[self.validCcys]
    for ccy in self.validCcys:
      self.spots.loc[ccy,'SpotDelta']=bal.loc[ccy,'balance']+bal.loc[ccy,'crossUnPnl']
    self.calcSpotDeltaUSD()
    #####
    self.liqDict = dict()
    futs = pd.DataFrame(self.api.dapiPrivate_get_positionrisk()).set_index('symbol')
    cl.dfSetFloat(futs, ['positionAmt','liquidationPrice','markPrice'])
    for ccy in self.validCcys:
      ccy2=ccy+'USD_PERP'
      mult=100 if ccy=='BTC' else 10 # ETH and XRP are 10 multipliers
      self.futures.loc[ccy,'FutDelta']=futs.loc[ccy2,'positionAmt']*mult/self.spotDict[ccy]
      self.liqDict[ccy] = futs.loc[ccy2,'liquidationPrice'] / futs.loc[ccy2,'markPrice']
    self.calcFuturesDeltaUSD()
    #####
    pmts = pd.DataFrame()
    for ccy in self.validCcys:
      pmts = pmts.append(getPayments(ccy))
    self.payments = pmts
    #####
    self.prevIncome,self.oneDayIncome=getIncomes()
    self.prevAnnRet = self.prevIncome * 3 * 365 / self.futNotional
    self.oneDayAnnRet = self.oneDayIncome * 365 / self.futNotional
    #####
    self.nav = self.spots['SpotDeltaUSD'].sum()
    #####
    self.estFundingDict=dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.bnGetEstFunding(self.api, ccy)

  #####
  # BNT
  #####
  def bntInit(self):
    def getPayments(ccy):
      df = pd.DataFrame(self.api.fapiPublic_get_fundingrate({'symbol': ccy + 'USDT', 'startTime': getYest() * 1000}))
      cl.dfSetFloat(df, 'fundingRate')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
      df = df.set_index('date').sort_index()
      return df
    #####
    def getIncomes():
      df = pd.DataFrame(self.api.fapiPrivate_get_income({'incomeType': 'FUNDING_FEE', 'startTime': getYest() * 1000}))
      cl.dfSetFloat(df, 'income')
      df = df[['USDT' in z for z in df['symbol']]]
      df['Ccy'] = [z[:3] for z in df['symbol']]
      df = df.set_index('Ccy').loc[self.validCcys]
      df['incomeUSD'] = df['income'] * self.spotDict['USDT']
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['time']]
      df = df.set_index('date')
      prevIncome = df.loc[df.index[-1]]['incomeUSD'].sum()
      oneDayIncome = df['incomeUSD'].sum()
      return prevIncome, oneDayIncome
    #####
    self.api = cl.bnCCXTInit()
    futs = pd.DataFrame(self.api.fapiPrivate_get_positionrisk())
    cl.dfSetFloat(futs, ['positionAmt'])
    futs = futs.set_index('symbol').loc[[z+'USDT' for z in self.validCcys]]
    futs['Ccy'] = [z[:3] for z in futs.index]
    futs=futs.set_index('Ccy')
    futs['FutDelta'] = futs['FutDeltaUSD'] = futs['positionAmt']
    for ccy in self.validCcys:
      futs.loc[ccy, 'FutDeltaUSD'] *= self.spotDict[ccy]
    notional = futs['FutDeltaUSD'].abs().sum()
    self.futures=futs
    #####
    pmts=pd.DataFrame()
    for ccy in self.validCcys:
      pmts=pmts.append(getPayments(ccy))
    self.payments=pmts
    self.prevIncome,self.oneDayIncome=getIncomes()
    self.prevAnnRet = self.prevIncome * 3 * 365 / notional
    self.oneDayAnnRet = self.oneDayIncome * 365 / notional
    #####
    walletUSDT = pd.DataFrame(self.api.fapiPrivate_get_account()['assets']).set_index('asset').loc['USDT']
    self.nav = float(walletUSDT['marginBalance'])*self.spotDict['USDT']
    cushion = float(walletUSDT['availableBalance'])*self.spotDict['USDT']
    totalDelta = futs['FutDeltaUSD'].sum()
    self.liq = 1 - cushion / totalDelta
    #####
    self.estFundingDict = dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.bntGetEstFunding(self.api, ccy)

  ####
  # DB
  ####
  def dbInit(self):
    def getOneDayIncome(ccy, spot):
      df = pd.DataFrame(self.api.private_get_get_settlement_history_by_currency({'currency': ccy})['result']['settlements'])
      if len(df) == 0: return 0
      cl.dfSetFloat(df, 'funding')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['timestamp']]
      df = df.set_index('date').sort_index()
      if df.index[-1] >= (datetime.datetime.now() - pd.DateOffset(days=1)):
        return df['funding'].iloc[-1] * spot
      else:
        return 0
    #####
    self.api = cl.dbCCXTInit()
    self.liqDict = dict()
    for ccy in self.validCcys:
      acSum=self.api.private_get_get_account_summary({'currency': ccy})['result']
      self.spots.loc[ccy,'SpotDelta']=float(acSum['equity'])
      self.liqDict[ccy] = float(acSum['estimated_liquidation_ratio']) 
    self.calcSpotDeltaUSD()
    #####
    futs = pd.DataFrame([['BTC', self.spotDict['BTC'], cl.dbGetFutPos(self.api, 'BTC')],
                         ['ETH', self.spotDict['ETH'], cl.dbGetFutPos(self.api, 'ETH')],
                         ['XRP', self.spotDict['XRP'], 0]], columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
    futs['FutDelta'] = futs['FutDeltaUSD'] / futs['Spot']
    notional = futs['FutDeltaUSD'].abs().sum()
    self.futures=futs
    #####
    self.oneDayIncome = getOneDayIncome('BTC', self.spotDict['BTC']) + getOneDayIncome('ETH', self.spotDict['ETH'])
    self.oneDayAnnRet = self.oneDayIncome * 365 / notional
    #####
    self.nav = self.spots['SpotDeltaUSD'].sum()
    #####
    self.estFundingDict = dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.dbGetEstFunding(self.api, ccy)
      self.estFundingDict[ccy+'24H'] = cl.dbGetEstFunding(self.api, ccy, mins=60 * 24)
      self.estFundingDict[ccy+'8H'] = cl.dbGetEstFunding(self.api, ccy, mins=60 * 8)

  ####
  # KF
  ####
  def kfInit(self):
    def getPayments():
      ffn = os.path.dirname(cl.__file__) + '\\data\kfLog.csv'
      self.api.get_account_log(ffn)
      df = pd.read_csv(ffn, index_col=0, parse_dates=True)
      df['date'] = [datetime.datetime.strptime(z, '%Y-%m-%d %H:%M:%S') for z in df['dateTime']]
      df['date'] += pd.DateOffset(hours=8)  # Convert from UTC to HK Time
      df = df[df['date'] >= datetime.datetime.now() - pd.DateOffset(days=1)]
      df['Ccy']=df['collateral']
      df.loc[df['Ccy']=='XBT','Ccy']='BTC'
      df=df.set_index('Ccy',drop=False)
      for ccy in self.validCcys:
        df.loc[ccy, 'Spot'] = self.spotDict[ccy]
      df['incomeUSD'] = df['realized funding'] * df['Spot']
      prevIncome = df[df['date'] >= datetime.datetime.now() - pd.DateOffset(hours=4)]['incomeUSD'].sum()
      oneDayIncome=df['incomeUSD'].sum()
      df=df[df['type']=='funding rate change'].set_index('date').sort_index()
      df['rate'] = df['funding rate'] * df['Spot'] * 8
      return df,prevIncome,oneDayIncome
    #####
    self.api = cl.kfApophisInit()
    accounts = self.api.query('accounts')['accounts']
    self.liqDict = dict()
    for ccy in self.validCcys:
      ccy2 = 'xbt' if ccy=='BTC' else ccy.lower()
      self.spots.loc[ccy,'SpotDelta'] = accounts['fi_'+ccy2+'usd']['auxiliary']['pv'] + accounts['cash']['balances'][ccy2]
      self.liqDict[ccy] = accounts['fi_' + ccy2 + 'usd']['triggerEstimates']['im'] / self.spotDict[ccy]
    self.calcSpotDeltaUSD()
    #####
    futs = pd.DataFrame([['BTC', self.spotDict['BTC'], accounts['fi_xbtusd']['balances']['pi_xbtusd']], \
                         ['ETH', self.spotDict['ETH'], accounts['fi_ethusd']['balances']['pi_ethusd']],
                         ['XRP', self.spotDict['XRP'], accounts['fi_xrpusd']['balances']['pi_xrpusd']]], columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
    futs['FutDelta'] = futs['FutDeltaUSD'] / futs['Spot']
    notional = futs['FutDeltaUSD'].abs().sum()
    self.futures = futs
    #####
    self.payments,self.prevIncome,self.oneDayIncome=getPayments()
    self.prevAnnRet = self.prevIncome * 6 * 365 / notional
    self.oneDayAnnRet = self.oneDayIncome * 365 / notional
    #####
    self.nav = self.spots['SpotDeltaUSD'].sum()
    #####
    self.estFundingDict = dict()
    self.estFunding2Dict = dict()
    for ccy in self.validCcys:
      self.estFundingDict[ccy] = cl.kfGetEstFunding1(self.api, ccy)
      self.estFunding2Dict[ccy] = cl.kfGetEstFunding2(self.api, ccy)

  ####
  # KR
  ####
  def krInit(self):
    def getBal(bal, ccy):
      try:
        return float(bal[self.KR_CCY_DICT[ccy]])
      except:
        return 0
    #####
    self.KR_CCY_DICT = dict({'BTC': 'XXBT', 'ETH': 'XETH', 'XRP': 'XXRP', 'EUR': 'ZEUR'})
    self.api = cl.krCCXTInit(self.n)
    bal = self.api.private_post_balance()['result']
    for ccy in self.KR_CCY_DICT.keys():
      self.spots.loc[ccy,'SpotDelta']=getBal(bal,ccy)
    #####
    positions = pd.DataFrame(self.api.private_post_openpositions()['result']).transpose().set_index('pair')
    if not all([z in ['XXBTZUSD', 'XXBTZEUR'] for z in positions.index]):
      print('Invalid Kraken pair detected!')
      sys.exit(1)
    cl.dfSetFloat(positions, ['vol', 'vol_closed', 'time'])
    positions['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in positions['time']]
    positions['volNetBTC'] = positions['vol'] - positions['vol_closed']
    positions['volNetUSD'] = positions['volNetBTC'] * self.spotDict['BTC']
    self.spots.loc['BTC','SpotDelta'] += positions['volNetBTC'].sum()
    if 'XXBTZEUR' in positions.index:
      self.spots.loc['EUR','SpotDelta'] -= positions.loc['XXBTZEUR', 'volNetBTC'].sum() * float(self.api.public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
    for ccy in self.KR_CCY_DICT.keys():
      self.spots.loc[ccy,'SpotDeltaUSD']=self.spots.loc[ccy,'SpotDelta']*self.spotDict[ccy]
    notional = positions['volNetUSD'].abs().sum()
    #####
    # mdbUSD=Margin Delta BTC in USD
    xxbtzeur_volNetUSD_sum = positions.loc['XXBTZEUR', 'volNetUSD'].sum() if 'XXBTZEUR' in positions.index else 0
    self.mdbUSDDf = pd.DataFrame([['USD', positions.loc['XXBTZUSD', 'volNetUSD'].sum()], ['EUR', xxbtzeur_volNetUSD_sum]], columns=['Ccy', 'MDBU']).set_index('Ccy')
    #####
    self.oneDayIncome = -self.mdbUSDDf['MDBU'].sum() * 0.0006
    self.oneDayAnnRet = self.oneDayIncome * 365 / notional
    #####
    tradeBal = self.api.private_post_tradebalance()['result']
    self.nav = float(tradeBal['eb'])+float(tradeBal['n'])
    #####
    freeMargin = float(tradeBal['mf'])
    self.liqBTC = 1 - freeMargin / self.spots.loc['BTC','SpotDeltaUSD']

  def krPrintBorrow(self, nav):
    d=self.KR_CCY_DICT.copy()
    del d['EUR']
    zList=[]
    for ccy in d.keys():
      zList.append('$'+str(round(self.spots.loc[ccy,'SpotDeltaUSD']/1000))+'K')
    zPctNAV = '('+str(round(-self.mdbUSDDf['MDBU'].sum() / nav*100))+'%)'
    suffix='(spot '+'/'.join(d.keys())+': '
    suffix+='/'.join(zList)
    suffix+='; XXBTZUSD/XXBTZEUR: $'
    suffix += str(round(self.mdbUSDDf.loc['USD', 'MDBU'] / 1000)) + 'K/$'
    suffix += str(round(self.mdbUSDDf.loc['EUR', 'MDBU'] / 1000)) + 'K)'
    print(('KR' + str(self.n) + ' USD/EUR est borrow rate: ').rjust(41) + ('22% p.a. ($' + str(round(-self.mdbUSDDf['MDBU'].sum()/1000)) + 'K) '+zPctNAV).ljust(27)+suffix)

####################################################################################################

######
# Init
######
cl.printHeader('CryptoReporter')
if CRYPTO_MODE>0 and not APOPHIS_IS_IP_WHITELIST:
  print('CryptoReporter cannot be run in higher modes without IP whitelisting!')
  sys.exit(1)
ftx=cl.ftxCCXTInit()
spotDict=dict()
spotDict['USD']=1
for ccy in MAIN_CCY_DICT.keys():
  spotDict[ccy]=cl.ftxGetMid(ftx,ccy+'/USD')
#####
ftxCore = core('ftx',spotDict)
bbCore = core('bb',spotDict)
objs=[ftxCore,bbCore]
krCores=[]
if CRYPTO_MODE>0:
  bbtCore = core('bbt', spotDict)
  bnCore = core('bn', spotDict)
  bntCore = core('bnt', spotDict)
  dbCore = core('db', spotDict)
  kfCore = core('kf', spotDict)
  for i in range(CR_N_KR_ACCOUNTS):
    krCores.append(core('kr',spotDict,n=i+1))
  objs.extend([bbtCore, bnCore, bntCore, dbCore, kfCore] + krCores)
Parallel(n_jobs=len(objs), backend='threading')(delayed(obj.run)() for obj in objs)

#############
# Aggregation
#############
agDf = pd.DataFrame({'Ccy': AG_CCY_DICT.keys(), 'SpotDelta': AG_CCY_DICT.values(), 'FutDelta':[0] * len(AG_CCY_DICT.keys())}).set_index('Ccy')
nav=0
oneDayIncome=0
for obj in objs:
  nav+=obj.nav
  oneDayIncome += obj.oneDayIncome
  for ccy in AG_CCY_DICT.keys():
    agDf.loc[ccy,'SpotDelta']+=obj.spots.loc[ccy,'SpotDelta']
    agDf.loc[ccy,'FutDelta']+=obj.futures.loc[ccy,'FutDelta']
externalCoinsNAV=0
for ccy in AG_CCY_DICT.keys():
  externalCoinsNAV += AG_CCY_DICT[ccy] * spotDict[ccy]
externalUSDTNAV = EXTERNAL_USDT_DELTA * spotDict['USDT']
externalEURNAV = EXTERNAL_EUR_DELTA*(spotDict['EUR']-EXTERNAL_EUR_REF)
nav+=externalCoinsNAV+externalUSDTNAV+externalEURNAV
oneDayIncome+=ftxCore.oneDayFlows

########
# Output
########
navStrList=[]
for obj in objs:
  navStrList.append(getNAVStr(obj.name,obj.nav))
if externalCoinsNAV!=0: navStrList.append(getNAVStr('Coins ext',externalCoinsNAV))
if externalEURNAV!=0: navStrList.append(getNAVStr('EUR ext',externalEURNAV))
print(termcolor.colored(('NAV as of '+cl.getCurrentTime()+': $').rjust(42)+str(round(nav))+' ('+' / '.join(navStrList)+')','blue'))
#####
zList=[]
for ccy in MAIN_CCY_DICT.keys():
  zList.append(ccy + '=' + str(round(spotDict[ccy],MAIN_CCY_DICT[ccy])))
print(termcolor.colored('24h income: $'.rjust(42)+(str(round(oneDayIncome))+' ('+str(round(oneDayIncome*365/nav*100))+'% p.a.)').ljust(26),'blue')+' / '.join(zList))
print()
#####
for ccy in AG_CCY_DICT.keys():
  printDeltas(ccy,spotDict,agDf.loc[ccy,'SpotDelta'],agDf.loc[ccy,'FutDelta'])
if CRYPTO_MODE>0:
  printUSDTDeltas(ftxCore, spotDict, [bbtCore, bntCore])
  printEURDeltas(krCores, spotDict)
print()
#####
ftxCore.ftxPrintFlowsSummary('USD')
ftxCore.ftxPrintFlowsSummary('USDT')
ftxCore.ftxPrintBorrowLending('USD',nav)
ftxCore.ftxPrintBorrowLending('USDT',nav)
print()
#####
if CR_IS_SHOW_COIN_LENDING:
  for ccy in AG_CCY_DICT.keys():
    ftxCore.ftxPrintFlowsSummary(ccy)
  print()
#####
ftxCore.printAll()
if CRYPTO_MODE>0:
  printAllDual(bbCore, bbtCore)
  printAllDual(bnCore, bntCore)
  dbCore.printAll()
  kfCore.printAll()
  krPrintAll(krCores, nav)
else:
  bbCore.printAll()
#####
if '-f' in sys.argv:
  while True:
    time.sleep(1)