import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='ETH'
notional=10000
tgtBps=15
color='magenta'

# [Enabled? (0 = disabled; 1 = enabled),
#  Axe (+ve = eager to buy; -ve = eager to sell),
#  Optional: Max abs position USD]
CT_CONFIGS_DICT['SPOT_ETH']=[0,0]
CT_CONFIGS_DICT['FTX_ETH']=[0,0]
CT_CONFIGS_DICT['BBT_ETH']=[0,0]
CT_CONFIGS_DICT['BNT_ETH']=[0,0]
CT_CONFIGS_DICT['KF_ETH']=[0,0]
CT_CONFIGS_DICT['BB_ETH']=[0,0]
CT_CONFIGS_DICT['BN_ETH']=[0,0]

######
# Main
######
cl.ctRun(ccy,tgtBps,color,notional)
