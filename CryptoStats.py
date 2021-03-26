import CryptoLib as cl
import pandas as pd
import datetime

###########
# Functions
###########
def ftxPrintFundingRate(ftx,ccy,cutoff):
  df=pd.DataFrame(ftx.private_get_funding_payments({'limit':1000,'future':ccy+'-PERP'})['result'])
  df.index = [datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df['time']]
  df = df[df.index >= cutoff].sort_index()
  rate=df['rate'].mean()*24*365
  print (('Average FTX '+ccy+' funding rate since '+str(df.index[0])[:10]+': ').rjust(60)+str(round(rate*100))+'%')
  return rate

def bnPrintFundingRate(bn,ccy,cutoff):
  df = pd.DataFrame(bn.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP'}))
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['fundingTime']]
  df = df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  cl.dfSetFloat(df,'fundingRate')
  rate=df['fundingRate'].mean() * 3 * 365
  print(('Average Binance ' + ccy + ' funding rate since ' + df.index[0].strftime('%Y-%m-%d') + ': ').rjust(60) + str(round(rate * 100)) + '%')
  return rate

def bbPrintFundingRate(bb,ccy,cutoff):
  df=pd.DataFrame(bb.v2_private_get_execution_list({'symbol': ccy + 'USD', 'limit': 1000})['result']['trade_list'])
  df['fee_rate'] = [float(fr) for fr in df['fee_rate']]
  df=df[df['exec_type']=='Funding']
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['trade_time_ms']]
  df=df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  rate=-df['fee_rate'].mean() * 3 * 365
  print(('Average Bybit ' + ccy + ' funding rate since ' + df.index[0].strftime('%Y-%m-%d') + ': ').rjust(60)+ str(round(rate * 100)) + '%')
  return rate

######
# Init
######
cl.printHeader('CryptoStats')
ftx=cl.ftxCCXTInit()
bn = cl.bnCCXTInit()
bb = cl.bbCCXTInit()
cutoff=datetime.datetime.now() - pd.DateOffset(days=7)

df=pd.DataFrame(ftx.private_get_spot_margin_borrow_history({'limit':1000})['result'])
df.index=[datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df['time']]
df=df[df.index>=cutoff].sort_index()
print (('Average FTX USD borrow rate since '+str(df.index[0])[:10]+': ').rjust(60)+str(round(df['rate'].mean()*24*365*100))+'%  (Only averaged over periods during which you borrowed)')

df=pd.DataFrame(ftx.private_get_spot_margin_lending_history({'limit':1000})['result'])
df.index=[datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df['time']]
df=df[df.index>=cutoff].sort_index()
print (('Average FTX USD lending rate since '+str(df.index[0])[:10]+': ').rjust(60)+str(round(df['rate'].mean()*24*365*100))+'%  (Only averaged over periods during which you lent)')
print()

ftxBTCFundingRate=ftxPrintFundingRate(ftx,'BTC',cutoff)
ftxETHFundingRate=ftxPrintFundingRate(ftx,'ETH',cutoff)
ftxPrintFundingRate(ftx,'FTT',cutoff)
print()

bnBTCFundingRate=bnPrintFundingRate(bn,'BTC',cutoff)
bnETHFundingRate=bnPrintFundingRate(bn,'ETH',cutoff)
print()

bbBTCFundingRate=bbPrintFundingRate(bb,'BTC',cutoff)
bbETHFundingRate=bbPrintFundingRate(bb,'ETH',cutoff)
print()

ftxMixedFundingRate=(ftxBTCFundingRate+ftxETHFundingRate)/2
bnMixedFundingRate=(bnBTCFundingRate+bnETHFundingRate)/2
bbMixedFundingRate=(bbBTCFundingRate+bbETHFundingRate)/2

print('FTX mixed funding rate (BTC+ETH): '.rjust(60)+str(round(ftxMixedFundingRate*100))+'%')
print('Binance mixed funding rate (BTC+ETH): '.rjust(60)+str(round(bnMixedFundingRate*100))+'%')
print('Bybit mixed funding rate (BTC+ETH): '.rjust(60)+str(round(bbMixedFundingRate*100))+'%')

