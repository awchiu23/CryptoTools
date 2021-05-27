#########
# BNTUtil
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
bn=cl.bnCCXTInit()
cl.printHeader('BNTUtil')
ccys=cl.getValidCcys('bnt')
df=cl.bntGetRiskDf(bn,ccys)
df=df[['notional','markPrice','liquidationPrice','liq','unRealizedProfit']]
cols = ['notional','unRealizedProfit']
cols2 = ['markPrice','liquidationPrice']
df[cols]=df[cols].astype(int)
df[cols2]=df[cols2].round(2)
df=df.sort_values('liq')
df['liq'] = df['liq'].apply(fmtPct)
pd.set_option('display.max_columns',len(df.columns))
print(df)
