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
CT_CONFIGS_DICT['SPOT_'+ccy]=[0,0]
CT_CONFIGS_DICT['FTX_'+ccy]=[0,0]
CT_CONFIGS_DICT['BBT_'+ccy]=[0,0]
CT_CONFIGS_DICT['BB_'+ccy]=[0,0]
CT_CONFIGS_DICT['DB_'+ccy]=[0,0]
CT_CONFIGS_DICT['KF_'+ccy]=[0,0]
CT_CONFIGS_DICT['KUT_'+ccy]=[0,0]

# BN/BNT to be deprecated soon....
CT_CONFIGS_DICT['BNT_'+ccy]=[0,0]
CT_CONFIGS_DICT['BN_'+ccy]=[0,0]

# Misc settings
CT_CONFIGS_DICT['NPROGRAMS'] = 10
CT_CONFIGS_DICT['CURRENT_BBT']=1
CT_CONFIGS_DICT['CURRENT_KUT']=1

######
# Main
######
cl.ctRun(ccy,tgtBps,color,notional)
