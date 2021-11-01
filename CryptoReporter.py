from CryptoParams import *
import CryptoLib as cl
from joblib import Parallel, delayed
import pandas as pd
import datetime
import time
import termcolor
import sys
import threading

###########
# Functions
###########
def appendDeltas(myList, ccy, spotDict, spotDelta, futDelta):
  spot = spotDict[ccy]
  netDelta=spotDelta+futDelta
  nDigits=2 if ccy=='BTC' else 1
  zLabel = 'spot/'
  z1 = str(round(spotDelta,nDigits)) + '/'
  z2 = '($' + str(round(spotDelta * spot / 1000)) + 'K/$'
  zLabel += 'fut/'
  z1 += str(round(futDelta,nDigits)) + '/'
  z2 += str(round(futDelta * spot / 1000)) + 'K/$'
  zLabel += 'net'
  z1 += str(round(netDelta,nDigits))
  z2 += str(round(netDelta * spot / 1000)) + 'K)'
  z=(ccy + ' ' +zLabel+': ').rjust(37)+z1.ljust(27)+z2
  myList.append(colored(z,'red'))

def appendUSDTDeltas(myList, ftxCore, spotDict, usdtCoreList):
  spotDeltaUSD = ftxCore.spots.loc['USDT','SpotDeltaUSD'] + CR_EXT_DELTA_USDT * spotDict['USDT']
  implDeltaUSD=0
  for core in usdtCoreList:
    spotDeltaUSD+=core.spots.loc['USDT','SpotDeltaUSD']
    implDeltaUSD-=core.futures['FutDeltaUSD'].sum()
  netDeltaUSD=spotDeltaUSD+implDeltaUSD
  #####
  spotDelta=spotDeltaUSD/spotDict['USDT']
  implDelta=implDeltaUSD/spotDict['USDT']
  netDelta=netDeltaUSD/spotDict['USDT']
  #####
  zLabel = 'spot/'
  z1=str(round(spotDelta/1000))+'K/'
  z2='($'+str(round(spotDeltaUSD/1000))+'K/$'
  zLabel += 'impl/'
  z1+=str(round(implDelta/1000))+'K/'
  z2+=str(round(implDeltaUSD/1000)) + 'K/$'
  zLabel += 'net: '
  z1 += str(round(netDelta / 1000)) + 'K'
  z2 += str(round(netDeltaUSD/1000))+'K)'
  myList.append(colored(('USDT '+zLabel).rjust(37)+(z1+' ').ljust(27)+z2, 'red'))

def appendFlows(myList, ftxCore, nav):
  def getSuffix(ftxCore,ccy,nav):
    return '(' + str(round(ftxCore.wallet.loc[ccy, 'usdValue'] / nav * 100)) + '%)'
  #####
  try:
    myList.append(ftxCore.flowsDict['USD'])
    myList.append(ftxCore.flowsDict['USDT'])
    myList.append(ftxCore.flowsDict['USD2']+getSuffix(ftxCore,'USD',nav))
    myList.append(ftxCore.flowsDict['USDT2']+getSuffix(ftxCore,'USDT',nav))
    myList.append('')
    for ccy in CR_FTX_FLOWS_CCYS:
      z = ftxCore.flowsDict[ccy]
      if not z is None: myList.append(z)
  except:
    pass

def colored(text, color):
  if '--nocolor' in sys.argv:
    return text
  else:
    return termcolor.colored(text,color)

def blank():
  return colored('', 'grey')

def fmtLiq(liq):
  return 'never' if (liq <= 0 or liq >= 10) else str(round(liq * 100)) + '%'

def getCores(isRetry=True):
  def getDummyCore(spotDict,objs):
    dummyCore=core('dummy', spotDict)
    objs.append(dummyCore)
    return dummyCore
  #####
  def processCore(exch,spotDict,objs,n=None):
    if SHARED_EXCH_DICT[exch]<1:
      return getDummyCore(spotDict,objs)
    else:
      myCore = core(exch, spotDict, n=n)
      objs.append(myCore)
      return myCore
  #####
  ftx=cl.ftxCCXTInit()
  spotDict=dict()
  ccyList = list(CR_QUOTE_CCY_DICT.keys())
  for ccy in ccyList:
    spotDict[ccy]=cl.ftxGetMid(ftx,ccy+'/USD')
  spotDict['USD']=1
  #####
  objs = []
  ftxCore=processCore('ftx',spotDict,objs)
  bbCore=processCore('bb',spotDict,objs)
  bbtCores=[]
  if SHARED_EXCH_DICT['bbt']==0:
    bbtCores.append(getDummyCore(spotDict,objs))
  else:
    for n in range(SHARED_EXCH_DICT['bbt']):
      bbtCores.append(processCore('bbt',spotDict,objs,n=n+1))
  dbCore=processCore('db', spotDict, objs)
  kfCore=processCore('kf',spotDict,objs)
  kutCores=[]
  if SHARED_EXCH_DICT['kut']==0:
    kutCores.append(getDummyCore(spotDict,objs))
  else:
    for n in range(SHARED_EXCH_DICT['kut']):
      kutCores.append(processCore('kut',spotDict,objs,n=n+1))
  #####
  isOk=True
  try:
    Parallel(n_jobs=len(objs), backend='threading')(delayed(obj.run)() for obj in objs)
  except:
    if not isRetry: return None, None, None, False
    print('[WARNING: Parallel run failed!  Rerunning in serial ....]')
    isOk=True
    for obj in objs:
      try:
        print('Running '+obj.name+' ....')
        obj.run()
      except:
        pass
      if not obj.isDone:
        isOk=False
        print('[WARNING: Corrupted results for ' + obj.name + '!]')
    print()
    
  coresDict=dict()
  coresDict['ftx']=ftxCore
  coresDict['bb']=bbCore
  coresDict['bbt']=bbtCores
  coresDict['db']=dbCore
  coresDict['kf']=kfCore
  coresDict['kut']=kutCores
  
  return coresDict, spotDict, objs, isOk

