###############
# Crypto Params
###############

######
# Main
######
API_KEY_FTX = ''
API_SECRET_FTX = ''
API_KEYS_BB = ['']        # List of keys to facilitate multiple bybit accounts
API_SECRETS_BB = ['']     # List of secrets to facilitate multiple bybit accounts
API_KEY_BN = ''
API_SECRET_BN = ''
API_KEY_DB = ''
API_SECRET_DB = ''
API_KEY_KF = ''
API_SECRET_KF = ''
API_KEY_KU = ''
API_SECRET_KU = ''
API_PASSWORD_KU = ''

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
CT_CONFIGS_DICT['MAX_BTC'] = 1                       # Limit for BTC in number of coins (secondary control)
CT_CONFIGS_DICT['MAX_ETH'] = 10                      # Limit for ETH in number of coins (secondary control)

CT_CONFIGS_DICT['CURRENT_BBT'] = 1                   # Current BBT account to trade with

CT_CONFIGS_DICT['SPOT_MAX_WAIT_TIME']=3              # Execution setting
CT_CONFIGS_DICT['FTX_MAX_WAIT_TIME']=3               # Execution setting
CT_CONFIGS_DICT['BBT_MAX_WAIT_TIME']=15              # Execution setting
CT_CONFIGS_DICT['BB_MAX_WAIT_TIME']=15               # Execution setting
CT_CONFIGS_DICT['DB_MAX_WAIT_TIME']=3                # Execution setting
CT_CONFIGS_DICT['KF_MAX_WAIT_TIME']=10               # Execution setting
CT_CONFIGS_DICT['KUT_MAX_WAIT_TIME']=3                # Execution setting

