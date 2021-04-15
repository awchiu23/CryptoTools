#################
# KR24HBorrowCalc
#################
from CryptoParams import *
import CryptoLib as cl
import pandas as pd
import datetime
import time

###########
# Functions
###########
def getLedgersRaw(kr,start,ofs):
  while True:
    try:
      return pd.DataFrame(kr.private_post_ledgers({'type': 'rollover', 'start': start, 'ofs': ofs})['result']['ledger'])
    except:
      print('.',end='')
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

######
# Init
######
cl.printHeader('Kraken24HBorrowCalc')
ftx = cl.ftxCCXTInit()
ftxWallet = cl.ftxGetWallet(ftx)
spotBTC = ftxWallet.loc['BTC', 'spot']

krs=[]
for i in range(CR_N_KR_ACCOUNTS):
  krs.append(cl.krCCXTInit(i+1))
spot_xxbtzeur = float(krs[0].public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
spot_xxbtzusd = float(krs[0].public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
spotEUR = spot_xxbtzusd / spot_xxbtzeur

n=0
for krChosen in krs:
  n+=1
  ledgers=getLedgers(krChosen,spotBTC,spotEUR)
  print()
  print('KR'+str(n)+' 24h borrow: $'+str(round(ledgers['feeUSD'].sum())))