def getNAV(objs,spotDict):
  nav = 0
  for obj in objs:
    nav+=obj.nav
  extCoinsNAV=0
  for ccy in CR_AG_CCY_DICT.keys():
    extCoinsNAV += CR_AG_CCY_DICT[ccy] * spotDict[ccy]
  extCoinsNAV += CR_EXT_DELTA_USDT * spotDict['USDT']
  nav+= extCoinsNAV
  return nav, extCoinsNAV

def getNAVStr(name, nav):
  return name + ': $' + str(round(nav/1000)) + 'K'

def printAllDual(core1, core2):
  if core1.exch == 'dummy' and core2.exch == 'dummy': return
  if core1.exch == 'dummy':
    core2.printAll()
  elif core2.exch == 'dummy':
    core1.printAll()
  else:
    n=120
    print(core1.incomesStr.ljust(n) + core2.incomesStr)
    list1 = list(core1.fundingStrDict.values())
    list2 = list(core2.fundingStrDict.values())
    if core1.liqStr!='': list1.append(core1.liqStr.ljust(n))
    if core2.liqStr!='': list2.append(core2.liqStr)
    printTwoLists(list1,list2,n)

def printAllTrio(core1, core2, core3):
  if core1.exch == 'dummy' and core2.exch == 'dummy' and core3.exch == 'dummy': return
  if core1.exch == 'dummy':
    printAllDual(core2, core3)
  elif core2.exch == 'dummy':
    printAllDual(core1, core3)
  elif core3.exch == 'dummy':
    printAllDual(core1, core2)
  else:
    n = 120
    print(core1.incomesStr.ljust(n) + core2.incomesStr)
    list1 = list(core1.fundingStrDict.values())
    list2 = list(core2.fundingStrDict.values())
    if core1.liqStr!='': list1.append(core1.liqStr.ljust(n))
    if core2.liqStr!='': list2.append(core2.liqStr)
    list2.append('')
    list2.append(core3.incomesStr)
    list2.extend(core3.fundingStrDict.values())
    if core3.liqStr!='': list2.append(core3.liqStr)
    printTwoLists(list1, list2, n)

def printAllQuad(core1, core2, core3, core4):
  if core1.exch == 'dummy' and core2.exch == 'dummy' and core3.exch == 'dummy' and core4.exch == 'dummy': return
  if core1.exch == 'dummy':
    printAllTrio(core2,core3,core4)
  elif core2.exch == 'dummy':
    printAllTrio(core1,core3,core4)
  elif core3.exch == 'dummy':
    printAllTrio(core1,core2,core4)
  elif core4.exch == 'dummy':
    printAllTrio(core1,core2,core3)
  else:
    n = 120
    print(core1.incomesStr.ljust(n) + core2.incomesStr)
    list1 = list(core1.fundingStrDict.values())
    list2 = list(core2.fundingStrDict.values())
    if core1.liqStr != '': list1.append(core1.liqStr.ljust(n))
    if core2.liqStr != '': list2.append(core2.liqStr)
    list2.append('')
    list2.append(core3.incomesStr)
    list2.extend(core3.fundingStrDict.values())
    if core3.liqStr != '': list2.append(core3.liqStr)
    list2.append('')
    list2.append(core4.incomesStr)
    list2.extend(core4.fundingStrDict.values())
    if core4.liqStr != '': list2.append(core4.liqStr)
    printTwoLists(list1, list2, n)

def printTwoLists(list1, list2, n):
  for i in range(min(len(list1), len(list2))):
    print(list1[i].ljust(n) + list2[i])
  if len(list1) > len(list2):
    for i in range(len(list2), len(list1)):
      print(list1[i].ljust(n))
  elif len(list2) > len(list1):
    for i in range(len(list1), len(list2)):
      print(blank().ljust(n) + list2[i])
  print()

####################################################################################################