CT_CONFIGS_DICT['SPOT_LEG1_DISTANCE_TICKS']=-10      # Execution setting
CT_CONFIGS_DICT['FTX_LEG1_DISTANCE_TICKS']=-10       # Execution setting
CT_CONFIGS_DICT['BBT_LEG1_DISTANCE_TICKS']=-3        # Execution setting
CT_CONFIGS_DICT['BB_LEG1_DISTANCE_TICKS']=-3         # Execution setting
CT_CONFIGS_DICT['DB_LEG1_DISTANCE_TICKS']=-15        # Execution setting
CT_CONFIGS_DICT['KF_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['KUT_LEG1_DISTANCE_TICKS']=-3         # Execution setting

CT_CONFIGS_DICT['SPOT_LEG2_DISTANCE_TICKS']=1        # Execution setting
CT_CONFIGS_DICT['FTX_LEG2_DISTANCE_TICKS']=1         # Execution setting
CT_CONFIGS_DICT['BBT_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BB_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['DB_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['KF_LEG2_DISTANCE_TICKS']=1          # Execution setting
CT_CONFIGS_DICT['KUT_LEG2_DISTANCE_TICKS']=0          # Execution setting

# BN/BNT to be deprecated soon....
CT_CONFIGS_DICT['BNT_MAX_WAIT_TIME']=3               # Execution setting
CT_CONFIGS_DICT['BN_MAX_WAIT_TIME']=3                # Execution setting
CT_CONFIGS_DICT['BNT_LEG1_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BN_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['BNT_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BN_LEG2_DISTANCE_TICKS']=0          # Execution setting

#############################################################################################

##########################
# Apophis (Kraken Futures)
##########################
APOPHIS_CONFIGS_DICT=dict()
APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST'] = True

#################
# Crypto Reporter
#################
CR_QUOTE_CCY_DICT = dict({'USDT':4, 'BTC':1, 'ETH':1, 'FTT':1})  # Quoted currencies; values are # digits for display rounding
CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0})                      # Aggregated currencies; values are external deltas (# coins)
CR_FTX_FLOWS_CCYS = ['BTC', 'ETH']                               # FTX-flows currencies; borrow/lending cash flows are calculated for use in income calculations
CR_EXT_DELTA_USDT = 0

########
# Shared
########
SHARED_EXCH_DICT=dict({'ftx':1,'bbt':1,'bb':1,'bnt':0,'bn':0,'bnim':0,'db':1,'kf':1,'kut':1})
SHARED_CCY_DICT=dict()
SHARED_CCY_DICT['BTC'] = {'futExch': ['ftx', 'bbt', 'bb', 'db', 'kf', 'kut']}
SHARED_CCY_DICT['ETH'] = {'futExch': ['ftx', 'bbt', 'bb', 'db', 'kf', 'kut']}
SHARED_CCY_DICT['FTT'] = {'futExch':['ftx']}
SHARED_ETC_DICT=dict()
SHARED_ETC_DICT['FTX_SPOTLESS'] = ['ADA', 'ALGO', 'AVAX', 'DOT', 'EOS', 'ETC', 'FIL', 'ICP', 'XLM', 'HBAR', 'VET']

#############
# Smart Basis
#############
SMB_DICT=dict()
SMB_DICT['HALF_LIFE_HOURS']=8
SMB_DICT['BASE_RATE']=0.07
SMB_DICT['BASE_BASIS']=SMB_DICT['BASE_RATE']/365
SMB_DICT['USDT_COLLATERAL_COVERAGE']=1/6

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
  API_KEYS_BB = [sl.jLoad('API_KEY_BB'),sl.jLoad('API_KEY_BB2'),sl.jLoad('API_KEY_BB3')]
  API_SECRETS_BB = [sl.jLoad('API_SECRET_BB'),sl.jLoad('API_SECRET_BB2'),sl.jLoad('API_SECRET_BB3')]
  API_KEY_BN = sl.jLoad('API_KEY_BN')
  API_SECRET_BN = sl.jLoad('API_SECRET_BN')
  API_KEY_KF = sl.jLoad('API_KEY_KF')
  API_SECRET_KF = sl.jLoad('API_SECRET_KF')
  API_KEY_DB = sl.jLoad('API_KEY_DB')
  API_SECRET_DB = sl.jLoad('API_SECRET_DB')
  API_KEY_KU = sl.jLoad('API_KEY_KU')
  API_SECRET_KU = sl.jLoad('API_SECRET_KU')
  API_PASSWORD_KU = sl.jLoad('API_PASSWORD_KU')
  #####
  #APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST'] = False
  SHARED_EXCH_DICT=dict({'ftx':1,'bbt':3,'bb':0,'bnt':0,'bn':0,'bnim':0,'db':0,'kf':1,'kut':1})
  ############################################################################################################
  my_FTX=['AAVE']
  my_FTX_BBT=['XRP', 'DOGE', 'FTM', 'SOL', 'SUSHI', 'AXS']
  my_FTX_BBT_flowless=['ADA', 'AVAX', 'DOT', 'ETC', 'ICP']
  my_FTX_KUT_flowless=['HBAR','VET']
  my_KUT_append=['XRP', 'DOGE', 'FTM', 'SOL', 'ADA', 'DOT']
  ############################################################################################################
  for ccy in (my_FTX + my_FTX_BBT + my_FTX_BBT_flowless + my_FTX_KUT_flowless + my_KUT_append): CR_QUOTE_CCY_DICT[ccy] = 4
  for ccy in (my_FTX_BBT + my_FTX_BBT_flowless + my_FTX_KUT_flowless + my_KUT_append):  CR_AG_CCY_DICT[ccy] = 0
  CR_FTX_FLOWS_CCYS.extend(my_FTX + my_FTX_BBT)
  for ccy in my_FTX: SHARED_CCY_DICT[ccy] = {'futExch': ['ftx']}
  for ccy in (my_FTX_BBT + my_FTX_BBT_flowless): SHARED_CCY_DICT[ccy] = {'futExch': ['ftx', 'bbt']}
  for ccy in my_FTX_KUT_flowless: SHARED_CCY_DICT[ccy] = {'futExch': ['ftx', 'kut']}
  SHARED_CCY_DICT['XRP']['futExch'].append('bb')
  for ccy in my_KUT_append: SHARED_CCY_DICT[ccy]['futExch'].append('kut')
  #####
  #CR_AG_CCY_DICT['BTC']=-37.2 #bbftx
  #CR_AG_CCY_DICT['ETH']=29.302 #bbftx
  #CR_AG_CCY_DICT['XRP'] = 78999 #bbftx
  #CR_EXT_DELTA_USDT = 180e3 #bbftx
