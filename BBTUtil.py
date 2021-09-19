#########
# BBTUtil
#########
import CryptoLib as cl
from CryptoParams import *
import pandas as pd

########
# Params
########
isAutoRiskLimit=True

###########
# Functions
###########
def fmtPct(n):
  return str(round(n * 100, 1))+'%'

def autoRiskLimit(api, sym_list):
  fut_sym_list = [sym + 'USDT' for sym in sym_list]
  risk_dict = dict()
  for sym in fut_sym_list:
    risk_limit = api.public_linear_get_risk_limit({'symbol': sym})['result']
    risk_dict[sym] = risk_limit
  for sym in fut_sym_list:
    df = pd.DataFrame(api.private_linear_get_position_list({'symbol': sym})['result']).set_index('side')
    if len(df) > 0:
      lev = dict()
      for side in ['Buy', 'Sell']:
        lev[side] = float(df.loc[side, 'leverage'])
      for side in ['Buy', 'Sell']:
        opp_side = 'Buy' if side == 'Sell' else 'Sell'
        size = abs(float(df.loc[side, 'size']))
        if size != 0:
          position_value = float(df.loc[side, 'position_value'])
          risk_limit = risk_dict[sym]
          for risk in risk_limit:
            max_size = float(risk['limit'])
            if max_size > position_value:
              select_id = int(risk['id'])
              select_lev = float(risk['max_leverage'])
              isMod=False
              if int(df.loc[side, 'risk_id']) != select_id:
                api.private_linear_post_position_set_risk({'symbol': sym, 'side': side, 'risk_id': select_id})
                isMod=True
              if lev[side] < select_lev:
                api.private_linear_post_position_set_leverage({'symbol': sym, side.lower() + '_leverage': select_lev, opp_side.lower() + '_leverage': lev[opp_side]})
                isMod=True
              if isMod: print(f'{sym} {position_value:,.0f} -> Risk limit ({max_size:,.0f})  Leverage ({select_lev})')
              break

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
  df.drop(['position_value','im_value','mm_value'],axis=1,inplace=True)
  cols = ['delta_value','unrealised_pnl']
  cols2 = ['spot_price','liq_price']
  df[cols]=df[cols].astype(int)
  df[cols2]=df[cols2].round(2)
  df=df.sort_values('unrealised_pnl',ascending=False)
  df['liq'] = df['liq'].apply(fmtPct)
  df['ratio'] = df['unrealised_pnl']/df['delta_value']
  df['ratio'] = df['ratio'].apply(fmtPct)
  pd.set_option('display.max_columns',len(df.columns))
  df=df[df['delta_value']!=0]
  print(df)
  print()
  if isAutoRiskLimit: autoRiskLimit(bbForBBT, df.index)

