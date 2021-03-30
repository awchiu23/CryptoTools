import CryptoLib as cl
import pandas as pd
import datetime
import termcolor

###########
# Functions
###########
def getOneDay(df):
  df2=df.sort_index()
  return df2[df2.index > (df2.index[-1] - pd.DateOffset(days=1))]

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

def printDeltas(ccy,spot,spotDelta,futDelta):
  netDelta=spotDelta+futDelta
  print((ccy+' spot/fut/net delta: ').rjust(41)+str(round(spotDelta,2))+'/'+str(round(futDelta,2))+'/'+str(round(netDelta,2)) + \
    ' ($' + str(round(spotDelta * spot)) + '/$' + str(round(futDelta * spot)) + '/$' + str(round(netDelta * spot)) + ')')

#####

def ftxInit(ftx):
  def cleanBorrows(ftxPayments,ccy, df):
    df2 = df.copy()
    df2=df2[df2['coin']==ccy]
    df2.index = pd.to_datetime(df2.index).tz_localize(None)
    df2 = df2.sort_index()
    return df2.reindex(ftxPayments.index.unique()).fillna(0).copy()
  ######
  def getBorrowsLoans(ftxWallet,ftxPayments,ccy):
    tm = ftxPayments.index[-1]
    borrows = cleanBorrows(ftxPayments, ccy, pd.DataFrame(ftx.private_get_spot_margin_borrow_history({'limit': 1000})['result']).set_index('time'))
    cl.dfSetFloat(borrows, 'cost')
    loans = cleanBorrows(ftxPayments, ccy, pd.DataFrame(ftx.private_get_spot_margin_lending_history({'limit': 1000})['result']).set_index('time'))
    cl.dfSetFloat(loans, 'proceeds')
    prevBorrow = borrows.loc[tm]['cost']
    prevLoan = loans.loc[tm]['proceeds']
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
  ftxNotional=ftxPositions.loc[['BTC','ETH','FTT']]['FutDeltaUSD'].abs().sum()
  ######
  ftxPayments = pd.DataFrame(ftx.private_get_funding_payments()['result']).set_index('time')
  cl.dfSetFloat(ftxPayments, ['payment','rate'])
  ftxPayments.index = pd.to_datetime(ftxPayments.index).tz_localize(None)
  ftxPayments=getOneDay(ftxPayments)
  #####
  ftxPrevIncome = -ftxPayments.loc[ftxPayments.index[-1]]['payment'].sum()
  ftxPrevAnnRet = ftxPrevIncome * 24 * 365 / ftxNotional
  ftxOneDayIncome = -ftxPayments['payment'].sum()
  ftxOneDayAnnRet = ftxOneDayIncome * 365 / ftxNotional
  #####
  ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet,ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet=getBorrowsLoans(ftxWallet, ftxPayments, 'USD')
  ftxPrevBTCFlows, ftxPrevBTCFlowsAnnRet, ftxOneDayBTCFlows, ftxOneDayBTCFlowsAnnRet = getBorrowsLoans(ftxWallet, ftxPayments, 'BTC')
  ftxPrevETHFlows, ftxPrevETHFlowsAnnRet, ftxOneDayETHFlows, ftxOneDayETHFlowsAnnRet = getBorrowsLoans(ftxWallet, ftxPayments, 'ETH')
  ftxOneDayBTCFlows *= spotBTC
  ftxOneDayETHFlows*=spotETH
  #####
  ftxNAV = ftxWallet['usdValue'].sum()
  ftxMF = float(ftxInfo['marginFraction'])
  ftxMMReq = float(ftxInfo['maintenanceMarginRequirement'])
  #####
  return ftxWallet,ftxPositions,ftxPayments, \
         ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet, \
         ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet,ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet, \
         ftxPrevBTCFlows, ftxPrevBTCFlowsAnnRet, ftxOneDayBTCFlows, ftxOneDayBTCFlowsAnnRet, \
         ftxPrevETHFlows,ftxPrevETHFlowsAnnRet,ftxOneDayETHFlows,ftxOneDayETHFlowsAnnRet, \
         ftxNAV,ftxMF,ftxMMReq,spotBTC,spotETH,spotFTT

