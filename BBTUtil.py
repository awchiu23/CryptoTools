#########
# BBTUtil
#########
import CryptoLib as cl
import pandas as pd

############
# Parameters
############
isCalcMyLiq = True   # Calculate own liq numbers

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

if isCalcMyLiq:
  wallet = bb.v2_private_get_wallet_balance({'coin': 'USDT'})['result']['USDT']
  wallet_balance = float(wallet['wallet_balance'])
  ab = wallet_balance - df['im_value'].sum() + df['unrealised_pnl'].clip(None,0).sum()
  cushion=(ab + df['im_value']-df['mm_value'] +df['unrealised_pnl'].clip(0,None))
  df['my_liq']=1-cushion/df['delta_value']

cols = ['position_value','delta_value','unrealised_pnl','im_value','mm_value']
cols2 = ['spot_price','liq_price']
df[cols]=df[cols].round()
df[cols2]=df[cols2].round(2)
df=df.sort_values('liq')
pd.set_option('display.max_columns',len(df.columns))
print(df)

