import CryptoLib as cl
import pandas as pd
import datetime
import ccxt
import termcolor

###########
# Functions
###########
def getOneDay(df):
  df=df.sort_index()
  return df[df.index > df.index[-1] - pd.DateOffset(days=1)]   

def printFunding(name,df,ccy,oneDayFunding,prevFunding,estFunding,est2Funding=None):
  prefix=name + ' ' + ccy + ' 24h/prev/est'
  if name=='Bybit':
    prefix+='1/est2'
  prefix+=' funding:'
  suffix = str(round(oneDayFunding * 100)) + '%/' + str(round(prevFunding * 100)) + '%/' + str(round(estFunding * 100)) + '%'
  if name=='Bybit':
    suffix+='/' + str(round(est2Funding * 100)) + '%'
  suffix+=' p.a. ($' + str(round(df.loc[ccy, 'FutDeltaUSD'])) + ')'
  print(prefix.rjust(40) + ' ' + suffix)

def printIncomes(name,prevIncome,prevAnnRet,oneDayIncome,oneDayAnnRet):
  z1='$' + str(round(oneDayIncome)) + ' (' + str(round(oneDayAnnRet * 100)) + '% p.a.)'
  z2='$' + str(round(prevIncome)) + ' (' + str(round(prevAnnRet * 100)) + '% p.a.)'
  print(termcolor.colored((name + ' 24h/prev income: ').rjust(41) + z1 + ' / ' + z2,'blue'))

def printDeltas(ccy,spot,spotDelta,futDelta):
  netDelta=spotDelta+futDelta
  print((ccy+' spot/fut/net delta: ').rjust(41)+str(round(spotDelta,2))+'/'+str(round(futDelta,2))+'/'+str(round(netDelta,2)) + \
    ' ($' + str(round(spotDelta * spot)) + '/$' + str(round(futDelta * spot)) + '/$' + str(round(netDelta * spot)) + ')')

def ftxInit(ftx):
  ftxInfo = ftx.private_get_account()['result']
  ######
  ftxWallet = pd.DataFrame(ftx.private_get_wallet_all_balances()['result']['main'])
  ftxWallet['Ccy']=ftxWallet['coin']
  ftxWallet['SpotDelta']=ftxWallet['total']
  ftxWallet=ftxWallet.set_index('Ccy').loc[['BTC','ETH','FTT','USD']]
  spotBTC = ftxWallet.loc['BTC', 'usdValue'] / ftxWallet.loc['BTC', 'total']
  spotETH = ftxWallet.loc['ETH', 'usdValue'] / ftxWallet.loc['ETH', 'total']
  spotFTT = ftxWallet.loc['FTT', 'usdValue'] / ftxWallet.loc['FTT', 'total']
  ######
  ftxPositions = pd.DataFrame(ftxInfo['positions'])
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
  ftxPayments.index = pd.to_datetime(ftxPayments.index).tz_localize(None)
  ftxPayments=getOneDay(ftxPayments)
  ftxTDiff = ftxPayments.index[-1] - ftxPayments.index[0]
  ftxNDays = ftxTDiff.days + (ftxTDiff.seconds + 3600) / 86400
  #####
  ftxBorrows = pd.DataFrame(ftx.private_get_spot_margin_borrow_history()['result']).set_index('time')
  ftxBorrows.index = pd.to_datetime(ftxBorrows.index).tz_localize(None)
  ftxBorrows=getOneDay(ftxBorrows)  
  #####
  ftxLoans=pd.DataFrame(ftx.private_get_spot_margin_lending_history()['result']).set_index('time')
  ftxLoans.index = pd.to_datetime(ftxLoans.index).tz_localize(None)
  ftxLoans = getOneDay(ftxLoans)
  #####
  tm=ftxPayments.index[-1]
  ftxPrevPayment=-ftxPayments.loc[tm]['payment'].sum()
  try:
    ftxPrevBorrow=ftxBorrows.loc[tm]['cost'].sum()
  except:
    ftxPrevBorrow=0
  try:
    ftxPrevLoan=ftxLoans.loc[tm]['proceeds'].sum()
  except:
    ftxPrevLoan=0
  ftxPrevIncome = ftxPrevPayment-ftxPrevBorrow+ftxPrevLoan
  ftxPrevAnnRet = ftxPrevIncome * 24 * 365 / ftxNotional
  ftxOneDayIncome = -ftxPayments['payment'].sum() - ftxBorrows['cost'].sum() + ftxLoans['proceeds'].sum()
  ftxOneDayAnnRet = (ftxOneDayIncome / ftxNDays * 365) / ftxNotional
  #####
  ftxNAV = ftxWallet['usdValue'].sum()
  ftxMF = ftxInfo['marginFraction']
  ftxMMReq = ftxInfo['maintenanceMarginRequirement']
  #####
  return ftxWallet,ftxPositions,ftxPayments,ftxBorrows, \
         ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet, \
         ftxNAV,ftxMF,ftxMMReq,spotBTC,spotETH,spotFTT