def ftxPrintFlowsSummary(ccy, oneDayFlows,oneDayFlowsAnnRet,prevFlows,prevFlowsAnnRet):
  z1 = '$' + str(round(oneDayFlows)) + ' (' + str(round(oneDayFlowsAnnRet * 100)) + '% p.a.)'
  z2 = '$' + str(round(prevFlows)) + ' (' + str(round(prevFlowsAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored(('FTX 24h/prev '+ccy+' flows: ').rjust(41) + z1 + ' / ' + z2, 'blue'))

def ftxPrintUSDBorrowLending(ftx,ftxWallet):
  estBorrow = cl.ftxGetEstBorrow(ftx,'USD')
  estLending = cl.ftxGetEstLending(ftx,'USD')
  usdBalance = ftxWallet.loc['USD', 'usdValue']
  print('FTX USD est borrow/lending rate: '.rjust(41) + str(round(estBorrow * 100)) + '%/' + str(round(estLending * 100))+ '% p.a. ($' + str(round(usdBalance))+')')

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

#####

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
  bnPayments = pd.DataFrame(bn.dapiPrivate_get_income({'incomeType': 'FUNDING_FEE'}))
  cl.dfSetFloat(bnPayments, 'income')
  bnPayments = bnPayments[['USD_PERP' in z for z in bnPayments['symbol']]]
  bnPayments['Ccy'] = [z[:3] for z in bnPayments['symbol']]
  bnPayments = bnPayments.set_index('Ccy').loc[['BTC', 'ETH']]
  bnPayments['incomeUSD'] = bnPayments['income']
  bnPayments.loc['BTC', 'incomeUSD'] *= spotBTC
  bnPayments.loc['ETH', 'incomeUSD'] *= spotETH
  bnPayments['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in bnPayments['time']]
  bnPayments = bnPayments.set_index('date')
  bnPayments = getOneDay(bnPayments)
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
  df = pd.DataFrame(bn.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP'}))
  cl.dfSetFloat(df, 'fundingRate')
  df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
  df = df.set_index('date')
  df=getOneDay(df)
  oneDayFunding = df['fundingRate'].mean() * 3 * 365
  prevFunding = df['fundingRate'][-1] * 3 * 365
  estFunding=cl.bnGetEstFunding(bn,ccy)
  printFunding('BN', bnPR, ccy, oneDayFunding, prevFunding, estFunding)

#####

def bbInit(bb,spotBTC,spotETH):
  def getPayments(ccy):
    start_time = int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))) * 1000)
    n=0
    df=pd.DataFrame()
    while True:
      n+=1
      tl=bb.v2_private_get_execution_list({'symbol': ccy + 'USD', 'start_time': start_time, 'limit': 1000, 'page':n})['result']['trade_list']
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
  bbPL=bbPL.set_index('Ccy').loc[['BTC', 'ETH']]
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
  bbPayments = getOneDay(bbPayments)
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

#####

def cbInit(cb,spotBTC,spotETH):
  bal=cb.fetch_balance()
  cbSpotDeltaBTC=bal['BTC']['total']
  cbSpotDeltaETH=bal['ETH']['total']
  cbNAV=cbSpotDeltaBTC*spotBTC+cbSpotDeltaETH*spotETH
  return cbSpotDeltaBTC,cbSpotDeltaETH,cbNAV

######
# Init
######
ftx=cl.ftxCCXTInit()
bn = cl.bnCCXTInit()
bb = cl.bbCCXTInit()
cb= cl.cbCCXTInit()

ftxWallet,ftxPositions,ftxPayments, \
  ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet, \
  ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet,ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet, \
  ftxPrevBTCFlows, ftxPrevBTCFlowsAnnRet, ftxOneDayBTCFlows, ftxOneDayBTCFlowsAnnRet, \
  ftxPrevETHFlows,ftxPrevETHFlowsAnnRet,ftxOneDayETHFlows,ftxOneDayETHFlowsAnnRet, \
  ftxNAV,ftxMF,ftxMMReq,spotBTC,spotETH,spotFTT = ftxInit(ftx)

bnBal, bnPR, bnPayments, \
  bnPrevIncome, bnPrevAnnRet, bnOneDayIncome, bnOneDayAnnRet, \
  bnNAV, bnLiqBTC, bnLiqETH = bnInit(bn, spotBTC, spotETH)

bbSpotDeltaBTC, bbSpotDeltaETH, bbPL, bbPayments, \
  bbPrevIncome, bbPrevAnnRet, bbOneDayIncome, bbOneDayAnnRet, \
  bbNAV, bbLiqBTC, bbLiqETH = bbInit(bb, spotBTC, spotETH)

cbSpotDeltaBTC,cbSpotDeltaETH,cbNAV=cbInit(cb,spotBTC,spotETH)

#############
# Aggregation
#############
nav=ftxNAV+bnNAV+bbNAV+cbNAV
oneDayIncome=ftxOneDayIncome+ftxOneDayUSDFlows+ftxOneDayBTCFlows+ftxOneDayETHFlows
oneDayIncome+=bnOneDayIncome+bbOneDayIncome

