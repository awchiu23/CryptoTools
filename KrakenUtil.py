############
# KrakenUtil
############
from CryptoParams import *
import CryptoLib as cl
import pandas as pd
import datetime
import time
import sys

###########
# Functions
###########
def getLedgersRaw(kr,start,ofs):
  while True:
    try:
      return pd.DataFrame(kr.private_post_ledgers({'type': 'rollover', 'start': start, 'ofs': ofs})['result']['ledger'])
    except:
      time.sleep(10)

def getLedgers(kr, spotBTC, spotEUR):
  yest = datetime.datetime.now() - pd.DateOffset(days=1)
  yest2 = int((datetime.datetime.timestamp(yest)))
  n = 0
  ledgers = pd.DataFrame()
  while True:
    df = getLedgersRaw(kr,yest2,n).transpose()
    if len(df)==0:
      break
    cl.dfSetFloat(df, ['time', 'fee'])
    df['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in df['time']]
    ledgers=ledgers.append(df)
    if ledgers.iloc[-1]['date']<yest:
      ledgers=ledgers[ledgers['date']>=yest]
      break
    n+=50
  ledgers['feeUSD'] = ledgers['fee']
  ledgers.loc[ledgers['asset']=='XXBT','feeUSD']*=spotBTC
  ledgers.loc[ledgers['asset'] == 'ZEUR', 'feeUSD'] *= spotEUR
  return ledgers.set_index('date').sort_index()

def getPositions(kr):
  positions = pd.DataFrame(kr.private_post_openpositions()['result']).transpose().set_index('pair')
  if not all([z in ['XXBTZUSD', 'XXBTZEUR'] for z in positions.index]):
    print('Invalid Kraken pair detected!')
    sys.exit(1)
  cl.dfSetFloat(positions, ['time'])
  positions['date'] = [datetime.datetime.fromtimestamp(int(ts)) for ts in positions['time']]
  return positions

def getAutoLiqDate(positions,pair):
  return positions.loc[pair]['date'].sort_values()[0] + pd.DateOffset(days=365)

######
# Init
######
cl.printHeader('KrakenUtil')
ftx = cl.ftxCCXTInit()
ftxWallet = cl.ftxGetWallet(ftx)
spotBTC = ftxWallet.loc['BTC', 'spot']

krs=[]
for i in range(CR_N_KR_ACCOUNTS):
  krs.append(cl.krCCXTInit(i+1))
spot_xxbtzeur = float(krs[0].public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
spot_xxbtzusd = float(krs[0].public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
spotEUR = spot_xxbtzusd / spot_xxbtzeur

print('Please wait ....')
n=0
for krChosen in krs:
  n+=1
  ledgers=getLedgers(krChosen,spotBTC,spotEUR)
  print('KR'+str(n)+' 24h borrow: $'+str(round(ledgers['feeUSD'].sum())))
print()

n=0
for krChosen in krs:
  n+=1
  positions=getPositions(krChosen)
  dtAutoCloseUSD=(positions.loc['XXBTZUSD']['date'].sort_values()[0]+ pd.DateOffset(days=365)).strftime('%Y-%m-%d')
  dtAutoCloseEUR=(positions.loc['XXBTZEUR']['date'].sort_values()[0]+ pd.DateOffset(days=365)).strftime('%Y-%m-%d')
  dtFormat='%Y-%m-%d'
  print('KR'+str(n)+' auto liquidation dates XXBTZUSD/XXBTZEUR: '+getAutoLiqDate(positions,'XXBTZUSD').strftime(dtFormat)+' / '+getAutoLiqDate(positions,'XXBTZEUR').strftime(dtFormat))
