import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='BTC'
notional=10000
tgtBps=15
color='blue'

# [Enabled? (0 = disabled; 1 = enabled),
#  Axe (+ve = eager to buy; -ve = eager to sell),
#  Optional 1: Max abs position USD,
#  Optional 2: Allowed sign (+ve = long only; -ve = short only)]
CT_CONFIGS_DICT['SPOT_BTC']=[0,0]
CT_CONFIGS_DICT['FTX_BTC']=[0,0]
CT_CONFIGS_DICT['BBT_BTC']=[0,0]
CT_CONFIGS_DICT['BNT_BTC']=[0,0]
CT_CONFIGS_DICT['KF_BTC']=[0,0]
CT_CONFIGS_DICT['BB_BTC']=[0,0]
CT_CONFIGS_DICT['BN_BTC']=[0,0]

######
# Main
######
cl.ctRun(ccy,tgtBps,color,notional)
