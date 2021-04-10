from CryptoParams import *
import CryptoLib as cl
import pandas as pd
import datetime
import termcolor
import sys
import time

###########
# Functions
###########
def getYest():
  return int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))))

def printIncomes(name,prevIncome,prevAnnRet,oneDayIncome,oneDayAnnRet):
  z1='$' + str(round(oneDayIncome)) + ' (' + str(round(oneDayAnnRet * 100)) + '% p.a.)'
  z2='$' + str(round(prevIncome)) + ' (' + str(round(prevAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored((name + ' 24h/prev funding income: ').rjust(41) + z1 + ' / ' + z2,'blue'))

def printFunding(name,df,ccy,oneDayFunding,prevFunding,estFunding,est2Funding=None):
  prefix=name + ' ' + ccy + ' 24h/prev/est'
  if name=='BB':
    prefix+='1/est2'
  prefix+=' funding rate:'
  suffix = str(round(oneDayFunding * 100)) + '%/' + str(round(prevFunding * 100)) + '%/' + str(round(estFunding * 100)) + '%'
  if name=='BB':
    suffix+='/' + str(round(est2Funding * 100)) + '%'
  suffix+=' p.a. ($' + str(round(df.loc[ccy, 'FutDeltaUSD'])) + ')'
  print(prefix.rjust(40) + ' ' + suffix)

def printLiq(name,liqBTC,liqETH):
  zBTC = 'never' if (liqBTC <= 0 or liqBTC >= 10) else str(round(liqBTC * 100)) + '%'
  zETH = 'never' if (liqETH <= 0 or liqETH >= 10) else str(round(liqETH * 100)) + '%'
  print(termcolor.colored((name+' liquidation (BTC/ETH): ').rjust(41) + zBTC + '/' + zETH + ' (of spot)', 'red'))

def printDeltas(ccy,spot,spotDelta,futDelta):
  netDelta=spotDelta+futDelta
  print((ccy+' spot/fut/net delta: ').rjust(41)+str(round(spotDelta,2))+'/'+str(round(futDelta,2))+'/'+str(round(netDelta,2)) + \
    ' ($' + str(round(spotDelta * spot)) + '/$' + str(round(futDelta * spot)) + '/$' + str(round(netDelta * spot)) + ')')

####################################################################################################

def ftxInit(ftx):
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
  ftxInfo = ftx.private_get_account()['result']
  ######
  ftxWallet=cl.ftxGetWallet(ftx)
  ftxWallet['SpotDelta']=ftxWallet['total']
  spotBTC = ftxWallet.loc['BTC','spot']
  spotETH = ftxWallet.loc['ETH','spot']
  spotFTT = ftxWallet.loc['FTT','spot']
  ######
  ftxPositions = pd.DataFrame(ftxInfo['positions'])
  cl.dfSetFloat(ftxPositions, 'size')
  ftxPositions['Ccy'] = [z[:3] for z in ftxPositions['future']]
  ftxPositions=ftxPositions.set_index('Ccy').loc[['BTC','ETH','FTT']]
  ftxPositions['FutDelta']=ftxPositions['size']
  ftxPositions.loc[ftxPositions['side']=='sell','FutDelta']*=-1
  ftxPositions['FutDeltaUSD'] = ftxPositions['FutDelta']
  ftxPositions.loc['BTC', 'FutDeltaUSD'] *= spotBTC
  ftxPositions.loc['ETH', 'FutDeltaUSD'] *= spotETH
  ftxPositions.loc['FTT', 'FutDeltaUSD'] *= spotFTT
  ftxNotional=ftxPositions['FutDeltaUSD'].abs().sum()
  ######
  ftxPayments = pd.DataFrame(ftx.private_get_funding_payments({'limit':1000,'start_time':getYest()})['result'])
  ftxPayments = ftxPayments.set_index('future',drop=False).loc[['BTC-PERP','ETH-PERP','FTT-PERP']].set_index('time')
  cl.dfSetFloat(ftxPayments, ['payment','rate'])
  ftxPayments=ftxPayments.sort_index()
  #####
  ftxPrevIncome = -ftxPayments.loc[ftxPayments.index[-1]]['payment'].sum()
  ftxPrevAnnRet = ftxPrevIncome * 24 * 365 / ftxNotional
  ftxOneDayIncome = -ftxPayments['payment'].sum()
  ftxOneDayAnnRet = ftxOneDayIncome * 365 / ftxNotional
  #####
  ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet,ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet=getBorrowsLoans(ftxWallet,  'USD')
  ftxPrevUSDTFlows,ftxPrevUSDTFlowsAnnRet,ftxOneDayUSDTFlows,ftxOneDayUSDTFlowsAnnRet=getBorrowsLoans(ftxWallet, 'USDT')
  ftxPrevBTCFlows, ftxPrevBTCFlowsAnnRet, ftxOneDayBTCFlows, ftxOneDayBTCFlowsAnnRet = getBorrowsLoans(ftxWallet, 'BTC')
  ftxPrevETHFlows, ftxPrevETHFlowsAnnRet, ftxOneDayETHFlows, ftxOneDayETHFlowsAnnRet = getBorrowsLoans(ftxWallet, 'ETH')
  ftxOneDayBTCFlows *= spotBTC
  ftxOneDayETHFlows*=spotETH
  #####
  ftxNAV = ftxWallet['usdValue'].sum()
  ftxMF = float(ftxInfo['marginFraction'])
  ftxMMReq = float(ftxInfo['maintenanceMarginRequirement'])
  ftxTotalPositionNotional = ftxNAV / ftxMF
  ftxCushion = (ftxMF - ftxMMReq) * ftxTotalPositionNotional
  ftxTotalDelta = ftxWallet.loc[['BTC','ETH', 'FTT'], 'usdValue'].sum() + ftxPositions['FutDeltaUSD'].sum()
  ftxLiq = 1-ftxCushion/ftxTotalDelta
  ftxFreeCollateral = float(ftxInfo['freeCollateral'])
  #####
  return ftxWallet,ftxPositions,ftxPayments, \
         ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet, \
         ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet,ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet, \
         ftxPrevUSDTFlows, ftxPrevUSDTFlowsAnnRet, ftxOneDayUSDTFlows, ftxOneDayUSDTFlowsAnnRet, \
         ftxPrevBTCFlows, ftxPrevBTCFlowsAnnRet, ftxOneDayBTCFlows, ftxOneDayBTCFlowsAnnRet, \
         ftxPrevETHFlows,ftxPrevETHFlowsAnnRet,ftxOneDayETHFlows,ftxOneDayETHFlowsAnnRet, \
         ftxNAV,ftxLiq,ftxMF,ftxMMReq,ftxFreeCollateral, \
         spotBTC,spotETH,spotFTT

def ftxPrintFlowsSummary(ccy, oneDayFlows,oneDayFlowsAnnRet,prevFlows,prevFlowsAnnRet):
  z1 = '$' + str(round(oneDayFlows)) + ' (' + str(round(oneDayFlowsAnnRet * 100)) + '% p.a.)'
  z2 = '$' + str(round(prevFlows)) + ' (' + str(round(prevFlowsAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored(('FTX 24h/prev '+ccy+' flows: ').rjust(41) + z1 + ' / ' + z2, 'blue'))

def ftxPrintBorrowLending(ftx,ftxWallet,nav,ccy):
  estBorrow = cl.ftxGetEstBorrow(ftx,ccy)
  estLending = cl.ftxGetEstLending(ftx,ccy)
  n = ftxWallet.loc[ccy, 'usdValue']
  z1 = '($' + str(round(n))+')'
  z2 = '(' + str(round(n/nav*100))+'% of NAV)'
  print(('FTX '+ccy+' est borrow/lending rate: ').rjust(41) + str(round(estBorrow * 100)) + '%/' + str(round(estLending * 100))+ '% p.a. '+ z1+' '+z2)

def ftxPrintCoinLending(ftx,ftxWallet,ccy):
  estLending = float(pd.DataFrame(ftx.private_get_spot_margin_lending_rates()['result']).set_index('coin').loc[ccy, 'estimate']) * 24 * 365
  coinBalance = ftxWallet.loc[ccy,'usdValue']
  print(('FTX '+ccy+' est lending rate: ').rjust(41) + str(round(estLending * 100)) + '% p.a. ($' + str(round(coinBalance)) + ')')

def ftxPrintFunding(ftx,ftxPositions,ftxPayments,ccy):
  df=ftxPayments[ftxPayments['future']==ccy+'-PERP']
  oneDayFunding = df['rate'].mean() * 24 * 365
  prevFunding = df['rate'][-1] * 24 * 365
  estFunding = cl.ftxGetEstFunding(ftx,ccy)
  printFunding('FTX',ftxPositions,ccy,oneDayFunding,prevFunding,estFunding)

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
  def getLiq(bbPL,ccy):
    liqPrice = float(bbPL.loc[ccy, 'liq_price'])
    markPrice = float(bbPL.loc[ccy, 'size']) / (float(bbPL.loc[ccy, 'position_value']) + float(bbPL.loc[ccy, 'unrealised_pnl']))
    return liqPrice/markPrice
  #####
  bbBal=bb.fetch_balance()
  bbSpotDeltaBTC=bbBal['BTC']['total']
  bbSpotDeltaETH=bbBal['ETH']['total']
  #####
  bbPL=bb.v2_private_get_position_list()['result']
  bbPL=pd.DataFrame([pos['data'] for pos in bbPL])
  cl.dfSetFloat(bbPL,'size')
  bbPL['Ccy'] = [z[:3] for z in bbPL['symbol']]
  bbPL=bbPL.set_index('Ccy').loc[['BTC','ETH']]
  bbPL['FutDeltaUSD']=bbPL['size']
  bbPL.loc[bbPL['side'] == 'Sell', 'FutDeltaUSD'] *= -1
  bbPL['FutDelta']=bbPL['FutDeltaUSD']
  bbPL.loc['BTC','FutDelta']/=spotBTC
  bbPL.loc['ETH','FutDelta']/=spotETH
  bbNotional=bbPL['FutDeltaUSD'].abs().sum()
  #####
  bbPayments=getPayments('BTC').append(getPayments('ETH'))
  cl.dfSetFloat(bbPayments,['fee_rate','exec_fee'])
  bbPayments['incomeUSD']=-bbPayments['exec_fee']
  bbPayments.loc['BTCUSD','incomeUSD']*=spotBTC
  bbPayments.loc['ETHUSD','incomeUSD']*=spotETH
  bbPayments=bbPayments[bbPayments['exec_type']=='Funding']
  bbPayments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in bbPayments['trade_time_ms']]
  bbPayments=bbPayments.set_index('date')
  #####
  bbPrevIncome = bbPayments.loc[bbPayments.index[-1]]['incomeUSD'].sum()
  bbPrevAnnRet = bbPrevIncome * 3 * 365 / bbNotional
  bbOneDayIncome = bbPayments['incomeUSD'].sum()
  bbOneDayAnnRet = bbOneDayIncome * 365 / bbNotional
  #####
  bbNAV = bbSpotDeltaBTC * spotBTC + bbSpotDeltaETH * spotETH
  bbLiqBTC = getLiq(bbPL,'BTC')
  bbLiqETH = getLiq(bbPL,'ETH')
  #####
  return bbSpotDeltaBTC, bbSpotDeltaETH, bbPL, bbPayments, \
         bbPrevIncome, bbPrevAnnRet, bbOneDayIncome, bbOneDayAnnRet, \
         bbNAV,bbLiqBTC,bbLiqETH

def bbPrintFunding(bb,bbPL,bbPayments,ccy):
  df=bbPayments[bbPayments['symbol']==ccy + 'USD'].copy()
  for i in range(len(df)):
    if 'Sell' in df.iloc[i]['order_id']:
      df.loc[df.index[i],'fee_rate']*=-1
  oneDayFunding = df['fee_rate'].mean() * 3 * 365
  prevFunding = df['fee_rate'][-1] * 3 * 365
  estFunding1 = cl.bbGetEstFunding1(bb,ccy)
  estFunding2 = cl.bbGetEstFunding2(bb,ccy)
  printFunding('BB', bbPL, ccy, oneDayFunding, prevFunding, estFunding1,estFunding2)

####################################################################################################

def bnInit(bn,spotBTC,spotETH):
  bnBal = pd.DataFrame(bn.dapiPrivate_get_balance())
  cl.dfSetFloat(bnBal, ['balance', 'crossUnPnl'])
  bnBal['Ccy']=bnBal['asset']
  bnBal=bnBal.set_index('Ccy').loc[['BTC','ETH']]
  bnBal['SpotDelta']=bnBal['balance']+bnBal['crossUnPnl']
  #####
  bnPR = pd.DataFrame(bn.dapiPrivate_get_positionrisk())
  cl.dfSetFloat(bnPR, 'positionAmt')
  bnPR = bnPR[['USD_PERP' in z for z in bnPR['symbol']]]
  bnPR['Ccy'] = [z[:3] for z in bnPR['symbol']]
  bnPR=bnPR.set_index('Ccy').loc[['BTC','ETH']]
  bnPR['FutDeltaUSD']=bnPR['positionAmt']
  bnPR.loc['BTC', 'FutDeltaUSD'] *= 100
  bnPR.loc['ETH', 'FutDeltaUSD'] *= 10
  bnPR['FutDelta']=bnPR['FutDeltaUSD']
  bnPR.loc['BTC','FutDelta']/=spotBTC
  bnPR.loc['ETH','FutDelta']/=spotETH
  bnNotional=bnPR['FutDeltaUSD'].abs().sum()
  #####
  bnPayments = pd.DataFrame(bn.dapiPrivate_get_income({'incomeType': 'FUNDING_FEE','startTime':getYest()*1000}))
  cl.dfSetFloat(bnPayments, 'income')
  bnPayments = bnPayments[['USD_PERP' in z for z in bnPayments['symbol']]]
  bnPayments['Ccy'] = [z[:3] for z in bnPayments['symbol']]
  bnPayments = bnPayments.set_index('Ccy').loc[['BTC','ETH']]
  bnPayments['incomeUSD'] = bnPayments['income']
  bnPayments.loc['BTC', 'incomeUSD'] *= spotBTC
  bnPayments.loc['ETH', 'incomeUSD'] *= spotETH
  bnPayments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in bnPayments['time']]
  bnPayments = bnPayments.set_index('date')
  #####
  bnPrevIncome = bnPayments.loc[bnPayments.index[-1]]['incomeUSD'].sum()
  bnPrevAnnRet = bnPrevIncome * 3 * 365 / bnNotional
  bnOneDayIncome = bnPayments['incomeUSD'].sum()
  bnOneDayAnnRet = bnOneDayIncome * 365 / bnNotional
  #####
  bnNAV = bnBal.loc['BTC','SpotDelta'] * spotBTC +  bnBal.loc['ETH', 'SpotDelta'] * spotETH
  bnLiqBTC=float(bnPR.loc['BTC', 'liquidationPrice']) / float(bnPR.loc['BTC', 'markPrice'])
  bnLiqETH=float(bnPR.loc['ETH', 'liquidationPrice']) / float(bnPR.loc['ETH', 'markPrice'])
  #####
  return bnBal, bnPR, bnPayments, \
         bnPrevIncome, bnPrevAnnRet, bnOneDayIncome, bnOneDayAnnRet, \
         bnNAV, bnLiqBTC, bnLiqETH

