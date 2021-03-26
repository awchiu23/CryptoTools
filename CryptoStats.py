import CryptoLib as cl
import pandas as pd
import datetime
import termcolor

###########
# Functions
###########
def ftxPrintFundingRate(ftx,ccy,cutoff):
  df=pd.DataFrame(ftx.private_get_funding_payments({'limit':1000,'future':ccy+'-PERP'})['result'])
  df.index = [datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df['time']]
  df = df[df.index >= cutoff].sort_index()
  rate=df['rate'].mean()*24*365
  print (('Avg FTX '+ccy+' funding rate: ').rjust(40)+str(round(rate*100))+'%')
  return rate

def bnPrintFundingRate(bn,ccy,cutoff):
  df = pd.DataFrame(bn.dapiPublic_get_fundingrate({'symbol': ccy + 'USD_PERP'}))
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['fundingTime']]
  df = df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  cl.dfSetFloat(df,'fundingRate')
  rate=df['fundingRate'].mean() * 3 * 365
  print(('Avg Binance ' + ccy + ' funding rate: ').rjust(40) + str(round(rate * 100)) + '%')
  return rate

def bbPrintFundingRate(bb,ccy,cutoff):
  df=pd.DataFrame(bb.v2_private_get_execution_list({'symbol': ccy + 'USD', 'limit': 1000})['result']['trade_list'])
  df['fee_rate'] = [float(fr) for fr in df['fee_rate']]
  df=df[df['exec_type']=='Funding']
  df['date'] = [datetime.datetime.fromtimestamp(int(ts / 1000)) for ts in df['trade_time_ms']]
  df=df.set_index('date')
  df = df[df.index >= cutoff].sort_index()
  rate=-df['fee_rate'].mean() * 3 * 365
  print(('Avg Bybit ' + ccy + ' funding rate: ').rjust(40)+ str(round(rate * 100)) + '%')
  return rate

######
# Init
######
cl.printHeader('CryptoStats')
ftx=cl.ftxCCXTInit()
bn = cl.bnCCXTInit()
bb = cl.bbCCXTInit()

cutoff=datetime.datetime.now() - pd.DateOffset(days=7)
print('Cut-off date: '.rjust(40)+cutoff.strftime('%Y-%m-%d'))
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

print('-' * 100)
print()

ts=pd.DataFrame(ftx.private_get_spot_margin_borrow_history({'limit':1000})['result']).set_index('time')['rate']
ts2=pd.DataFrame(ftx.private_get_spot_margin_lending_history({'limit':1000})['result']).set_index('time')['rate']
df=pd.merge(ts/1.1,ts2*1.1,how='outer',left_index=True,right_index=True).mean(axis=1)*24*365
df.index=[datetime.datetime.strptime(z[:10], '%Y-%m-%d') for z in df.index]
df=df[df.index>=cutoff].sort_index()
print (('Avg FTX USD rate: ').rjust(40)+termcolor.colored(str(round(df.mean()*100))+'%','red'))

print('Avg FTX funding rate (BTC&ETH): '.rjust(40)+termcolor.colored(str(round(ftxMixedFundingRate*100))+'%','red'))
print('Avg Binance funding rate (BTC&ETH): '.rjust(40)+termcolor.colored(str(round(bnMixedFundingRate*100))+'%','red'))
print('Avg Bybit funding rate (BTC&ETH): '.rjust(40)+termcolor.colored(str(round(bbMixedFundingRate*100))+'%','red'))