#########
# Classes
#########
class core:
  def __init__(self, exch, spotDict, n=None):
    self.isDone = False
    self.exch = exch
    self.name = exch.upper()
    self.spotDict = spotDict
    self.n = n
    if self.n is not None: self.name += str(n)
    #####
    self.validCcys = cl.getValidCcys(exch)
    #####
    ccyList = list(SHARED_CCY_DICT.keys())
    cl.appendUnique(ccyList, 'USD')
    cl.appendUnique(ccyList, 'USDT')
    zeroes = [0] * len(ccyList)
    self.spots = pd.DataFrame({'Ccy': ccyList, 'SpotDelta': zeroes, 'SpotDeltaUSD':zeroes}).set_index('Ccy')
    self.futures = pd.DataFrame({'Ccy':ccyList, 'FutDelta': zeroes, 'FutDeltaUSD':zeroes}).set_index('Ccy')
    self.oneDayFlows = 0
    self.flowsDict = dict()
    self.oneDayIncome = 0
    self.nav = 0
    self.incomesStr = ''
    self.fundingStrDict=dict()
    self.liqDict=dict()
    self.liqStr = ''

  def run(self):
    if self.exch=='dummy':
      self.isDone=True
      return
    if self.exch=='ftx':
      self.ftxInit()
    elif self.exch=='bb':
      self.bbInit()
    elif self.exch=='bbt':
      self.bbtInit()
    elif self.exch=='db':
      self.dbInit()
    elif self.exch=='kf':
      self.kfInit()
    elif self.exch=='kut':
      self.kutInit()

  def calcSpotDeltaUSD(self):
    for ccy in self.spots.index:
      self.spots.loc[ccy,'SpotDeltaUSD']=self.spots.loc[ccy,'SpotDelta']*self.spotDict[ccy]

  def calcFuturesDeltaUSD(self):
    for ccy in self.spots.index:
      self.futures.loc[ccy, 'FutDeltaUSD'] = self.futures.loc[ccy, 'FutDelta'] * self.spotDict[ccy]
    self.futNotional = self.futures['FutDeltaUSD'].abs().sum()

  def makeIncomesStr(self):
    z1 = '$' + str(round(self.oneDayIncome)) + ' (' + str(round(self.oneDayAnnRet * 100)) + '% p.a.)'
    if self.exch == 'db':
      self.incomesStr = colored('DB 24h funding income: '.rjust(37) + z1, 'blue')
    else:
      zPrev  = '4h' if self.exch == 'kf' else 'prev'
      z2 = '$' + str(round(self.prevIncome)) + ' (' + str(round(self.prevAnnRet * 100)) + '% p.a.)'
      self.incomesStr = colored((self.name +  ' 24h/'+zPrev+' funding income: ').rjust(37) + z1 + ' / ' + z2, 'blue')

  def makeFundingStr(self,ccy, oneDayFunding, prevFunding, estFunding, estFunding2=None):
    if self.exch in ['bb','bbt','db','kf','kut']:
      z = fmtLiq(self.liqDict[ccy])
    else:
      z = ''
    liqStr = colored(z.rjust(5),'red')
    prefix = self.name + ' ' + ccy + ' 24h/'
    prefix += '8h' if self.exch=='db' else 'prev'
    prefix+='/est'
    if self.exch in ['bb','bbt','kf','kut']:
      prefix += '1/est2'
    prefix += ':'
    #####
    body = str(round(oneDayFunding * 100)) + '%/'
    body += str(round(prevFunding * 100)) + '%/'
    body += str(round(estFunding * 100)) + '%'
    if self.exch in ['bb','bbt','kf','kut']:
      body += '/' + str(round(estFunding2 * 100)) + '%'
    body += ' p.a.'
    #####
    spotDeltaUSD=self.spots.loc[ccy,'SpotDeltaUSD']
    futDeltaUSD=self.futures.loc[ccy, 'FutDeltaUSD']
    netDeltaUSD=spotDeltaUSD+futDeltaUSD
    if self.exch in ['bbt','kut']:
      suffix = '(fut: $' + str(round(futDeltaUSD / 1000)) + 'K)'
    else:
      suffix = '(spot/fut/net: $' + str(round(spotDeltaUSD/1000)) + 'K/$' + str(round(futDeltaUSD/1000)) + 'K/$' + str(round(netDeltaUSD/1000))+'K)'
    self.fundingStrDict[ccy] = liqStr.rjust(5) + prefix.rjust(31) + ' ' + body.ljust(27) + suffix

  def makeLiqStr(self,cushion=None,delta=None,riskDf=None,availableBalance=None):  # ftx, bbt, kut
    def bbtGetLiq(riskDf, availableBalance, increment):
      df = riskDf.copy()
      isOk = False
      for i in range(100):
        df['unrealised_pnl_sim'] = df['unrealised_pnl'] + df['delta_value'] * (i + 1) * increment
        df['ab_delta'] = df['unrealised_pnl_sim'].clip(None, 0) - df['unrealised_pnl'].clip(None, 0)
        ab = availableBalance + df['ab_delta'].sum()
        df['unreal_loss_indiv'] = 0
        if ab < 0:
          losers = df['ab_delta'] < 0
          df.loc[losers, 'unreal_loss_indiv'] = ab * (df.loc[losers, 'delta_value'] / df.loc[losers, 'delta_value'].sum())
          ab = 0
        df['cushion'] = ab + df['unreal_loss_indiv'] + df['im_value'] - df['mm_value'] + df['unrealised_pnl_sim'].clip(0, None)
        if df['cushion'].min() < 0:
          isOk=True
          break
      if isOk:
        return 1 + i * increment
      else:
        return 0
    #####
    def kutGetLiq(riskDf, availableBalance, increment):
      df = riskDf.copy()
      isOk = False
      for i in range(100):
        sim_liq_ratio = (1 + ((i + 1) * increment))
        df['sim_add_liq_ratio'] = sim_liq_ratio - df['liqRaw']
        df['sim_add_margin'] = df['sim_add_liq_ratio'].clip(0, None) * abs(df['markValue'])
        cushion = availableBalance - df['sim_add_margin'].sum()
        if cushion < 0:
          isOk=True
          break
      if isOk:
        return 1 + i * increment
      else:
        return 0
    #####
    if self.exch in ['bbt','kut']:
      if len(riskDf)==0:
        self.liqL = 0
        self.liqH = 10
      elif self.exch=='bbt':
        self.liqL = bbtGetLiq(riskDf, availableBalance,-0.01)
        self.liqH = bbtGetLiq(riskDf, availableBalance,0.01)
      elif self.exch=='kut':
        self.liqL = kutGetLiq(riskDf, availableBalance, -0.01)
        self.liqH = kutGetLiq(riskDf, availableBalance, 0.01)
    else: # ftx
      liq = 1 - cushion / delta
      if delta>=0:
        self.liqL = liq
        self.liqH = 10
      else:
        self.liqL = 0
        self.liqH = liq
    #####
    zL = fmtLiq(self.liqL)
    zH = fmtLiq(self.liqH)
    if self.exch == 'ftx':
      z = 'FTX liqL/liqH/mf/fc: '.rjust(37) + zL + '/' + zH + '/' + str(round(self.mf * 100, 1)) + '%(vs.' + str(round(self.mmReq * 100, 1)) + '%)/$' + str(round(self.freeCollateral))
    elif self.exch in ['bbt','kut']:
      z = (self.name + ' liqL/liqH/ab: ').rjust(37) + zL + '/' + zH + '/' + '$'+str(round(availableBalance))
    else:
      z = (self.name + ' liqL/liqH: ').rjust(37) + zL +'/' + zH
    self.liqStr = colored(z,'red')

  def printAll(self):
    try:
      if self.exch=='dummy': return
      print(self.incomesStr)
      for ccy in self.validCcys:
        print(self.fundingStrDict[ccy])
      if self.liqStr!='': print(self.liqStr)
      print()
    except:
      pass

  def setAnnRets(self):
    if self.futNotional !=0 :
      self.oneDayAnnRet = self.oneDayIncome * 365 / self.futNotional
      if self.exch == 'ftx':
        mult = 24
      elif self.exch == 'kf':
        mult = 6
      else:
        mult = 3
      self.prevAnnRet = self.prevIncome * mult * 365 / self.futNotional
    else:
      self.oneDayAnnRet = 0
      self.prevAnnRet = 0

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
    def makeFlows(ccy):
      start_time = cl.getYest()
      borrows = cleanBorrows(ccy, pd.DataFrame(self.api.private_get_spot_margin_borrow_history({'limit': 1000, 'start_time': start_time})['result']))
      loans = cleanBorrows(ccy, pd.DataFrame(self.api.private_get_spot_margin_lending_history({'limit': 1000, 'start_time': start_time})['result']))
      cl.dfSetFloat(borrows, ['cost','rate'])
      cl.dfSetFloat(loans, 'proceeds')
      prevBorrow = borrows.iloc[-1]['cost'] if borrows.index[-1] == self.payments.index[-1] else 0
      prevLoan = loans.iloc[-1]['proceeds'] if loans.index[-1] == self.payments.index[-1] else 0
      absBalUSD = abs(self.wallet.loc[ccy, 'total']*self.spotDict[ccy])
      d=dict()
      d['oneDayFlows'] = (loans['proceeds'].sum() - borrows['cost'].sum()) * self.spotDict[ccy]
      d['oneDayFlowsAnnRet'] = d['oneDayFlows'] * 365 / absBalUSD
      d['oneDayBorrowRate'] = borrows['rate'].mean() * 24 * 365
      d['prevFlows']=(prevLoan - prevBorrow) * self.spotDict[ccy]
      d['prevFlowsAnnRet']=d['prevFlows'] * 24 * 365 / absBalUSD
      d['prevBorrowRate'] = borrows.iloc[-1]['rate'] * 24 * 365 if borrows.index[-1] == self.payments.index[-1] else 0
      return d
    ######
    self.api = cl.ftxCCXTInit()
    self.wallet = cl.ftxGetWallet(self.api,self.validCcys)
    ccys=self.validCcys.copy()
    cl.appendUnique(ccys,'USDT')
    for ccy in ccys:
      self.spots.loc[ccy,'SpotDelta'] = self.wallet.loc[ccy,'total']
    self.calcSpotDeltaUSD()
    ######
    info = self.api.private_get_account()['result']
    futs = pd.DataFrame(info['positions']).set_index('future')
    cl.dfSetFloat(futs, 'size')
    for ccy in self.validCcys:
      ccy2=ccy+'-PERP'
      if ccy2 in futs.index:
        mult = -1 if futs.loc[ccy2, 'side']=='sell' else 1
        self.futures.loc[ccy,'FutDelta']=futs.loc[ccy2,'size']*mult
    self.calcFuturesDeltaUSD()
    ######
    start_time=cl.getYest()
    pmts = pd.DataFrame()
    for ccy in self.validCcys:
      pmts = pmts.append(pd.DataFrame(self.api.private_get_funding_payments({'future':ccy+'-PERP', 'start_time': start_time})['result']))
    pmts = pmts.set_index('time').sort_index()
    cl.dfSetFloat(pmts, 'payment')
    self.payments = pmts
    #####
    self.oneDayIncome = -self.payments['payment'].sum()
    self.prevIncome = -self.payments.loc[self.payments.index[-1]]['payment'].sum()
    self.setAnnRets()
    #####
    flowsCcy=CR_FTX_FLOWS_CCYS.copy()
    cl.appendUnique(flowsCcy,'USD')
    cl.appendUnique(flowsCcy,'USDT')
    for ccy in flowsCcy:
      d=makeFlows(ccy)
      self.oneDayFlows += d['oneDayFlows']
      if d['oneDayFlows']==0 and d['prevFlows']==0 and not ccy in ['USD','USDT']:
        self.flowsDict[ccy]=None
      else:
        z1 = '$' + str(round(d['oneDayFlows'])) + ' (' + str(round(d['oneDayFlowsAnnRet'] * 100)) + '% p.a.)'
        z2 = '$' + str(round(d['prevFlows'])) + ' (' + str(round(d['prevFlowsAnnRet'] * 100)) + '% p.a.)'
        self.flowsDict[ccy]=colored(('FTX 24h/prev ' + ccy + ' flows: ').rjust(37) + z1 + ' / ' + z2, 'blue')
      if ccy in ['USD','USDT']: # Extra info for USD/USDT
        zList = []
        zList.append('na' if d['oneDayBorrowRate'] == 0 else str(round(d['oneDayBorrowRate'] * 100)) + '%')
        zList.append('na' if d['prevBorrowRate'] == 0 else str(round(d['prevBorrowRate'] * 100)) + '%')
        zList.append(str(round(cl.ftxGetEstBorrow(self.api, ccy) * 100)) + '%')
        self.flowsDict[ccy+'2'] = ('FTX ' + ccy + ' 24h/prev/est: ').rjust(37) + '/'.join(zList) + ' p.a. ($' + str(round(self.wallet.loc[ccy, 'usdValue'] / 1000)) + 'K) '
    #####
    self.nav = self.wallet['usdValue'].sum()
    #####
    for ccy in self.validCcys:
      df=pd.DataFrame(self.api.public_get_funding_rates({'future':ccy+'-PERP', 'start_time': start_time})['result']).set_index('time').sort_index()
      cl.dfSetFloat(df,'rate')
      oneDayFunding = df['rate'].mean() * 24 * 365
      prevFunding = df['rate'][-1] * 24 * 365
      estFunding = cl.ftxGetEstFunding(self.api, ccy)
      self.makeFundingStr(ccy, oneDayFunding, prevFunding, estFunding)
    #####
    self.makeIncomesStr()
    #####
    self.mf = float(info['marginFraction'])
    self.mmReq = float(info['maintenanceMarginRequirement'])
    self.freeCollateral = float(info['freeCollateral'])
    totalPositionNotional = self.nav / self.mf
    cushion = (self.mf - self.mmReq) * totalPositionNotional
    delta = self.wallet.loc[self.validCcys, 'usdValue'].sum() + self.futures['FutDeltaUSD'].sum()
    self.makeLiqStr(cushion=cushion,delta=delta)
    #####
    self.isDone=True

  ####
  # BB
  ####
  def bbInit(self):
    def getPayments(ccy):
      n = 0
      df = pd.DataFrame()
      while True:
        n += 1
        tl = self.api.v2_private_get_execution_list({'symbol': ccy + 'USD', 'start_time': cl.getYest() * 1000, 'limit': 1000, 'page': n})['result']['trade_list']
        if tl is None:
          break
        else:
          df = df.append(pd.DataFrame(tl))
      if len(df)==0:
        return None
      else:
        return df.set_index('symbol', drop=False)
    #####
    self.api = cl.bbCCXTInit()
    self.wallet=pd.DataFrame(self.api.v2_private_get_wallet_balance()['result']).transpose()
    cl.dfSetFloat(self.wallet,'equity')
    for ccy in self.validCcys:
      self.spots.loc[ccy,'SpotDelta']=self.wallet.loc[ccy,'equity']
    self.calcSpotDeltaUSD()
    #####
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
    self.oneDayIncome=0
    self.prevIncome=0
    pmts = pd.DataFrame()
    for ccy in self.validCcys:
      pmts = pmts.append(getPayments(ccy))
    if len(pmts)>0:
      pmts = pmts[pmts['exec_type'] == 'Funding'].copy()
      cl.dfSetFloat(pmts, ['fee_rate', 'exec_fee'])
      pmts.loc[['Sell' in z for z in pmts['order_id']],'fee_rate']*=-1 # Correction for fee_rate signs
      for ccy in self.validCcys:
        ccy2=ccy+'USD'
        if ccy2 in pmts.index: pmts.loc[ccy2, 'incomeUSD'] = -pmts.loc[ccy2, 'exec_fee'] * self.spotDict[ccy]
      pmts['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in pmts['trade_time_ms']]
      pmts = pmts.set_index('date')
      #####
      if len(pmts)>0:
        self.oneDayIncome = pmts['incomeUSD'].sum()
        self.prevIncome = pmts.loc[pmts.index[-1]]['incomeUSD'].sum()
    self.setAnnRets()
    #####
    self.nav=self.spots['SpotDeltaUSD'].sum()
    #####
    for ccy in self.validCcys:
      oneDayFunding=0
      prevFunding=0
      if len(pmts)>0:
        df = pmts.loc[pmts['symbol'] == ccy + 'USD', 'fee_rate']
        if len(df) > 0:
          oneDayFunding = df.mean() * 3 * 365
          prevFunding = df[df.index[-1]].mean() * 3 * 365
      estFunding = cl.bbGetEstFunding1(self.api, ccy)
      estFunding2 = cl.bbGetEstFunding2(self.api, ccy)
      self.makeFundingStr(ccy, oneDayFunding, prevFunding, estFunding, estFunding2)
    #####
    self.makeIncomesStr()
    self.isDone = True

  #####
  # BBT
  #####
  def bbtInit(self):
    self.api = cl.bbCCXTInit(n=self.n)
    riskDf = cl.bbtGetRiskDf(self.api, self.spotDict)
    for ccy in self.validCcys:
      if ccy in riskDf.index:
        self.futures.loc[ccy, 'FutDelta']=cl.bbtGetFutPos(self.api,ccy)
        self.liqDict[ccy] = riskDf.loc[ccy,'liq']
      else:
        self.liqDict[ccy] = 0
    self.calcFuturesDeltaUSD()
    #####
    if self.n>=2: # trim list for auxiliary BBTs
      self.validCcys=list(self.futures.index[self.futures['FutDelta'] != 0])
    #####
    pmts=pd.DataFrame()
    for ccy in self.validCcys:
      data = cl.bbtGetTradeExecutionList(self.api,ccy)
      if not data is None:
        pmts = pmts.append(pd.DataFrame(data).set_index('symbol', drop=False))
    if len(pmts)==0:
      self.oneDayIncome=0
      self.prevIncome=0
    else:
      cl.dfSetFloat(pmts, ['fee_rate', 'exec_fee'])
      pmts.loc[['Sell' in z for z in pmts['order_id']],'fee_rate']*=-1 # Correction for fee_rate signs
      pmts['incomeUSD'] = -pmts['exec_fee'] * self.spotDict['USDT']
      pmts['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in pmts['trade_time_ms']]
      pmts = pmts.set_index('date').sort_index()
      #####
      self.oneDayIncome = pmts['incomeUSD'].sum()
      self.prevIncome = pmts.loc[pmts.index[-1]]['incomeUSD'].sum()
    self.setAnnRets()
    #####
    usdtDict=self.api.v2_private_get_wallet_balance({'coin': 'USDT'})['result']['USDT']
    equity = float(usdtDict['equity'])
    self.nav = equity * self.spotDict['USDT']
    self.spots.loc['USDT', 'SpotDelta'] = equity
    self.calcSpotDeltaUSD()
    #####
    for ccy in self.validCcys:
      if len(pmts)==0:
        oneDayFunding = 0
        prevFunding = 0
      else:
        df=pmts.loc[pmts['symbol']==ccy+'USDT','fee_rate']
        if len(df) == 0:
          oneDayFunding = 0
          prevFunding = 0
        else:
          oneDayFunding = df.mean() * 3 * 365
          prevFunding = df[df.index[-1]].mean() * 3 * 365
      estFunding = self.bbtGetEstFunding1_fast(ccy)
      estFunding2 = self.bbtGetEstFunding2_fast(ccy)
      self.makeFundingStr(ccy, oneDayFunding, prevFunding, estFunding, estFunding2)
    #####
    self.makeIncomesStr()
    self.makeLiqStr(riskDf=riskDf,availableBalance=float(usdtDict['available_balance']))
    self.isDone = True

  def bbtGetEstFunding1_fast(self,ccy):
    key = 'bbtEstFunding1_'+ccy
    estFunding1 = cl.cache('r', key)
    if estFunding1 is None:
      estFunding1 = cl.bbtGetEstFunding1(self.api,ccy)
      cl.cache('w', key, estFunding1)
    return estFunding1

  def bbtGetEstFunding2_fast(self,ccy):
    key = 'bbtEstFunding2_'+ccy
    estFunding2 = cl.cache('r', key)
    if estFunding2 is None:
      estFunding2 = cl.bbtGetEstFunding2(self.api,ccy)
      cl.cache('w', key, estFunding2)
    return estFunding2
  
  ####
  # DB
  ####
  def dbInit(self):
    def getOneDayIncome(ccy):
      df = pd.DataFrame(self.api.private_get_get_settlement_history_by_currency({'currency': ccy})['result']['settlements'])
      if len(df) == 0: return 0
      cl.dfSetFloat(df, 'funding')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['timestamp']]
      df = df.set_index('date').sort_index()
      if df.index[-1] >= (datetime.datetime.now() - pd.DateOffset(days=1)):
        return df['funding'].iloc[-1] * self.spotDict[ccy]
      else:
        return 0
    #####
    self.api = cl.dbCCXTInit()
    for ccy in self.validCcys:
      acSum = self.api.private_get_get_account_summary({'currency': ccy})['result']
      self.spots.loc[ccy, 'SpotDelta'] = float(acSum['equity'])
      self.liqDict[ccy] = float(acSum['estimated_liquidation_ratio'])
    self.calcSpotDeltaUSD()
    #####
    for ccy in self.validCcys:
      self.futures.loc[ccy, 'FutDelta'] = cl.dbGetFutPos(self.api, ccy) / self.spotDict[ccy]
    self.calcFuturesDeltaUSD()
    #####
    for ccy in self.validCcys:
      self.oneDayIncome += getOneDayIncome(ccy)
    self.oneDayAnnRet = self.oneDayIncome * 365 / self.futNotional
    #####
    self.nav = self.spots['SpotDeltaUSD'].sum()
    #####
    for ccy in self.validCcys:
      oneDayFunding = cl.dbGetEstFunding(self.api, ccy, mins=60 * 24)
      prevFunding = cl.dbGetEstFunding(self.api, ccy, mins=60 * 8)
      estFunding = cl.dbGetEstFunding(self.api, ccy)
      self.makeFundingStr(ccy, oneDayFunding, prevFunding, estFunding)
    #####
    self.makeIncomesStr()
    self.isDone = True

  ####
  # KF
  ####
  def kfInit(self):
    def getPayments():
      if APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST']:
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
          if ccy in df.index: df.loc[ccy, 'Spot'] = self.spotDict[ccy]
        df['incomeUSD'] = df['realized funding'] * df['Spot']
        oneDayIncome = df['incomeUSD'].sum()
        prevIncome = df[df['date'] >= datetime.datetime.now() - pd.DateOffset(hours=4)]['incomeUSD'].sum()
        df=df[df['type']=='funding rate change'].set_index('date').sort_index()
        df['rate'] = df['funding rate'] * df['Spot'] * 8
        return df,oneDayIncome,prevIncome
      else:
        return None,0,0
    #####
    self.api = cl.kfApophisInit()
    accounts = self.api.query('accounts')['accounts']
    for ccy in self.validCcys:
      ccy2 = 'xbt' if ccy=='BTC' else ccy.lower()
      self.spots.loc[ccy,'SpotDelta'] = accounts['fi_'+ccy2+'usd']['auxiliary']['pv'] + accounts['cash']['balances'][ccy2]
      self.liqDict[ccy] = accounts['fi_' + ccy2 + 'usd']['triggerEstimates']['mm'] / self.spotDict[ccy]
    self.calcSpotDeltaUSD()
    #####
    for ccy in self.validCcys:
      ccy2 = 'xbt' if ccy == 'BTC' else ccy.lower()
      bal = accounts['fi_' + ccy2 + 'usd']['balances']
      symbol = 'pi_' + ccy2 + 'usd'
      if symbol in bal:
        self.futures.loc[ccy, 'FutDelta'] = bal[symbol] / self.spotDict[ccy]
    self.calcFuturesDeltaUSD()
    #####
    pmts,self.oneDayIncome,self.prevIncome=getPayments()
    self.setAnnRets()
    #####
    self.nav = self.spots['SpotDeltaUSD'].sum()
    #####
    for ccy in self.validCcys:
      oneDayFunding = 0
      prevFunding = 0
      if not pmts is None:
        df = pmts.loc[pmts['Ccy'] == ccy, 'rate']
        if len(df) > 0:
          oneDayFunding = df.mean() * 3 * 365
          prevFunding = df[df.index[-1]].mean() * 3 * 365
      estFunding = cl.kfGetEstFunding1(self.api, ccy)
      estFunding2 = cl.kfGetEstFunding2(self.api, ccy)
      self.makeFundingStr(ccy, oneDayFunding, prevFunding, estFunding, estFunding2)
    #####
    self.makeIncomesStr()
    self.isDone = True

  #####
  # KUT
  #####
  def kutInit(self):
    def getFundingHistory(ccy,startAt):
      key='kutLock'
      kutLock = cl.cache('r', key)
      if kutLock is None:
        kutLock = threading.Lock()
        cl.cache('w',key,kutLock)
      with kutLock:
        while True:
          try:
            fundingHistory = self.api.futuresPrivate_get_funding_history({'symbol': cl.kutGetCcy(ccy) + 'USDTM', 'startAt': startAt})['data']['dataList']
            break
          except:
            print("[DEBUG: Error from KuCoin's futuresPrivate_get_funding_history ("+self.name+':'+ccy+')!  Pausing for 30 seconds ....]')
            time.sleep(30)
            print('[DEBUG: Resuming ....]')
        time.sleep(CR_CONFIGS_DICT['KU_FUNDING_HISTORY_SLEEP'])
        return fundingHistory
    #####
    self.api = cl.kutCCXTInit(n=self.n)
    self.usdtDict = cl.kutGetUSDTDict(self.api)
    self.availableBalance = float(self.usdtDict['availableBalance'])
    self.riskDf=cl.kutGetRiskDf(self.api,self.availableBalance)
    #####
    posData=cl.kutGetPositions(self.api)
    for ccy in self.validCcys:
      ccy2=cl.kutGetCcy(ccy)+'USDTM'
      if ccy2 in posData.index:
        self.futures.loc[ccy, 'FutDelta']=float(posData.loc[ccy2,'currentQty'])*cl.kutGetMult(self.api,ccy)
    self.calcFuturesDeltaUSD()
    #####
    if self.n >= 2:  # trim list for auxiliary KUTs
      self.validCcys = list(self.futures.index[self.futures['FutDelta'] != 0])
    #####
    for ccy in self.validCcys:
      ccy2=cl.kutGetCcy(ccy)+'USDTM'
      if ccy2 in posData.index:
        self.liqDict[ccy] = self.riskDf.loc[ccy2,'liq']
      else:
        self.liqDict[ccy] = 0
      #futDeltaUSD = self.futures.loc[ccy, 'FutDeltaUSD']
      #if futDeltaUSD != 0:
      #  self.liqDict[ccy] -= (availableBalance / self.futures.loc[ccy, 'FutDeltaUSD'])
    #####
    pmts=pd.DataFrame()
    if CR_CONFIGS_DICT['IS_KU_CALC_PAYMENTS']:
      startAt = cl.getYest() * 1000
      for ccy in self.validCcys:
        df=pd.DataFrame(getFundingHistory(ccy,startAt))
        if len(df)>0: pmts=pmts.append(df[['symbol','timePoint','fundingRate','funding']])
    if len(pmts)==0:
      self.oneDayIncome=0
      self.prevIncome=0
    else:
      cl.dfSetFloat(pmts, ['timePoint', 'fundingRate', 'funding'])
      pmts['fundingUSD'] = pmts['funding'] * self.spotDict['USDT']
      pmts=pmts.set_index('timePoint').sort_index()
      self.oneDayIncome=pmts['fundingUSD'].sum()
      self.prevIncome=pmts.loc[pmts.index[-1]]['fundingUSD'].sum()
    self.setAnnRets()
    #####
    equity = float(self.usdtDict['accountEquity'])
    self.nav = equity * self.spotDict['USDT']
    self.spots.loc['USDT', 'SpotDelta'] = equity
    self.calcSpotDeltaUSD()
    #####
    for ccy in self.validCcys:
      if len(pmts)==0:
        oneDayFunding = 0
        prevFunding = 0
      else:
        df=pmts.loc[pmts['symbol']==cl.kutGetCcy(ccy)+'USDTM','fundingRate']
        if len(df) == 0:
          oneDayFunding = 0
          prevFunding = 0
        else:
          oneDayFunding = df.mean() * 3 * 365
          prevFunding = df[df.index[-1]].mean() * 3 * 365
      estFunding,estFunding2 = self.kutGetEstFundings_fast(ccy)
      self.makeFundingStr(ccy, oneDayFunding, prevFunding, estFunding, estFunding2)
    #####
    self.makeIncomesStr()
    self.makeLiqStr(riskDf=self.riskDf, availableBalance=self.availableBalance)
    self.isDone = True

  def kutGetEstFundings_fast(self,ccy):
    key = 'kutEstFundings_'+ccy
    estFundings = cl.cache('r', key)
    if estFundings is None:
      estFundings = cl.kutGetEstFundings(self.api,ccy)
      cl.cache('w',key,estFundings)
    return estFundings

####################################################################################################

if __name__ == '__main__':
  ######
  # Init
  ######
  cl.printHeader('CryptoReporter')
  if SHARED_EXCH_DICT['kf']==1 and not APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST']:
    print('[WARNING: IP is not whitelisted for Apophis, therefore KF incomes are not shown]\n')

  ###########
  # Get cores
  ###########
  coresDict, spotDict, objs, _ = getCores()
  ftxCore=coresDict['ftx']
  bbCore=coresDict['bb']
  bbtCores=coresDict['bbt']
  dbCore=coresDict['db']
  kfCore=coresDict['kf']
  kutCores=coresDict['kut']

  #############
  # Aggregation
  #############
  nav, extCoinsNAV=getNAV(objs,spotDict)
  agDf = pd.DataFrame({'Ccy': CR_AG_CCY_DICT.keys(), 'SpotDelta': CR_AG_CCY_DICT.values(), 'FutDelta': [0] * len(CR_AG_CCY_DICT.keys())}).set_index('Ccy')
  oneDayIncome=0
  for obj in objs:
    oneDayIncome += obj.oneDayIncome
    for ccy in CR_AG_CCY_DICT.keys():
      agDf.loc[ccy,'SpotDelta']+=obj.spots.loc[ccy,'SpotDelta']
      agDf.loc[ccy,'FutDelta']+=obj.futures.loc[ccy,'FutDelta']
  oneDayIncome+=ftxCore.oneDayFlows

  ########
  # Output
  ########
  navList=[]
  for obj in objs:
    if obj.name!='DUMMY': navList.append(getNAVStr(obj.name, obj.nav))
  if extCoinsNAV!=0: navList.append(getNAVStr('Ext Coins', extCoinsNAV))
  print(colored(('NAV as of '+cl.getCurrentTime()+': $').rjust(38) + str(round(nav)) +' (' +' / '.join(navList) + ')', 'blue'))
  #####
  quoteList=[]
  for ccy in CR_QUOTE_CCY_DICT.keys():
    quoteList.append(ccy + '=' + str(round(spotDict[ccy], CR_QUOTE_CCY_DICT[ccy])))
  print(colored('24h income: $'.rjust(38)+(str(round(oneDayIncome))+' ('+str(round(oneDayIncome*365/nav*100))+'% p.a.)').ljust(26),'blue') +' / '.join(quoteList))
  print()
  #####
  agList=[]
  for ccy in CR_AG_CCY_DICT.keys():
    appendDeltas(agList, ccy, spotDict, agDf.loc[ccy, 'SpotDelta'], agDf.loc[ccy, 'FutDelta'])
  usdtCores=[]
  for core in bbtCores:
    usdtCores.append(core)
  for core in kutCores:
    usdtCores.append(core)
  appendUSDTDeltas(agList, ftxCore, spotDict, usdtCores)
  #####
  flowList=[]
  appendFlows(flowList, ftxCore, nav)
  #####
  printTwoLists(agList, flowList, 120)
  #####
  printAllQuad(ftxCore, kfCore, dbCore, bbCore)
  #####
  bbt_kut_list=[]
  for i in range(SHARED_EXCH_DICT['bbt']):
    bbt_kut_list.append(bbtCores[i])
  for i in range(SHARED_EXCH_DICT['kut']):
    bbt_kut_list.append(kutCores[i])
  while len(bbt_kut_list)>0:
    if len(bbt_kut_list)>=2:
      printAllDual(bbt_kut_list.pop(0), bbt_kut_list.pop(0))
    elif len(bbt_kut_list)==1:
      bbt_kut_list[0].printAll()
      break
  #####
  if '-f' in sys.argv:
    while True:
      time.sleep(1)