def ftxPrintFunding(ftx,ftxPositions,ftxPayments,ccy):
  df=ftxPayments[ftxPayments['future']==ccy+'-PERP']
  oneDayFunding = df['rate'].mean() * 24 * 365
  prevFunding = df['rate'][-1] * 24 * 365
  estFunding = cl.ftxGetEstFunding(ftx,ccy)
  printFunding('FTX',ftxPositions,ccy,oneDayFunding,prevFunding,estFunding)

def ftxGetEstBorrow(ftx):
  while True:
    try:
      eb = pd.DataFrame(ftx.private_get_spot_margin_borrow_rates()['result']).set_index('coin').loc['USD', 'estimate'] * 24 * 365
    except:
      continue
    else:
      break
  return eb

def ftxPrintBorrow(ftx,ftxWallet,ftxBorrows):
  df=ftxBorrows[ftxBorrows['coin']=='USD']
  if len(df)>0:
    oneDayBorrow = df['cost'].sum()/df['size'].sum()*24*365
    prevBorrow = df['rate'][-1] * 24 * 365
  else:
    oneDayBorrow =0
    prevBorrow = 0
  estBorrow = cl.ftxGetEstBorrow(ftx)
  usdBalance = ftxWallet.loc['USD', 'total']
  print('FTX USD 24h/prev/est borrow: '.rjust(41) + str(round(oneDayBorrow * 100)) + '%/' + str(round(prevBorrow * 100)) + '%/' + str(round(estBorrow * 100)) + \
        '% p.a. ($' + str(round(usdBalance))+')')

def bnInit(bn,spotBTC,spotETH):
  bnBal = pd.DataFrame(bn.dapiPrivate_get_balance())
  bnBal['Ccy']=bnBal['asset']
  bnBal=bnBal.set_index('Ccy').loc[['BTC','ETH']]
  bnBal['balance']=[float(z) for z in bnBal['balance']]
  bnBal['crossUnPnl']=[float(z) for z in bnBal['crossUnPnl']]
  bnBal['SpotDelta']=bnBal['balance']+bnBal['crossUnPnl']
  #####
  bnPR = pd.DataFrame(bn.dapiPrivate_get_positionrisk())
  bnPR = bnPR[['USD_PERP' in z for z in bnPR['symbol']]]
  bnPR['Ccy'] = [z[:3] for z in bnPR['symbol']]
  bnPR=bnPR.set_index('Ccy').loc[['BTC','ETH']]
  bnPR['FutDeltaUSD']=bnPR['positionAmt']
  bnPR['FutDeltaUSD'] = [float(z) for z in bnPR['FutDeltaUSD']]
  bnPR.loc['BTC', 'FutDeltaUSD'] *= 100
  bnPR.loc['ETH', 'FutDeltaUSD'] *= 10
  bnPR['FutDelta']=bnPR['FutDeltaUSD']
  bnPR.loc['BTC','FutDelta']/=spotBTC
  bnPR.loc['ETH','FutDelta']/=spotETH
  bnNotional=bnPR['FutDeltaUSD'].abs().sum()
  #####
  bnPayments = pd.DataFrame(bn.dapiPrivate_get_income({'incomeType': 'FUNDING_FEE'}))
  bnPayments = bnPayments[['USD_PERP' in z for z in bnPayments['symbol']]]
  bnPayments['Ccy'] = [z[:3] for z in bnPayments['symbol']]
  bnPayments = bnPayments.set_index('Ccy').loc[['BTC', 'ETH']]
  bnPayments['incomeUSD'] = [float(z) for z in bnPayments['income']]
  bnPayments.loc['BTC', 'incomeUSD'] *= spotBTC
  bnPayments.loc['ETH', 'incomeUSD'] *= spotETH
  bnPayments['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in bnPayments['time']]
  bnPayments = bnPayments.set_index('date')
  bnPayments = getOneDay(bnPayments)
  bnTDiff = bnPayments.index[-1] - bnPayments.index[0]
  bnNDays = bnTDiff.days + (bnTDiff.seconds + 3600 * 8) / 86400
  #####
  bnPrevIncome = bnPayments.loc[bnPayments.index[-1]]['incomeUSD'].sum()
  bnPrevAnnRet = bnPrevIncome * 3 * 365 / bnNotional
  bnOneDayIncome = bnPayments['incomeUSD'].sum()
  bnOneDayAnnRet = (bnOneDayIncome / bnNDays * 365) / bnNotional
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
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['fundingTime']]
  df = df.set_index('date')
  df['fundingRate']=[float(fr) for fr in df['fundingRate']]
  df=getOneDay(df)
  oneDayFunding = df['fundingRate'].mean() * 3 * 365
  prevFunding = df['fundingRate'][-1] * 3 * 365
  estFunding=cl.bnGetEstFunding(bn,ccy)
  printFunding('Binance', bnPR, ccy, oneDayFunding, prevFunding, estFunding)

