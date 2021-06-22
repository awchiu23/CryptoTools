#########
# BBTUtil
#########
import CryptoLib as cl
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
cl.printHeader('BBTUtil')
spotDict=dict()
ccys=cl.getValidCcys('bbt')
for ccy in ccys:
  spotDict[ccy]=cl.ftxGetMid(ftx,ccy+'/USD')
spotDict['USDT']=cl.ftxGetMid(ftx,'USDT/USD')
df=cl.bbtGetRiskDf(bb,ccys,spotDict)
df.drop(['position_value','im','mm','im_value','mm_value'],axis=1,inplace=True)
cols = ['delta_value','unrealised_pnl']
cols2 = ['spot_price','liq_price']
df[cols]=df[cols].astype(int)
df[cols2]=df[cols2].round(2)
df=df.sort_values('liq')
df['liq'] = df['liq'].apply(fmtPct)
pd.set_option('display.max_columns',len(df.columns))
print(df)
