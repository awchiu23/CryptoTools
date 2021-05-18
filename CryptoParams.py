###############
# Crypto Params
###############

######
# Main
######
CRYPTO_MODE = 1         # 0 = FTX/BB/BBT only; 1 = +BN/BNT/KF/KR
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

#############################################################################################

###############
# Crypto Trader
###############
CT_CONFIGS_DICT=dict()

#####
# BTC
#####
# 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_BTC_OK']=0
CT_CONFIGS_DICT['FTX_BTC_OK']=0
CT_CONFIGS_DICT['BB_BTC_OK']=0
CT_CONFIGS_DICT['BBT_BTC_OK']=0
CT_CONFIGS_DICT['BN_BTC_OK']=0
CT_CONFIGS_DICT['BNT_BTC_OK']=0
CT_CONFIGS_DICT['KF_BTC_OK']=0

# Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BBT_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BN_BTC_ADJ_BPS']=0
CT_CONFIGS_DICT['BNT_BTC_ADJ_BPS']=0
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
CT_CONFIGS_DICT['BNT_ETH_OK']=0
CT_CONFIGS_DICT['KF_ETH_OK']=0

# Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BBT_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BN_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['BNT_ETH_ADJ_BPS']=0
CT_CONFIGS_DICT['KF_ETH_ADJ_BPS']=0

#####
# XRP
#####
# 0=Disabled; 1=Enabled
CT_CONFIGS_DICT['SPOT_XRP_OK']=0
CT_CONFIGS_DICT['FTX_XRP_OK']=0
CT_CONFIGS_DICT['BB_XRP_OK']=0
CT_CONFIGS_DICT['BBT_XRP_OK']=0
CT_CONFIGS_DICT['BN_XRP_OK']=0
CT_CONFIGS_DICT['BNT_XRP_OK']=0
CT_CONFIGS_DICT['KF_XRP_OK']=0

# Positive = eager to buy; Negative = eager to sell
CT_CONFIGS_DICT['SPOT_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['FTX_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BB_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BBT_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BN_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['BNT_XRP_ADJ_BPS']=0
CT_CONFIGS_DICT['KF_XRP_ADJ_BPS']=0

#############################################################################################

CT_CONFIGS_DICT['IS_NO_FUT_BUYS_WHEN_LONG'] = True   # Stop buying futures when position is long?
CT_CONFIGS_DICT['IS_HIGH_USD_RATE_PAUSE'] = True     # Trading of spot paused when spot rates >= 100%?
CT_CONFIGS_DICT['STREAK'] = 5                        # Number of observations through target before triggering
CT_CONFIGS_DICT['STREAK_RANGE_BPS'] = 10             # Max number of allowed bps for range of observations
CT_CONFIGS_DICT['NPROGRAMS'] = 50                    # Number of programs (each program being a pair of trades)
CT_CONFIGS_DICT['EMA_K'] = 2/(60 * 15 / 4 + 1)       # EMA smoothing parameter

CT_CONFIGS_DICT['TRADE_BTC_NOTIONAL'] = 5000         # Per trade notional
CT_CONFIGS_DICT['TRADE_ETH_NOTIONAL'] = 5000         # Per trade notional
CT_CONFIGS_DICT['TRADE_XRP_NOTIONAL'] = 5000         # Per trade notional

CT_CONFIGS_DICT['MAX_NOTIONAL'] = 50000              # Hard limit
CT_CONFIGS_DICT['MAX_BTC'] = 0.5                     # Hard limit
CT_CONFIGS_DICT['MAX_ETH'] = 10                      # Hard limit
CT_CONFIGS_DICT['MAX_XRP'] = 10000                   # Hard limit

CT_CONFIGS_DICT['FTX_DISTANCE_TO_BEST_BPS']=0        # Execution setting
CT_CONFIGS_DICT['BB_DISTANCE_TO_BEST_BPS']=-3        # Execution setting
CT_CONFIGS_DICT['BBT_DISTANCE_TO_BEST_BPS']=-3       # Execution setting
CT_CONFIGS_DICT['BN_DISTANCE_TO_BEST_BPS']=0         # Execution setting
CT_CONFIGS_DICT['BNT_DISTANCE_TO_BEST_BPS']=0        # Execution setting
CT_CONFIGS_DICT['KF_DISTANCE_TO_BEST_BPS']=0         # Execution setting
CT_CONFIGS_DICT['MAX_WAIT_TIME']=10                  # Execution setting

#############################################################################################

##########################
# Apophis (Kraken Futures)
##########################
APOPHIS_IS_IP_WHITELIST = True

#################
# Crypto Reporter
#################
CR_IS_SHOW_COIN_LENDING = False
CR_N_KR_ACCOUNTS = 0
CR_QUOTE_CCY_DICT = dict({'BTC':1, 'ETH':1, 'XRP':4, 'FTT':1, 'USDT':4, 'EUR':4})        # Quoted currencies; values are # digits for display rounding
CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0, 'XRP': 0})                                    # Aggregated currencies; values are external deltas (# coins)
CR_FTX_FLOWS_CCYS = ['BTC', 'ETH', 'XRP', 'USD', 'USDT']                                 # FTX-flows currencies; borrow/lending cash flows are calculated for use in income calculations
CR_KR_CCY_DICT = dict({'BTC': 'XXBT', 'ETH': 'XETH', 'XRP': 'XXRP', 'EUR': 'ZEUR'})      # Kraken currencies; values are Kraken currency names
CR_EXT_DELTA_USDT = 0
CR_EXT_DELTA_EUR = 0
CR_EXT_DELTA_EUR_REF = 0

