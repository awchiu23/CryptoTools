#########
# BBTUtil
#########
import CryptoLib as cl

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

cols = ['position_value','unrealised_pnl','mm_value']
df[cols]=df[cols].round()
df=df.sort_values('liq')
print(df)