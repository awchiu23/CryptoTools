import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='SOL'
notional=2000 # USD
tgtBps=30
color='cyan'

CT_CONFIGS_DICT['SPOT_'+ccy+'_OK']=1
CT_CONFIGS_DICT['FTX_'+ccy+'_OK']=1
CT_CONFIGS_DICT['SPOT_'+ccy+'_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_'+ccy+'_ADJ_BPS']=30   # Positive = eager to buy; Negative = eager to sell

CT_CONFIGS_DICT['FTX_DISTANCE_TO_BEST_BPS']=-2
#SHARED_CCY_DICT[ccy] = {'futExch': ['ftx']}


######
# Main
######
cl.ctRun(ccy, tgtBps, color, notional)