spotDeltaBTC=ftxWallet.loc['BTC','SpotDelta']
spotDeltaBTC+=bnBal.loc['BTC','SpotDelta']
spotDeltaBTC+=bbSpotDeltaBTC
spotDeltaBTC+=cbSpotDeltaBTC

futDeltaBTC=ftxPositions.loc['BTC','FutDelta']
futDeltaBTC+=bnPR.loc['BTC','FutDelta']
futDeltaBTC+=bbPL.loc['BTC','FutDelta']

spotDeltaETH=ftxWallet.loc['ETH','SpotDelta']
spotDeltaETH+=bnBal.loc['ETH','SpotDelta']
spotDeltaETH+=bbSpotDeltaETH
spotDeltaETH+=cbSpotDeltaETH

futDeltaETH=ftxPositions.loc['ETH','FutDelta']
futDeltaETH+=bnPR.loc['ETH','FutDelta']
futDeltaETH+=bbPL.loc['ETH','FutDelta']

spotDeltaFTT=ftxWallet.loc['FTT','SpotDelta']

futDeltaFTT=ftxPositions.loc['FTT','FutDelta']

########
# Output
########
cl.printHeader('CryptoReporter - '+cl.getCurrentTime())
z='NAV: $'.rjust(42)+str(round(nav))
z+=' (FTX: $' + str(round(ftxNAV/1000)) + 'K'
z+=' / BN: $' + str(round(bnNAV/1000)) + 'K'
z+=' / BB: $' + str(round(bbNAV/1000)) + 'K'
z+=' / CB: $' + str(round(cbNAV/1000)) + 'K)'
print(termcolor.colored(z,'blue'))
print(termcolor.colored('24h income: $'.rjust(42)+str(round(oneDayIncome))+' ('+str(round(oneDayIncome*365/nav*100))+'% p.a.)','blue'))
print()
ftxPrintFlowsSummary('USD',ftxOneDayUSDFlows,ftxOneDayUSDFlowsAnnRet,ftxPrevUSDFlows,ftxPrevUSDFlowsAnnRet)
ftxPrintUSDBorrowLending(ftx,ftxWallet)
print()
ftxPrintFlowsSummary('BTC',ftxOneDayBTCFlows,ftxOneDayBTCFlowsAnnRet,ftxPrevBTCFlows*spotBTC,ftxPrevBTCFlowsAnnRet)
ftxPrintCoinLending(ftx,ftxWallet,'BTC')
print()
ftxPrintFlowsSummary('ETH',ftxOneDayETHFlows,ftxOneDayETHFlowsAnnRet,ftxPrevETHFlows*spotETH,ftxPrevETHFlowsAnnRet)
ftxPrintCoinLending(ftx,ftxWallet,'ETH')
print()
printIncomes('FTX',ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet)
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'BTC')
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'ETH')
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'FTT')
print(termcolor.colored('FTX margin: '.rjust(41)+str(round(ftxMF*100,1))+'% (vs. '+str(round(ftxMMReq*100,1))+'% limit)','red'))
print()
printIncomes('BN',bnPrevIncome,bnPrevAnnRet,bnOneDayIncome,bnOneDayAnnRet)
bnPrintFunding(bn,bnPR,'BTC')
bnPrintFunding(bn,bnPR,'ETH')
zBTC='never' if bnLiqBTC==0 else str(round(bnLiqBTC*100,1))+'%'
zETH='never' if bnLiqETH==0 else str(round(bnLiqETH*100,1))+'%'
print(termcolor.colored('BN liquidation (BTC/ETH): '.rjust(41)+zBTC+'/'+zETH+' (of spot)','red'))
print()
printIncomes('BB',bbPrevIncome,bbPrevAnnRet,bbOneDayIncome,bbOneDayAnnRet)
bbPrintFunding(bb,bbPL,bbPayments,'BTC')
bbPrintFunding(bb,bbPL,bbPayments,'ETH')
print(termcolor.colored('BB liquidation (BTC/ETH): '.rjust(41)+str(round(bbLiqBTC*100,1))+'%/'+str(round(bbLiqETH*100,1))+'% (of spot)','red'))
print()
printDeltas('BTC',spotBTC,spotDeltaBTC,futDeltaBTC)
printDeltas('ETH',spotETH,spotDeltaETH,futDeltaETH)
printDeltas('FTT',spotFTT,spotDeltaFTT,futDeltaFTT)