########
# Shared
########
SHARED_CCY_DICT=dict()
SHARED_CCY_DICT['BTC']={'futExch':['ftx', 'bb', 'bbt', 'bn', 'bnt', 'kf']}
SHARED_CCY_DICT['ETH']={'futExch':['ftx', 'bb', 'bbt', 'bn', 'bnt', 'kf']}
SHARED_CCY_DICT['XRP']={'futExch':['ftx', 'bb', 'bbt', 'bn', 'bnt', 'kf']}
SHARED_CCY_DICT['FTT']={'futExch':['ftx']}

#############
# Smart Basis
#############
SMB_HALF_LIFE_HOURS = 8
SMB_BASE_RATE = 0.15
SMB_BASE_BASIS = SMB_BASE_RATE / 365
SMB_USDT_COLLATERAL_COVERAGE = 1 / 6

#############################################################################################

##################################
# Simon's section -- please ignore
##################################
import os
if os.environ.get('USERNAME')=='Simon':
  import SimonLib as sl
  #####
  if 'COLAB' in os.environ: APOPHIS_IS_IP_WHITELIST = False
  #####
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
  #####
  CR_QUOTE_CCY_DICT['LTC'] = 2
  CR_QUOTE_CCY_DICT['MATIC'] = 4
  CR_QUOTE_CCY_DICT['SOL'] = 2
  CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0, 'XRP': 0, 'LTC':0})
  CR_EXT_DELTA_USDT = 0
  CR_EXT_DELTA_EUR = 125000*0
  CR_EXT_DELTA_EUR_REF = 0
  SHARED_CCY_DICT['LTC'] = {'futExch': ['ftx', 'bbt', 'bnt']}
  SHARED_CCY_DICT['MATIC'] = {'futExch': ['ftx']}
  SHARED_CCY_DICT['SOL'] = {'futExch': ['ftx']}
  SHARED_CCY_DICT['BNB'] = {'futExch': ['bnt']}
  #####
  #CT_CONFIGS_DICT['IS_HIGH_USD_RATE_PAUSE'] = False    # **************************************** #
  #CT_CONFIGS_DICT['IS_NO_FUT_BUYS_WHEN_LONG'] = False  # **************************************** #
  #####
  # BTC: 0=Disabled; 1=Enabled / Positive = eager to buy; Negative = eager to sell
  CT_CONFIGS_DICT['SPOT_BTC_OK'] = 1
  CT_CONFIGS_DICT['FTX_BTC_OK'] = 1
  CT_CONFIGS_DICT['BBT_BTC_OK'] = 0
  CT_CONFIGS_DICT['BNT_BTC_OK'] = 0
  CT_CONFIGS_DICT['SPOT_BTC_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['FTX_BTC_ADJ_BPS'] = 15
  CT_CONFIGS_DICT['BBT_BTC_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['BNT_BTC_ADJ_BPS'] = 0
  #####
  CT_CONFIGS_DICT['KF_BTC_OK'] = 0
  CT_CONFIGS_DICT['KF_BTC_ADJ_BPS'] = 0
  #####
  # ETH: 0=Disabled; 1=Enabled / Positive = eager to buy; Negative = eager to sell
  CT_CONFIGS_DICT['SPOT_ETH_OK'] = 1
  CT_CONFIGS_DICT['FTX_ETH_OK'] = 1
  CT_CONFIGS_DICT['BBT_ETH_OK'] = 0
  CT_CONFIGS_DICT['BNT_ETH_OK'] = 0
  CT_CONFIGS_DICT['SPOT_ETH_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['FTX_ETH_ADJ_BPS'] = 15
  CT_CONFIGS_DICT['BBT_ETH_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['BNT_ETH_ADJ_BPS'] = 0
  #####
  CT_CONFIGS_DICT['KF_ETH_OK'] = 0
  CT_CONFIGS_DICT['KF_ETH_ADJ_BPS'] = 0
  #####
  # XRP: 0=Disabled; 1=Enabled / Positive = eager to buy; Negative = eager to sell
  CT_CONFIGS_DICT['SPOT_XRP_OK'] = 1
  CT_CONFIGS_DICT['FTX_XRP_OK'] = 1
  CT_CONFIGS_DICT['BBT_XRP_OK'] = 1
  CT_CONFIGS_DICT['BNT_XRP_OK'] = 1
  CT_CONFIGS_DICT['SPOT_XRP_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['FTX_XRP_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['BBT_XRP_ADJ_BPS'] = 0
  CT_CONFIGS_DICT['BNT_XRP_ADJ_BPS'] = 0

