###############
# Crypto Params
###############

######
# Main
######
CRYPTO_MODE = 1         # 0 = FTX/BB only; 1 = +BBT/BN/BNT/DB/KF/KR
API_KEY_FTX = ''
API_SECRET_FTX = ''
API_KEY_BB = ''
API_SECRET_BB = ''
API_KEY_BN = ''
API_SECRET_BN = ''
API_KEY_DB = ''
API_SECRET_DB = ''
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

#############################################################################################

###############
# Crypto Trader
###############
CT_CONFIGS_DICT=dict()

#####
# BTC
#####
# 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_BTC_OK']=1
CT_CONFIGS_DICT['FTX_BTC_OK']=1
CT_CONFIGS_DICT['BB_BTC_OK']=1
CT_CONFIGS_DICT['BBT_BTC_OK']=1
CT_CONFIGS_DICT['BN_BTC_OK']=1
CT_CONFIGS_DICT['BNT_BTC_OK']=1
CT_CONFIGS_DICT['DB_BTC_OK']=0 ### Off
CT_CONFIGS_DICT['KF_BTC_OK']=1

# Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BBT_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BN_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BNT_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['DB_BTC_ADJ_BPS']=0 ### Off
CT_CONFIGS_DICT['KF_BTC_ADJ_BPS']=0

#####
# ETH
#####
# 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_ETH_OK']=0
CT_CONFIGS_DICT['FTX_ETH_OK']=0
CT_CONFIGS_DICT['BB_ETH_OK']=0
CT_CONFIGS_DICT['BBT_ETH_OK']=0
CT_CONFIGS_DICT['BN_ETH_OK']=0
CT_CONFIGS_DICT['BNT_ETH_OK']=1
CT_CONFIGS_DICT['DB_ETH_OK']=1
CT_CONFIGS_DICT['KF_ETH_OK']=0

# Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BBT_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BN_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BNT_ETH_ADJ_BPS']=5
CT_CONFIGS_DICT['DB_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['KF_ETH_ADJ_BPS']=0

#####
# XRP
#####
# 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_XRP_OK']=0
CT_CONFIGS_DICT['FTX_XRP_OK']=0
CT_CONFIGS_DICT['BB_XRP_OK']=0
CT_CONFIGS_DICT['BN_XRP_OK']=1
CT_CONFIGS_DICT['BNT_XRP_OK']=0
CT_CONFIGS_DICT['KF_XRP_OK']=1

# Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BN_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BNT_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['KF_XRP_ADJ_BPS']=-10

#############################################################################################

CT_IS_NO_FUT_BUYS_WHEN_LONG = True   # Stop buying futures when position is long?
CT_IS_HIGH_USD_RATE_PAUSE = True     # Trading of spot paused when spot rates >= 100%?
CT_STREAK = 5                        # Number of observations through target before triggering
CT_STREAK_BPS_RANGE = 10             # Max number of allowed bps for range of observations
CT_NPROGRAMS = 50                    # Number of programs (each program being a pair of trades)
CT_K = 2/(60 * 15 / 4 + 1)           # EMA smoothing parameter

CT_TRADE_BTC_NOTIONAL = 5000         # Per trade notional
CT_TRADE_ETH_NOTIONAL = 5000         # Per trade notional
CT_TRADE_XRP_NOTIONAL = 3000         # Per trade notional

CT_MAX_NOTIONAL = 50000              # Hard limit
CT_MAX_BTC = 0.5                     # Hard limit
CT_MAX_ETH = 10                      # Hard limit
CT_MAX_XRP = 10000                   # Hard limit

CT_FTX_DISTANCE_TO_BEST_BPS=0        # Execution setting
CT_BB_DISTANCE_TO_BEST_BPS=-5        # Execution setting
CT_BBT_DISTANCE_TO_BEST_BPS=-2.5     # Execution setting
CT_BN_DISTANCE_TO_BEST_BPS=0         # Execution setting
CT_BNT_DISTANCE_TO_BEST_BPS=0        # Execution setting
CT_DB_DISTANCE_TO_BEST_BPS=0         # Execution setting
CT_KF_DISTANCE_TO_BEST_BPS=0         # Execution setting
CT_MAX_WAIT_TIME=10                  # Execution setting

#############################################################################################

##########################
# Apophis (Kraken Futures)
##########################
APOPHIS_IS_IP_WHITELIST = True

#################
# Crypto Reporter
#################
CR_IS_SHOW_COIN_LENDING = False
CR_N_KR_ACCOUNTS = 1
CR_QUOTE_CCY_DICT = dict({'BTC':1, 'ETH':1, 'XRP':4, 'FTT':1, 'USDT':4, 'EUR':4})        # Quote currencies: values are nDigits for display
CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0, 'XRP': 0})                                    # Aggregated currencies: values are external deltas (# coins)
CR_FTX_FLOWS_CCYS = ['BTC', 'ETH', 'XRP', 'USD', 'USDT']                                 # FTX flows currencies: borrow/lending cash flows are calculated for these
CR_KR_CCY_DICT = dict({'BTC': 'XXBT', 'ETH': 'XETH', 'XRP': 'XXRP', 'EUR': 'ZEUR'})      # Kraken currencies: values are Kraken currency names
CR_EXTERNAL_USDT_DELTA = 0
CR_EXTERNAL_EUR_DELTA = 0
CR_EXTERNAL_EUR_REF = 0

###########
# Internals
###########
INT_CCY_DICT=dict() # Exch = Valid futures exchanges
INT_CCY_DICT['BTC']={'exch':['ftx', 'bb', 'bbt', 'bn', 'bnt', 'db', 'kf']}
INT_CCY_DICT['ETH']={'exch':['ftx', 'bb', 'bbt', 'bn', 'bnt', 'db', 'kf']}
INT_CCY_DICT['XRP']={'exch':['ftx', 'bb', 'bn', 'bnt', 'kf']}
INT_CCY_DICT['FTT']={'exch':['ftx']}

#############
# Smart Basis
#############
SMB_HALF_LIFE_HOURS = 8
SMB_BASE_RATE = 0.25
SMB_BASE_BASIS = SMB_BASE_RATE / 365
SMB_USDT_COLLATERAL_COVERAGE = 1 / 5

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
  API_KEY_DB = sl.jLoad('API_KEY_DB')
  API_SECRET_DB = sl.jLoad('API_SECRET_DB')
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
  CR_EXTERNAL_USDT_DELTA = sl.jLoad('EXTERNAL_USDT_DELTA')
  CR_EXTERNAL_EUR_DELTA = sl.jLoad('EXTERNAL_EUR_DELTA')
  CR_EXTERNAL_EUR_REF = sl.jLoad('EXTERNAL_EUR_REF')
  #####
  CR_AG_CCY_DICT = dict({'BTC': sl.jLoad('EXTERNAL_BTC_DELTA'), 'ETH': sl.jLoad('EXTERNAL_ETH_DELTA'), 'XRP': sl.jLoad('EXTERNAL_XRP_DELTA')})
  CR_QUOTE_CCY_DICT['MATIC']=6
  INT_CCY_DICT['MATIC'] = {'exch': ['ftx']}
