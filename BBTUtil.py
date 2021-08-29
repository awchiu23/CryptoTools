#########
# BBTUtil
#########
import CryptoLib as cl
from CryptoParams import *
import pandas as pd

###########
# Functions
###########
def fmtPct(n):
  return str(round(n * 100, 1))+'%'

######
# Main
######
ftx=cl.ftxCCXTInit()
bb=cl.bbCCXTInit()
spotDict=dict()
ccys=cl.getValidCcys('bbt')
for ccy in ccys:
  spotDict[ccy]=cl.ftxGetMid(ftx,ccy+'/USD')
spotDict['USDT']=cl.ftxGetMid(ftx,'USDT/USD')

for n in range(SHARED_EXCH_DICT['bbt']):
  z='BBT'
  if n>0: z+=str(n+1)
  cl.printHeader(z)
  bbForBBT = cl.bbCCXTInit(n+1)
  df=cl.bbtGetRiskDf(bbForBBT,ccys,spotDict)
  df.drop(['position_value','im','mm','im_value','mm_value'],axis=1,inplace=True)
  cols = ['delta_value','unrealised_pnl']
  cols2 = ['spot_price','liq_price']
  df[cols]=df[cols].astype(int)
  df[cols2]=df[cols2].round(2)
  df=df.sort_values('liq')
  df['liq'] = df['liq'].apply(fmtPct)
  pd.set_option('display.max_columns',len(df.columns))
  df=df[df['delta_value']!=0]
  print(df)
  print()
