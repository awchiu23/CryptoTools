###############
# Crypto Params
###############

######
# Main
######
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

#############################################################################################

###############
# Crypto Trader
###############
CT_CONFIGS_DICT=dict()

CT_CONFIGS_DICT['IS_HIGH_USD_RATE_PAUSE'] = True     # Trading of spot paused when spot rates >= 100%?
CT_CONFIGS_DICT['STREAK'] = 3                        # Number of observations through target before triggering
CT_CONFIGS_DICT['STREAK_RANGE_BPS'] = 5              # Max number of allowed bps for range of observations
CT_CONFIGS_DICT['NPROGRAMS'] = 100                   # Number of programs (each program being a pair of trades)
CT_CONFIGS_DICT['EMA_K'] = 2/(60 * 15 / 5 + 1)       # EMA smoothing parameter

CT_CONFIGS_DICT['MAX_NOTIONAL_USD'] = 50000          # Universal notional limit in USD
CT_CONFIGS_DICT['MAX_BTC'] = 1                       # Limit for BTC in number of coins
CT_CONFIGS_DICT['MAX_ETH'] = 10                      # Limit for ETH in number of coins

CT_CONFIGS_DICT['MAX_WAIT_TIME']=10                  # Execution setting
CT_CONFIGS_DICT['SPOT_LEG1_DISTANCE_TICKS']=0        # Execution setting
CT_CONFIGS_DICT['FTX_LEG1_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BBT_LEG1_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BB_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['BNT_LEG1_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BN_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['DB_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['KF_LEG1_DISTANCE_TICKS']=0          # Execution setting

CT_CONFIGS_DICT['SPOT_LEG2_DISTANCE_TICKS']=0        # Execution setting
CT_CONFIGS_DICT['FTX_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BBT_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BB_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['BNT_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BN_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['DB_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['KF_LEG2_DISTANCE_TICKS']=0          # Execution setting

#############################################################################################

##########################
# Apophis (Kraken Futures)
##########################
APOPHIS_CONFIGS_DICT=dict()
APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST'] = True

#################
# Crypto Reporter
#################
CR_IS_ENABLE_BN_ISOLATED_MARGIN = False
CR_QUOTE_CCY_DICT = dict({'USDT':4, 'BTC':1, 'ETH':1, 'FTT':1})  # Quoted currencies; values are # digits for display rounding
CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0})                      # Aggregated currencies; values are external deltas (# coins)
CR_FTX_FLOWS_CCYS = ['BTC', 'ETH']                               # FTX-flows currencies; borrow/lending cash flows are calculated for use in income calculations
CR_EXT_DELTA_USDT = 0

########
# Shared
########
SHARED_EXCH_DICT=dict({'ftx':1,'bbt':1,'bb':1,'bnt':1,'bn':1,'db':1,'kf':1})
SHARED_CCY_DICT=dict()
SHARED_CCY_DICT['BTC'] = {'futExch': ['ftx', 'bbt', 'bb', 'bnt', 'bn', 'db', 'kf']}
SHARED_CCY_DICT['ETH'] = {'futExch': ['ftx', 'bbt', 'bb', 'bnt', 'bn', 'db', 'kf']}
SHARED_CCY_DICT['FTT'] = {'futExch':['ftx']}

#############
# Smart Basis
#############
SMB_HALF_LIFE_HOURS = 8
SMB_BASE_RATE = 0.02
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
  if 'COLAB' in os.environ: APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST'] = False
  #####
  API_KEY_FTX = sl.jLoad('API_KEY_FTX')
  API_SECRET_FTX = sl.jLoad('API_SECRET_FTX')
  API_KEY_BB = sl.jLoad('API_KEY_BB')
  API_SECRET_BB = sl.jLoad('API_SECRET_BB')
  API_KEY_BN = sl.jLoad('API_KEY_BN')
  API_SECRET_BN = sl.jLoad('API_SECRET_BN')
  API_KEY_KF = sl.jLoad('API_KEY_KF')
  API_SECRET_KF = sl.jLoad('API_SECRET_KF')
  API_KEY_DB = sl.jLoad('API_KEY_DB')
  API_SECRET_DB = sl.jLoad('API_SECRET_DB')
  #####
  #CR_IS_ENABLE_BN_ISOLATED_MARGIN = True
  #SHARED_EXCH_DICT=dict({'ftx':1,'bbt':1,'bb':1,'bnt':1,'bn':1,'db':1,'kf':1})
  CR_QUOTE_CCY_DICT['XRP'] = 4
  CR_QUOTE_CCY_DICT['LTC'] = 4
  CR_QUOTE_CCY_DICT['BNB'] = 4
  CR_AG_CCY_DICT['XRP'] = 0
  CR_AG_CCY_DICT['LTC'] = 0
  CR_AG_CCY_DICT['BNB'] = 0
  CR_FTX_FLOWS_CCYS.extend(['XRP','LTC','BNB'])
  SHARED_CCY_DICT['XRP'] = {'futExch': ['ftx','bbt','bb','bnt','bn','kf']}
  SHARED_CCY_DICT['LTC'] = {'futExch': ['ftx','bbt','bnt','bn','kf']}
  SHARED_CCY_DICT['BNB'] = {'futExch': ['ftx','bbt','bnt']}
  #####
  #CR_AG_CCY_DICT['BTC']=13.059 #bnftx
  #CR_AG_CCY_DICT['ETH']=96.9 #bbftx
  #CR_AG_CCY_DICT['XRP'] = 334280 #bbftx
  #CR_AG_CCY_DICT['LTC'] = 374 #ftxkf
  #CR_EXT_DELTA_USDT = 250e3 #bbftx
