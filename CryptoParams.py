###############
# Crypto Params
###############

############################
# APIs and External Balances
############################
API_KEY_FTX = ''
API_SECRET_FTX = ''
API_KEY_BB = ''
API_SECRET_BB = ''
API_KEY_BN = ''
API_SECRET_BN = ''
API_KEY_KF = ''
API_SECRET_KF = ''
API_KEY_KR1 = ''
API_SECRET_KR1 = ''
API_KEY_KR2 = ''
API_SECRET_KR2 = ''
API_KEY_KR3 = ''
API_SECRET_KR3 = ''
API_KEY_KR4 = ''
API_SECRET_KR4 = ''
API_KEY_CB = ''
API_SECRET_CB = ''
EXTERNAL_EUR_DELTA = 0
EXTERNAL_EUR_REF = 0

#############################################################################################

##############
# CryptoTrader
##############
CT_CONFIGS_DICT=dict()
CT_DEFAULT_TGT_BPS=15
CT_CONFIGS_DICT['BTC_TGT_BPS']=CT_DEFAULT_TGT_BPS
CT_CONFIGS_DICT['ETH_TGT_BPS']=CT_DEFAULT_TGT_BPS

# BTC --- 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_BTC_OK']=1
CT_CONFIGS_DICT['FTX_BTC_OK']=1
CT_CONFIGS_DICT['BB_BTC_OK']=1
CT_CONFIGS_DICT['BN_BTC_OK']=1
CT_CONFIGS_DICT['KF_BTC_OK']=1

# BTC --- Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_BTC_ADJ_BPS']=10
CT_CONFIGS_DICT['BN_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['KF_BTC_ADJ_BPS']=0

# ETH --- 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_ETH_OK']=1
CT_CONFIGS_DICT['FTX_ETH_OK']=1
CT_CONFIGS_DICT['BB_ETH_OK']=1
CT_CONFIGS_DICT['BN_ETH_OK']=1
CT_CONFIGS_DICT['KF_ETH_OK']=1

# ETH --- Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_ETH_ADJ_BPS']=5
CT_CONFIGS_DICT['BN_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['KF_ETH_ADJ_BPS']=0

CT_IS_HIGH_SPOT_RATE_PAUSE = True    # Trading of spot paused when spot rates >= 100%?
CT_IS_NO_FUT_BUYS_WHEN_LONG = True   # Stop buying futures when position is long?
CT_STREAK = 5                        # Number of observations through target before triggering
CT_STREAK_BPS_RANGE = 10             # Max number of allowed bps for range of observations
CT_SLEEP = 3                         # Delay in seconds between observations
CT_NPROGRAMS = 100                   # Number of programs (each program being a pair of trades)
CT_BB_DISTANCE_TO_BEST_BPS=5         # Bybit execution parameter

CT_TRADE_BTC_NOTIONAL = 3000         # Per trade notional
CT_TRADE_ETH_NOTIONAL = 3000         # Per trade notional

CT_MAX_NOTIONAL = 50000              # Hard limit
CT_MAX_BTC = 0.5                     # Hard limit
CT_MAX_ETH = 10                      # Hard limit

#############################################################################################

####################
# Smart Basis Models
####################
HALF_LIFE_HOURS_SPOT = 8
HALF_LIFE_HOURS_BASIS = 8
HALF_LIFE_HOURS_FUNDING = 8

BASE_SPOT_RATE = 0.3
BASE_FUNDING_RATE = 0.3
BASE_BASIS = BASE_FUNDING_RATE/365

#############################################################################################

#################
# Crypto Reporter
#################
CR_IS_ADVANCED = True                # Set False to use only FTX, BB and CB
CR_IS_SHOW_COIN_LENDING = False      # Set True to see lendings in coins
CR_N_KR_ACCOUNTS = 4                 # Number of Kraken accounts

#############################################################################################

#########
# Apophis
#########
IS_IP_WHITELIST = True               # Use the whitelisted URI

#############################################################################################

####################################
# Simon's section -- can leave alone
####################################
import os
if os.environ.get('USERNAME')=='Simon':
  import SimonLib as sl
  API_KEY_FTX = sl.jLoad('API_KEY_FTX')
  API_SECRET_FTX = sl.jLoad('API_SECRET_FTX')
  API_KEY_BB = sl.jLoad('API_KEY_BB')
  API_SECRET_BB = sl.jLoad('API_SECRET_BB')
  API_KEY_BN = sl.jLoad('API_KEY_BN')
  API_SECRET_BN = sl.jLoad('API_SECRET_BN')
  API_KEY_KF = sl.jLoad('API_KEY_KF')
  API_SECRET_KF = sl.jLoad('API_SECRET_KF')
  API_KEY_KR1 = sl.jLoad('API_KEY_KR1')
  API_SECRET_KR1 = sl.jLoad('API_SECRET_KR1')
  API_KEY_KR2 = sl.jLoad('API_KEY_KR2')
  API_SECRET_KR2 = sl.jLoad('API_SECRET_KR2')
  API_KEY_KR3 = sl.jLoad('API_KEY_KR3')
  API_SECRET_KR3 = sl.jLoad('API_SECRET_KR3')
  API_KEY_KR4 = sl.jLoad('API_KEY_KR4')
  API_SECRET_KR4 = sl.jLoad('API_SECRET_KR4')
  API_KEY_CB = sl.jLoad('API_KEY_CB')
  API_SECRET_CB = sl.jLoad('API_SECRET_CB')
  EXTERNAL_EUR_DELTA = sl.jLoad('EXTERNAL_EUR_DELTA')
  EXTERNAL_EUR_REF = sl.jLoad('EXTERNAL_EUR_REF')
