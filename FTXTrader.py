import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='MATIC'
notional=1000 # USD
tgtBps=30
color='cyan'
CT_CONFIGS_DICT['SPOT_'+ccy+'_OK']=1
CT_CONFIGS_DICT['FTX_'+ccy+'_OK']=1
CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_'+ccy+'_ADJ_BPS']=15   # Positive = eager to buy; Negative = eager to sell

######
# Main
######
cl.ctRun(ccy, tgtBps, color, notional)
