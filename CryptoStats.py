import CryptoLib as cl
import pandas as pd
import datetime
import termcolor
import ccxt

########
# Params
########
isShowAltFundings=False

###########
# Functions
###########
def getSuffix(df):
  return '(since ' + df.index[0].strftime('%Y-%m-%d') + ')'

def ftxPrintFundingRate(ftx,ccy,cutoff):
  df=pd.DataFrame(ftx.private_get_funding_payments({'limit':1000,'future':ccy+'-PERP'})['result'])
  cl.dfSetFloat(df, 'rate')
  df.index = [datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df['time']]
  df = df[df.index >= cutoff].sort_index()
  rate=df['rate'].mean()*24*365

  print (('Avg FTX '+ccy+' funding rate: ').rjust(40)+str(round(rate*100))+'% '+ getSuffix(df))
  return rate, df['time']

def ftxPrintBorrowLendingRate(ftx,ftxTimeS,ccy):
  def cleanBorrows(df, ccy, cutoff):
    df2 = df[df['coin'] == ccy].set_index('time',drop=False).reindex(ftxTimeS).fillna(0).copy()
    ts=df2['rate']
    ts[:] = [float(n) for n in ts]
    ts.index = [datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in ts.index]
    ts = ts[ts.index >= cutoff].sort_index()
    return ts
  ts=  cleanBorrows(pd.DataFrame(ftx.private_get_spot_margin_borrow_history({'limit': 1000})['result']),ccy,cutoff)
  ts2 = cleanBorrows(pd.DataFrame(ftx.private_get_spot_margin_lending_history({'limit': 1000})['result']),ccy,cutoff)
  df = pd.merge(ts / 1.1, ts2 * 1.1, how='outer', left_index=True, right_index=True).mean(axis=1)
  df *= (24 * 365)
  if ccy=='USD':
    z='borrow/lending'
  else:
    z='lending'
  print(('Avg FTX '+ccy+' '+z+' rate: ').rjust(40) + termcolor.colored(str(round(df.mean() * 100)) + '% ' + getSuffix(df), 'red'))

def bnPrintFundingRate(bn,ccy,cutoff):
  df = pd.DataFrame(bn.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP'}))
  cl.dfSetFloat(df, 'fundingRate')
  df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['fundingTime']]
  df = df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  rate=df['fundingRate'].mean() * 3 * 365
  print(('Avg BN ' + ccy + ' funding rate: ').rjust(40) + str(round(rate * 100)) + '% '+ getSuffix(df))
  return rate

def bbPrintFundingRate(bb,ccy,cutoff):
  start_time = int((datetime.datetime.timestamp(cutoff)) * 1000)
  df=pd.DataFrame(bb.v2_private_get_execution_list({'symbol': ccy + 'USD','start_time':start_time, 'limit': 1000})['result']['trade_list'])
  cl.dfSetFloat(df,'fee_rate')
  df=df[df['exec_type']=='Funding']
  df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['trade_time_ms']]
  df=df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  rate=-df['fee_rate'].mean() * 3 * 365
  print(('Avg BB ' + ccy + ' funding rate: ').rjust(40)+ str(round(rate * 100)) + '% '+ getSuffix(df))
  return rate

def dbPrintFundingRate(db,ccy,cutoff):
  start_timestamp = int(datetime.datetime.timestamp(cutoff)*1000)
  end_timestamp = int((datetime.datetime.timestamp(datetime.datetime.now())) * 1000)
  df = pd.DataFrame(db.public_get_get_funding_rate_history({'instrument_name': ccy+'-PERPETUAL', 'start_timestamp': start_timestamp, 'end_timestamp': end_timestamp})['result'])
  cl.dfSetFloat(df,'interest_1h')
  df['date'] = [datetime.datetime.fromtimestamp(int(ts) / 1000) for ts in df['timestamp']]
  df = df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  rate=df['interest_1h'].mean() * 24 * 365
  print(('Avg Deribit ' + ccy + ' funding rate: ').rjust(40) + str(round(rate * 100)) + '% '+ getSuffix(df))
  return rate

######
# Init
######
cl.printHeader('CryptoStats')
ftx=cl.ftxCCXTInit()
bn = cl.bnCCXTInit()
bb = cl.bbCCXTInit()
if isShowAltFundings:
  db = ccxt.deribit({'apiKey': 's545TabG', 'secret': 'Ii7kYRE1N9Klu-0fer8-IMJocaz3BNqVsobqGfKSo-M', 'enableRateLimit': True})

cutoff=datetime.datetime.now() - pd.DateOffset(days=7)
ftxBTCFundingRate,ftxTimeS=ftxPrintFundingRate(ftx,'BTC',cutoff)
ftxETHFundingRate,_=ftxPrintFundingRate(ftx,'ETH',cutoff)
ftxFTTFundingRate,_=ftxPrintFundingRate(ftx,'FTT',cutoff)
bnBTCFundingRate=bnPrintFundingRate(bn,'BTC',cutoff)
bnETHFundingRate=bnPrintFundingRate(bn,'ETH',cutoff)
bbBTCFundingRate=bbPrintFundingRate(bb,'BTC',cutoff)
bbETHFundingRate=bbPrintFundingRate(bb,'ETH',cutoff)
if isShowAltFundings:
  dbPrintFundingRate(db,'BTC',cutoff)
  dbPrintFundingRate(db,'ETH',cutoff)
print()

ftxMixedFundingRate=(ftxBTCFundingRate+ftxETHFundingRate)/2
bnMixedFundingRate=(bnBTCFundingRate+bnETHFundingRate)/2
bbMixedFundingRate=(bbBTCFundingRate+bbETHFundingRate)/2

print('-' * 100)
print()

ftxPrintBorrowLendingRate(ftx,ftxTimeS,'USD')
ftxPrintBorrowLendingRate(ftx,ftxTimeS,'BTC')
ftxPrintBorrowLendingRate(ftx,ftxTimeS,'ETH')
print()
print('Avg FTX funding rate (BTC&ETH): '.rjust(40)+termcolor.colored(str(round(ftxMixedFundingRate*100))+'%','red'))
print('Avg BN funding rate (BTC&ETH): '.rjust(40)+termcolor.colored(str(round(bnMixedFundingRate*100))+'%','red'))
print('Avg BB funding rate (BTC&ETH): '.rjust(40)+termcolor.colored(str(round(bbMixedFundingRate*100))+'%','red'))