def bnPrintFunding(bn,bnPR,ccy):
  df = pd.DataFrame(bn.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP','startTime':getYest()*1000}))
  cl.dfSetFloat(df, 'fundingRate')
  df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
  df = df.set_index('date').sort_index()
  oneDayFunding = df['fundingRate'].mean() * 3 * 365
  prevFunding = df['fundingRate'][-1] * 3 * 365
  estFunding=cl.bnGetEstFunding(bn,ccy)
  printFunding('BN', bnPR, ccy, oneDayFunding, prevFunding, estFunding)

####################################################################################################

def dbInit(db,spotBTC,spotETH):
  def getFutPos(db,ccy):
    return float(db.private_get_get_position({'instrument_name': ccy+'-PERPETUAL'})['result']['size'])
  #####
  def get4pmIncome(db,ccy,spot):
    df= pd.DataFrame(db.private_get_get_settlement_history_by_currency({'currency': ccy})['result']['settlements'])
    if len(df)>0:
      cl.dfSetFloat(df, 'funding')
      df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['timestamp']]
      df=df.set_index('date').sort_index()
      return df['funding'].iloc[-1]*spot
    else:
      return 0
  #####
  def getLiq(dbAS,dbFutures,ccy):
    totalDelta = float(dbAS['equity']) + dbFutures.loc[ccy,'FutDelta']
    cushion=float(dbAS['margin_balance']) - float(dbAS['maintenance_margin'])
    return 1-cushion/totalDelta
  #####
  dbASBTC = db.private_get_get_account_summary({'currency': 'BTC'})['result']
  dbASETH = db.private_get_get_account_summary({'currency': 'ETH'})['result']
  dbSpotDeltaBTC = float(dbASBTC['equity'])
  dbSpotDeltaETH = float(dbASETH['equity'])
  dbFutures = pd.DataFrame([['BTC', spotBTC, getFutPos(db, 'BTC')], ['ETH', spotETH, getFutPos(db, 'ETH')]], columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
  dbFutures['FutDelta'] = dbFutures['FutDeltaUSD'] / dbFutures['Spot']
  dbNotional = dbFutures['FutDeltaUSD'].abs().sum()
  #####
  db4pmIncome=get4pmIncome(db,'BTC',spotBTC)+get4pmIncome(db,'ETH',spotETH)
  db4pmAnnRet = db4pmIncome * 365 / dbNotional
  #####
  dbNAV = dbSpotDeltaBTC * spotBTC + dbSpotDeltaETH * spotETH
  #####
  if dbASBTC['portfolio_margining_enabled']:
    dbLiqBTC=getLiq(dbASBTC,dbFutures,'BTC')
    dbLiqETH=getLiq(dbASETH, dbFutures, 'ETH')
  else:
    dbLiqBTC=float(dbASBTC['estimated_liquidation_ratio'])
    dbLiqETH=float(dbASETH['estimated_liquidation_ratio'])
  #####
  return dbSpotDeltaBTC, dbSpotDeltaETH, dbFutures, \
         db4pmIncome, db4pmAnnRet, \
         dbNAV, dbLiqBTC, dbLiqETH

def dbPrintIncomes(_4pmIncome,_4pmAnnRet):
  z1='$' + str(round(_4pmIncome)) + ' (' + str(round(_4pmAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored(('DB 4pm funding income: ').rjust(41) + z1,'blue'))

def dbPrintFunding(db,dbFutures,ccy):
  oneDayFunding = cl.dbGetEstFunding(db,ccy,mins=60*24)
  estFunding=cl.dbGetEstFunding(db,ccy)
  prefix='DB ' + ccy + ' 24h/est funding rate:'
  suffix = str(round(oneDayFunding * 100)) + '%/' + str(round(estFunding * 100)) + '% p.a. ($' + str(round(dbFutures.loc[ccy, 'FutDeltaUSD'])) + ')'
  print(prefix.rjust(40) + ' ' + suffix)

####################################################################################################

def kfInit(kf,spotBTC,spotETH):
  kfAccounts = kf.query('accounts')['accounts']
  kfSpotDeltaBTC=kfAccounts['fi_xbtusd']['auxiliary']['pv']+kfAccounts['cash']['balances']['xbt']
  kfSpotDeltaETH=kfAccounts['fi_ethusd']['auxiliary']['pv']+kfAccounts['cash']['balances']['eth']
  kfFutures = pd.DataFrame([['BTC', spotBTC, kfAccounts['fi_xbtusd']['balances']['pi_xbtusd']], \
                            ['ETH', spotETH, kfAccounts['fi_ethusd']['balances']['pi_ethusd']]], \
                           columns=['Ccy', 'Spot', 'FutDeltaUSD']).set_index('Ccy')
  kfFutures['FutDelta'] = kfFutures['FutDeltaUSD'] / kfFutures['Spot']
  kfNotional=kfFutures['FutDeltaUSD'].abs().sum()
  #####
  kfTickers=cl.kfGetTickers(kf)  
  kfOneDayIncome=-kfFutures.loc['BTC','FutDeltaUSD']*cl.kfGetEstFunding1(kf,'BTC',kfTickers)/365
  kfOneDayIncome-=kfFutures.loc['ETH','FutDeltaUSD']*cl.kfGetEstFunding1(kf,'ETH',kfTickers)/365
  kfOneDayAnnRet = kfOneDayIncome * 365 / kfNotional
  #####
  kfNAV = kfSpotDeltaBTC * spotBTC + kfSpotDeltaETH * spotETH
  kfLiqBTC = kfAccounts['fi_xbtusd']['triggerEstimates']['im']/spotBTC
  kfLiqETH = kfAccounts['fi_ethusd']['triggerEstimates']['im']/spotETH
  #####
  return kfSpotDeltaBTC, kfSpotDeltaETH, kfFutures, \
         kfOneDayIncome, kfOneDayAnnRet, \
         kfNAV, kfLiqBTC, kfLiqETH

def kfPrintIncomes(oneDayIncome,oneDayAnnRet):
  z1='$' + str(round(oneDayIncome)) + ' (' + str(round(oneDayAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored(('KF 24h funding income: ').rjust(41) + z1,'blue'))

def kfPrintFunding(kf,kfFutures,ccy):
  kfTickers=cl.kfGetTickers(kf)
  estFunding1=cl.kfGetEstFunding1(kf,ccy,kfTickers)
  estFunding2 = cl.kfGetEstFunding2(kf, ccy, kfTickers)
  prefix='KF ' + ccy + ' est1/est2 funding rate:'
  suffix = str(round(estFunding1 * 100)) + '%/'+str(round(estFunding2 * 100))+'% p.a. ($' + str(round(kfFutures.loc[ccy, 'FutDeltaUSD'])) + ')'
  print(prefix.rjust(40) + ' ' + suffix)

####################################################################################################

def krInit(kr, spotBTC):
  def getLedgersRaw(kr,start,ofs):
    while True:
      try:
        return pd.DataFrame(kr.private_post_ledgers({'type': 'rollover', 'start': start, 'ofs': ofs})['result']['ledger'])
      except:
        print('Cooling off for Kraken API ....')
        time.sleep(10)
  def getBTCLedgers(kr, spotBTC):
    yest = getYest()
    n = 0
    while True:
      df = getLedgersRaw(kr,yest,n).transpose()
      if len(df) == 0:
        break
      if n == 0:
        ledgers = df
      else:
        ledgers = ledgers.append(df)
      n += 50
    cl.dfSetFloat(ledgers, ['time', 'fee'])
    ledgers['feeUSD'] = ledgers['fee'] * spotBTC
    ledgers['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in ledgers['time']]
    return ledgers.set_index('date').sort_index()
  #####
  krBalance=kr.private_post_balance()['result']
  krSpotDeltaBTC = float(krBalance['XXBT'])
  krSpotDeltaETH = float(krBalance['XETH'])
  #####
  krPositions = pd.DataFrame(kr.private_post_openpositions()['result']).transpose().set_index('pair')
  if 'XXETHUSD' in krPositions.index:
    print('Cannot handle ETH margined spots in Kraken!')
    sys.exit(1)
  krPositions=krPositions.loc['XXBTZUSD'] # From this point onwards only handle BTC
  cl.dfSetFloat(krPositions, ['vol', 'vol_closed', 'time'])
  krPositions['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in krPositions['time']]
  krPositions['vol_net'] = krPositions['vol']- krPositions['vol_closed']
  krMarginDelta = krPositions['vol_net'].sum()
  krSpotDeltaBTC+=krMarginDelta
  krMarginDeltaUSD = krMarginDelta * spotBTC
  krNotional = krPositions['vol_net'].abs().sum() * spotBTC
  #####
  if CR_IS_FAST:
    krOneDayIncome=-krMarginDeltaUSD*0.0001*6
  else:
    krOneDayIncome = -getBTCLedgers(kr, spotBTC)['feeUSD'].sum()
  krOneDayAnnRet = krOneDayIncome * 365 / krNotional
  #####
  krTradeBal = kr.private_post_tradebalance()['result']
  krNAV = float(krTradeBal['e'])
  #####
  krFreeMargin = float(krTradeBal['mf'])
  krLiqBTC = 1 - krFreeMargin / (krSpotDeltaBTC * spotBTC)
  #####
  return krSpotDeltaBTC, krSpotDeltaETH, krMarginDeltaUSD, \
         krOneDayIncome, krOneDayAnnRet, \
         krNAV, krLiqBTC

def krPrintIncomes(oneDayIncome, oneDayAnnRet):
  z1 = '$' + str(round(oneDayIncome)) + ' (' + str(round(oneDayAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored('KR 24h rollover fees: '.rjust(41) + z1, 'blue'))

def krPrintBorrow(marginDeltaUSD, oneDayAnnRet, nav):
  z1 = '($' + str(round(-marginDeltaUSD)) + ')'
  z2 = '(' + str(round(-marginDeltaUSD / nav * 100)) + '% of NAV)'
  print('KR USD est borrow rate: '.rjust(41) + str(round(-oneDayAnnRet * 100)) + '% p.a. ' + z1 + ' ' + z2)

####################################################################################################

def cbInit(cb,spotBTC,spotETH):
  bal=cb.fetch_balance()
  cbSpotDeltaBTC=bal['BTC']['total']
  cbSpotDeltaETH=bal['ETH']['total']
  cbNAV=cbSpotDeltaBTC*spotBTC+cbSpotDeltaETH*spotETH
  return cbSpotDeltaBTC,cbSpotDeltaETH,cbNAV

####################################################################################################

######
# Init
######
cl.printHeader('CryptoReporter - '+cl.getCurrentTime())
ftx=cl.ftxCCXTInit()
bb = cl.bbCCXTInit()
cb= cl.cbCCXTInit()

ftxWallet,ftxPositions,ftxPayments, \
  ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet, \
  ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet,ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet, \
  ftxPrevUSDTFlows, ftxPrevUSDTFlowsAnnRet, ftxOneDayUSDTFlows, ftxOneDayUSDTFlowsAnnRet, \
  ftxPrevBTCFlows, ftxPrevBTCFlowsAnnRet, ftxOneDayBTCFlows, ftxOneDayBTCFlowsAnnRet, \
  ftxPrevETHFlows,ftxPrevETHFlowsAnnRet,ftxOneDayETHFlows,ftxOneDayETHFlowsAnnRet, \
  ftxNAV, ftxLiq, ftxMF, ftxMMReq, ftxFreeCollateral, \
  spotBTC, spotETH, spotFTT = ftxInit(ftx)

bbSpotDeltaBTC, bbSpotDeltaETH, bbPL, bbPayments, \
  bbPrevIncome, bbPrevAnnRet, bbOneDayIncome, bbOneDayAnnRet, \
  bbNAV, bbLiqBTC, bbLiqETH = bbInit(bb, spotBTC, spotETH)

cbSpotDeltaBTC,cbSpotDeltaETH,cbNAV=cbInit(cb,spotBTC,spotETH)

if CR_IS_ADVANCED:
  bn = cl.bnCCXTInit()
  db = cl.dbCCXTInit()
  kf = cl.kfInit()
  kr = cl.krCCXTInit()

  bnBal, bnPR, bnPayments, \
    bnPrevIncome, bnPrevAnnRet, bnOneDayIncome, bnOneDayAnnRet, \
    bnNAV, bnLiqBTC, bnLiqETH = bnInit(bn, spotBTC, spotETH)

  dbSpotDeltaBTC, dbSpotDeltaETH, dbFutures, \
    db4pmIncome, db4pmAnnRet, \
    dbNAV, dbLiqBTC, dbLiqETH = dbInit(db, spotBTC, spotETH)

  kfSpotDeltaBTC, kfSpotDeltaETH, kfFutures, \
    kfOneDayIncome, kfOneDayAnnRet, \
    kfNAV, kfLiqBTC, kfLiqETH = kfInit(kf,spotBTC,spotETH)

  krSpotDeltaBTC, krSpotDeltaETH, krMarginDeltaUSD, \
    krOneDayIncome, krOneDayAnnRet, \
    krNAV, krLiqBTC = krInit(kr, spotBTC)

#############
# Aggregation
#############
nav=ftxNAV+bbNAV+cbNAV
oneDayIncome=ftxOneDayIncome+ftxOneDayUSDFlows+ftxOneDayUSDTFlows+ftxOneDayBTCFlows+ftxOneDayETHFlows+bbOneDayIncome
if CR_IS_ADVANCED:
  nav+=bnNAV+dbNAV+kfNAV+krNAV
  oneDayIncome += bnOneDayIncome + db4pmIncome + kfOneDayIncome + krOneDayIncome

spotDeltaBTC=ftxWallet.loc['BTC','SpotDelta']
spotDeltaBTC+=bbSpotDeltaBTC
spotDeltaBTC+=cbSpotDeltaBTC
if CR_IS_ADVANCED:
  spotDeltaBTC+=bnBal.loc['BTC','SpotDelta']
  spotDeltaBTC+=dbSpotDeltaBTC
  spotDeltaBTC += kfSpotDeltaBTC
  spotDeltaBTC+=krSpotDeltaBTC

futDeltaBTC=ftxPositions.loc['BTC','FutDelta']
futDeltaBTC+=bbPL.loc['BTC','FutDelta']
if CR_IS_ADVANCED:
  futDeltaBTC+=bnPR.loc['BTC','FutDelta']
  futDeltaBTC+=dbFutures.loc['BTC','FutDelta']
  futDeltaBTC+=kfFutures.loc['BTC', 'FutDelta']

spotDeltaETH=ftxWallet.loc['ETH','SpotDelta']
spotDeltaETH+=bbSpotDeltaETH
spotDeltaETH+=cbSpotDeltaETH
if CR_IS_ADVANCED:
  spotDeltaETH+=bnBal.loc['ETH','SpotDelta']
  spotDeltaETH+=dbSpotDeltaETH
  spotDeltaETH+=kfSpotDeltaETH
  spotDeltaETH+=krSpotDeltaETH

futDeltaETH=ftxPositions.loc['ETH','FutDelta']
futDeltaETH+=bbPL.loc['ETH','FutDelta']
if CR_IS_ADVANCED:
  futDeltaETH+=bnPR.loc['ETH','FutDelta']
  futDeltaETH+=dbFutures.loc['ETH','FutDelta']
  futDeltaETH+=kfFutures.loc['ETH', 'FutDelta']

spotDeltaFTT=ftxWallet.loc['FTT','SpotDelta']
futDeltaFTT=ftxPositions.loc['FTT','FutDelta']

########
# Output
########
z='NAV: $'.rjust(42)+str(round(nav))
z+=' (FTX: $' + str(round(ftxNAV/1000)) + 'K'
z+=' / BB: $' + str(round(bbNAV/1000)) + 'K'
if CR_IS_ADVANCED:
  z+=' / BN: $' + str(round(bnNAV/1000)) + 'K'
  z+=' / DB: $' + str(round(dbNAV/1000)) + 'K'
  z += ' / KF: $' + str(round(kfNAV / 1000)) + 'K'
  z+=' / KR: $' + str(round(krNAV/1000)) + 'K'
z+=' / CB: $' + str(round(cbNAV/1000)) + 'K)'
print(termcolor.colored(z,'blue'))
print(termcolor.colored('24h income: $'.rjust(42)+str(round(oneDayIncome))+' ('+str(round(oneDayIncome*365/nav*100))+'% p.a.)','blue'))
print()
ftxPrintFlowsSummary('USD',ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet,ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet)
ftxPrintFlowsSummary('USDT',ftxOneDayUSDTFlows,ftxOneDayUSDTFlowsAnnRet,ftxPrevUSDTFlows,ftxPrevUSDTFlowsAnnRet)
ftxPrintBorrowLending(ftx,ftxWallet,nav,'USD')
ftxPrintBorrowLending(ftx,ftxWallet,nav,'USDT')
print()
#####
if CR_IS_SHOW_COIN_LENDING:
  ftxPrintFlowsSummary('BTC',ftxOneDayBTCFlows,ftxOneDayBTCFlowsAnnRet,ftxPrevBTCFlows*spotBTC,ftxPrevBTCFlowsAnnRet)
  ftxPrintFlowsSummary('ETH',ftxOneDayETHFlows,ftxOneDayETHFlowsAnnRet,ftxPrevETHFlows*spotETH,ftxPrevETHFlowsAnnRet)
  ftxPrintCoinLending(ftx,ftxWallet,'BTC')
  ftxPrintCoinLending(ftx,ftxWallet,'ETH')
  print()
#####
printIncomes('FTX',ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet)
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'BTC')
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'ETH')
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'FTT')
z = 'never' if (ftxLiq <=0 or ftxLiq > 10) else str(round(ftxLiq * 100)) + '%'
print(termcolor.colored('FTX liquidation (parallel shock): '.rjust(41) + z + ' (of spot)', 'red'))
print(termcolor.colored('FTX margin fraction: '.rjust(41)+str(round(ftxMF*100,1))+'% (vs. '+str(round(ftxMMReq*100,1))+'% limit)','red'))
print(termcolor.colored('FTX free collateral: $'.rjust(42)+str(round(ftxFreeCollateral)),'red'))
print()
#####
printIncomes('BB',bbPrevIncome,bbPrevAnnRet,bbOneDayIncome,bbOneDayAnnRet)
bbPrintFunding(bb,bbPL,bbPayments,'BTC')
bbPrintFunding(bb,bbPL,bbPayments,'ETH')
printLiq('BB',bbLiqBTC,bbLiqETH)
print()
#####
if CR_IS_ADVANCED:
  printIncomes('BN',bnPrevIncome,bnPrevAnnRet,bnOneDayIncome,bnOneDayAnnRet)
  bnPrintFunding(bn,bnPR,'BTC')
  bnPrintFunding(bn,bnPR,'ETH')
  printLiq('BN',bnLiqBTC,bnLiqETH)
  print()
  #####
  dbPrintIncomes(db4pmIncome,db4pmAnnRet)
  dbPrintFunding(db,dbFutures,'BTC')
  dbPrintFunding(db,dbFutures,'ETH')
  printLiq('DB',dbLiqBTC,dbLiqETH)
  print()
  #####
  kfPrintIncomes(kfOneDayIncome,kfOneDayAnnRet)
  kfPrintFunding(kf, kfFutures, 'BTC')
  kfPrintFunding(kf, kfFutures, 'ETH')
  printLiq('KF', kfLiqBTC, kfLiqETH)
  print()
  #####
  krPrintIncomes(krOneDayIncome,krOneDayAnnRet)
  krPrintBorrow(krMarginDeltaUSD,krOneDayAnnRet,nav)
  z = 'never' if (krLiqBTC <= 0 or krLiqBTC > 10) else str(round(krLiqBTC * 100)) + '%'
  print(termcolor.colored('KR liquidation (BTC): '.rjust(41) + z + ' (of spot)', 'red'))
  print()
  #####
#####
printDeltas('BTC',spotBTC,spotDeltaBTC,futDeltaBTC)
printDeltas('ETH',spotETH,spotDeltaETH,futDeltaETH)
printDeltas('FTT',spotFTT,spotDeltaFTT,futDeltaFTT)