def bbInit(bb,spotBTC,spotETH):
  def getPayments(ccy):
    start_time = int((datetime.datetime.timestamp(datetime.datetime.now() - pd.DateOffset(days=1))) * 1000)
    return pd.DataFrame(bb.v2_private_get_execution_list({'symbol': ccy + 'USD','start_time':start_time,'limit':1000})['result']['trade_list']).set_index('symbol',drop=False)

  def getLiq(bbPL,ccy):
    liqPrice = float(bbPL.loc[ccy, 'liq_price'])
    markPrice = float(bbPL.loc[ccy, 'size']) / float(bbPL.loc[ccy, 'position_value'])
    return liqPrice/markPrice

  bbBal=bb.fetch_balance()
  bbSpotDeltaBTC=bbBal['BTC']['total']
  bbSpotDeltaETH=bbBal['ETH']['total']
  #####
  bbPL=bb.v2_private_get_position_list()['result']
  bbPL=pd.DataFrame([pos['data'] for pos in bbPL])
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
  bbPayments['fee_rate'] = [float(fr) for fr in bbPayments['fee_rate']]
  bbPayments['incomeUSD']=[-float(income) for income in bbPayments['exec_fee']]
  bbPayments.loc['BTCUSD','incomeUSD']*=spotBTC
  bbPayments.loc['ETHUSD','incomeUSD']*=spotETH
  bbPayments=bbPayments[bbPayments['exec_type']=='Funding']
  bbPayments['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in bbPayments['trade_time_ms']]
  bbPayments=bbPayments.set_index('date')
  bbPayments = getOneDay(bbPayments)
  bbTDiff=bbPayments.index[-1]-bbPayments.index[0]
  bbNDays=bbTDiff.days+(bbTDiff.seconds+3600*8)/86400
  #####
  bbPrevIncome = bbPayments.loc[bbPayments.index[-1]]['incomeUSD'].sum()
  bbPrevAnnRet = bbPrevIncome * 3 * 365 / bbNotional
  bbOneDayIncome = bbPayments['incomeUSD'].sum()
  bbOneDayAnnRet = (bbOneDayIncome / bbNDays * 365) / bbNotional
  #####
  bbNAV = bbSpotDeltaBTC * spotBTC + bbSpotDeltaETH * spotETH
  bbLiqBTC = getLiq(bbPL,'BTC')
  bbLiqETH = getLiq(bbPL,'ETH')
  #####
  return bbSpotDeltaBTC, bbSpotDeltaETH, bbPL, bbPayments, \
         bbPrevIncome, bbPrevAnnRet, bbOneDayIncome, bbOneDayAnnRet, \
         bbNAV,bbLiqBTC,bbLiqETH

def bbPrintFunding(bb,bbPL,bbPayments,ccy):
  df=bbPayments[bbPayments['symbol']==ccy + 'USD']
  oneDayFunding = -df['fee_rate'].mean() * 3 * 365
  prevFunding = -df['fee_rate'][-1] * 3 * 365
  estFunding1 = cl.bbGetEstFunding1(bb,ccy)
  estFunding2 = cl.bbGetEstFunding2(bb,ccy)
  printFunding('Bybit', bbPL, ccy, oneDayFunding, prevFunding, estFunding1,estFunding2)

def cbInit(cb,spotBTC,spotETH):
  bal=cb.fetch_balance()
  cbSpotDeltaBTC=bal['BTC']['total']
  cbSpotDeltaETH=bal['ETH']['total']
  cbNAV=cbSpotDeltaBTC*spotBTC+cbSpotDeltaETH*spotETH
  return cbSpotDeltaBTC,cbSpotDeltaETH,cbNAV

######
# Init
######
ftx=ccxt.ftx({'apiKey': cl.API_KEY_FTX, 'secret': cl.API_SECRET_FTX, 'enableRateLimit': True})
bn = ccxt.binance({'apiKey': cl.API_KEY_BINANCE, 'secret': cl.API_SECRET_BINANCE, 'enableRateLimit': True})
bb = ccxt.bybit({'apiKey': cl.API_KEY_BYBIT, 'secret': cl.API_SECRET_BYBIT, 'enableRateLimit': True})
cb=ccxt.coinbase({'apiKey': cl.API_KEY_CB, 'secret': cl.API_SECRET_CB, 'enableRateLimit': True})

ftxWallet,ftxPositions,ftxPayments,ftxBorrows, \
  ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet, \
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
oneDayIncome=ftxOneDayIncome+bnOneDayIncome+bbOneDayIncome

spotDeltaBTC=0
spotDeltaBTC+=ftxWallet.loc['BTC','SpotDelta']
spotDeltaBTC+=bnBal.loc['BTC','SpotDelta']
spotDeltaBTC+=bbSpotDeltaBTC
spotDeltaBTC+=cbSpotDeltaBTC

futDeltaBTC=0
futDeltaBTC+=ftxPositions.loc['BTC','FutDelta']
futDeltaBTC+=bnPR.loc['BTC','FutDelta']
futDeltaBTC+=bbPL.loc['BTC','FutDelta']

spotDeltaETH=0
spotDeltaETH+=ftxWallet.loc['ETH','SpotDelta']
spotDeltaETH+=bnBal.loc['ETH','SpotDelta']
spotDeltaETH+=bbSpotDeltaETH
spotDeltaETH+=cbSpotDeltaETH

futDeltaETH=0
futDeltaETH+=ftxPositions.loc['ETH','FutDelta']
futDeltaETH+=bnPR.loc['ETH','FutDelta']
futDeltaETH+=bbPL.loc['ETH','FutDelta']

spotDeltaFTT=0
spotDeltaFTT+=ftxWallet.loc['FTT','SpotDelta']

futDeltaFTT=0
futDeltaFTT+=ftxPositions.loc['FTT','FutDelta']

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
printIncomes('FTX',ftxPrevIncome,ftxPrevAnnRet,ftxOneDayIncome,ftxOneDayAnnRet)
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'BTC')
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'ETH')
ftxPrintFunding(ftx,ftxPositions,ftxPayments,'FTT')
ftxPrintBorrow(ftx,ftxWallet,ftxBorrows)
print(termcolor.colored('FTX margin: '.rjust(41)+str(round(ftxMF*100,1))+'% (vs. '+str(round(ftxMMReq*100,1))+'% limit)','red'))
print()
printIncomes('Binance',bnPrevIncome,bnPrevAnnRet,bnOneDayIncome,bnOneDayAnnRet)
bnPrintFunding(bn,bnPR,'BTC')
bnPrintFunding(bn,bnPR,'ETH')
print(termcolor.colored('Binance liquidation (BTC/ETH): '.rjust(41)+str(round(bnLiqBTC*100,1))+'%/'+str(round(bnLiqETH*100,1))+'% (of spot)','red'))
print()
printIncomes('Bybit',bbPrevIncome,bbPrevAnnRet,bbOneDayIncome,bbOneDayAnnRet)
bbPrintFunding(bb,bbPL,bbPayments,'BTC')
bbPrintFunding(bb,bbPL,bbPayments,'ETH')
print(termcolor.colored('Bybit liquidation (BTC/ETH): '.rjust(41)+str(round(bbLiqBTC*100,1))+'%/'+str(round(bbLiqETH*100,1))+'% (of spot)','red'))
print()
printDeltas('BTC',spotBTC,spotDeltaBTC,futDeltaBTC)
printDeltas('ETH',spotETH,spotDeltaETH,futDeltaETH)
printDeltas('FTT',spotFTT,spotDeltaFTT,futDeltaFTT)
