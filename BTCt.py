import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='BTC'
notional=10000
tgtBps=20
color='blue'

# [Enabled? (0 = disabled; 1 = enabled),
#  Axe (+ve = eager to buy; -ve = eager to sell),
#  Optional: Max abs position USD]
CT_CONFIGS_DICT['SPOT_'+ccy]=[0,0]
CT_CONFIGS_DICT['FTX_'+ccy]=[0,0]
CT_CONFIGS_DICT['BBT_'+ccy]=[0,0]
CT_CONFIGS_DICT['BB_'+ccy]=[0,0]
CT_CONFIGS_DICT['DB_'+ccy]=[0,0]
CT_CONFIGS_DICT['KF_'+ccy]=[0,0]
CT_CONFIGS_DICT['KUT_'+ccy]=[0,0]

######
# Main
######
cl.ctRun(ccy,tgtBps,color,notional)
