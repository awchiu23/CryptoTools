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
  print ('Average FTX '+ccy+' funding rate since '+str(df.index[0])[:10]+':     '+str(round(df['rate'].mean()*24*365*100))+'%')

def bnPrintFundingRate(bn,ccy,cutoff):
  df = pd.DataFrame(bn.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP'}))
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['fundingTime']]
  df = df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  df['fundingRate']=[float(fr) for fr in df['fundingRate']]
  print('Average Binance ' + ccy + ' funding rate since ' + df.index[0].strftime('%Y-%m-%d') + ': ' + str(round(df['fundingRate'].mean() * 3 * 365 * 100)) + '%')

def bbPrintFundingRate(bb,ccy,cutoff):
  df=pd.DataFrame(bb.v2_private_get_execution_list({'symbol': ccy + 'USD', 'limit': 1000})['result']['trade_list'])
  df['fee_rate'] = [float(fr) for fr in df['fee_rate']]
  df=df[df['exec_type']=='Funding']
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['trade_time_ms']]
  df=df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  print('Average Bybit ' + ccy + ' funding rate since ' + df.index[0].strftime('%Y-%m-%d') + ':   ' + str(round(-df['fee_rate'].mean() * 3 * 365 * 100)) + '%')

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
print ('Average FTX USD borrow rate since '+str(df.index[0])[:10]+':      '+str(round(df['rate'].mean()*24*365*100))+'%  (Only averaged over periods during which you borrowed)')

df=pd.DataFrame(ftx.private_get_spot_margin_lending_history({'limit':1000})['result'])
df.index=[datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df['time']]
df=df[df.index>=cutoff].sort_index()
print ('Average FTX USD lending rate since '+str(df.index[0])[:10]+':     '+str(round(df['rate'].mean()*24*365*100))+'%  (Only averaged over periods during which you lent)')
print()

ftxPrintFundingRate(ftx,'BTC',cutoff)
ftxPrintFundingRate(ftx,'ETH',cutoff)
ftxPrintFundingRate(ftx,'FTT',cutoff)
print()

bnPrintFundingRate(bn,'BTC',cutoff)
bnPrintFundingRate(bn,'ETH',cutoff)
print()

bbPrintFundingRate(bb,'BTC',cutoff)
bbPrintFundingRate(bb,'ETH',cutoff)
print()

