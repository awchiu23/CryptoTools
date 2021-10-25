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
API_KEY_DB = ''
API_SECRET_DB = ''
API_KEY_KF = ''
API_SECRET_KF = ''
API_KEYS_KUT = ['']       # List of keys to facilitate multiple kucoin accounts
API_SECRETS_KUT = ['']    # List of secrets to facilitate multiple kucoin accounts
API_PASSWORDS_KUT = ['']  # List of passwords to facilitate multiple kucoin accounts

#############################################################################################

###############
# Crypto Trader
###############
CT_CONFIGS_DICT=dict()

CT_CONFIGS_DICT['IS_HIGH_USD_RATE_PAUSE'] = True     # Trading of spot paused when usd rates >= 100%?
CT_CONFIGS_DICT['STREAK'] = 3                        # Number of observations through target before triggering
CT_CONFIGS_DICT['STREAK_RANGE_BPS'] = 5              # Max number of allowed bps for range of observations
CT_CONFIGS_DICT['NPROGRAMS'] = 100                   # Number of programs (each program being a pair of trades)
CT_CONFIGS_DICT['EMA_K'] = 2/(60 * 15 / 5 + 1)       # EMA smoothing parameter

CT_CONFIGS_DICT['MAX_NOTIONAL_USD'] = 50000          # Universal notional limit in USD

CT_CONFIGS_DICT['CURRENT_BBT'] = 1                   # Current BBT account to trade with
CT_CONFIGS_DICT['CURRENT_KUT'] = 1                   # Current KUT account to trade with
CT_CONFIGS_DICT['IS_BBT_STEPPER']=False              # Special trade mode for BBT
CT_CONFIGS_DICT['IS_KUT_STEPPER']=False              # Special trade mode for KUT

CT_CONFIGS_DICT['SPOT_MAX_WAIT_TIME']=3              # Execution setting
CT_CONFIGS_DICT['FTX_MAX_WAIT_TIME']=3               # Execution setting
CT_CONFIGS_DICT['BBT_MAX_WAIT_TIME']=15              # Execution setting
CT_CONFIGS_DICT['BB_MAX_WAIT_TIME']=15               # Execution setting
CT_CONFIGS_DICT['DB_MAX_WAIT_TIME']=3                # Execution setting
CT_CONFIGS_DICT['KF_MAX_WAIT_TIME']=10               # Execution setting
CT_CONFIGS_DICT['KUT_MAX_WAIT_TIME']=10              # Execution setting

CT_CONFIGS_DICT['SPOT_LEG1_DISTANCE_TICKS']=-10      # Execution setting
CT_CONFIGS_DICT['FTX_LEG1_DISTANCE_TICKS']=-10       # Execution setting
CT_CONFIGS_DICT['BBT_LEG1_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BB_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['DB_LEG1_DISTANCE_TICKS']=-15        # Execution setting
CT_CONFIGS_DICT['KF_LEG1_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['KUT_LEG1_DISTANCE_TICKS']=0         # Execution setting

CT_CONFIGS_DICT['SPOT_LEG2_DISTANCE_TICKS']=0        # Execution setting
CT_CONFIGS_DICT['FTX_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BBT_LEG2_DISTANCE_TICKS']=0         # Execution setting
CT_CONFIGS_DICT['BB_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['DB_LEG2_DISTANCE_TICKS']=0          # Execution setting
CT_CONFIGS_DICT['KF_LEG2_DISTANCE_TICKS']=1          # Execution setting
CT_CONFIGS_DICT['KUT_LEG2_DISTANCE_TICKS']=0          # Execution setting

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
CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0, 'FTT':0})             # Aggregated currencies; values are external deltas (# coins)
CR_FTX_FLOWS_CCYS = ['BTC', 'ETH']                               # FTX-flows currencies; borrow/lending cash flows are calculated for use in income calculations
CR_EXT_DELTA_USDT = 0
CR_CONFIGS_DICT=dict()
CR_CONFIGS_DICT['IS_KU_CALC_PAYMENTS'] = True

########
# Shared
########
SHARED_EXCH_DICT=dict({'ftx':1,'bbt':1,'bb':1,'db':1,'kf':1,'kut':1})
SHARED_CCY_DICT=dict()
SHARED_CCY_DICT['BTC'] = {'futExch': ['ftx', 'bbt', 'bb', 'db', 'kf', 'kut']}
SHARED_CCY_DICT['ETH'] = {'futExch': ['ftx', 'bbt', 'bb', 'db', 'kf', 'kut']}
SHARED_CCY_DICT['FTT'] = {'futExch':['ftx', 'bbt']}
SHARED_ETC_DICT=dict()
SHARED_ETC_DICT['FTX_SPOTLESS'] = ['ADA', 'ALGO', 'ATOM', 'AVAX', 'DOT', 'EOS', 'ETC', 'FIL', 'LUNA', 'ONE','VET','XLM']

#############
# Smart Basis
#############
SMB_DICT=dict()
SMB_DICT['HALF_LIFE_HOURS']=8
SMB_DICT['BASE_RATE']=0.15
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
  if 'COLAB' in os.environ:
    API_KEYS_BB = sl.jLoad('API_KEYS_BB_NO_IP')
    API_SECRETS_BB = sl.jLoad('API_SECRETS_BB_NO_IP')
    APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST'] = False
    CR_CONFIGS_DICT['IS_KU_CALC_PAYMENTS'] = False
  else:
    API_KEYS_BB = sl.jLoad('API_KEYS_BB')
    API_SECRETS_BB = sl.jLoad('API_SECRETS_BB')
    from win32api import GetKeyState
    from win32con import VK_CAPITAL
    CR_CONFIGS_DICT['IS_KU_CALC_PAYMENTS'] = bool(GetKeyState(VK_CAPITAL))
  #####
  API_KEY_FTX = sl.jLoad('API_KEY_FTX')
  API_SECRET_FTX = sl.jLoad('API_SECRET_FTX')
  API_KEY_KF = sl.jLoad('API_KEY_KF')
  API_SECRET_KF = sl.jLoad('API_SECRET_KF')
  API_KEY_DB = sl.jLoad('API_KEY_DB')
  API_SECRET_DB = sl.jLoad('API_SECRET_DB')
  API_KEYS_KUT = sl.jLoad('API_KEYS_KUT')
  API_SECRETS_KUT = sl.jLoad('API_SECRETS_KUT')
  API_PASSWORDS_KUT = sl.jLoad('API_PASSWORDS_KUT')
  #####
  CT_CONFIGS_DICT['IS_BBT_STEPPER'] = True
  CT_CONFIGS_DICT['IS_KUT_STEPPER'] = True
  APOPHIS_CONFIGS_DICT['IS_IP_WHITELIST'] = False
  SHARED_EXCH_DICT=dict({'ftx':1,'bbt':1,'bb':0,'db':0,'kf':0,'kut':18})
  SHARED_ETC_DICT['SHIFT'] = 15
  ############################################################################################################
  my_FTX=['FTM']
  my_FTX_BBT_KUT=['DOGE']
  my_FTX_BBT_KUT_flowless=[]
  my_FTX_BBT=[]
  my_FTX_BBT_flowless=[]
  my_FTX_KUT=['XRP','FTM','LINK','LTC','SOL','SUSHI']
  my_FTX_KUT_flowless=['ADA','ALGO','ATOM','DOT','DYDX','FIL','LUNA','SHIB','VET']
  ############################################################################################################
  for ccy in (my_FTX + my_FTX_BBT_KUT + my_FTX_BBT_KUT_flowless + my_FTX_BBT + my_FTX_BBT_flowless + my_FTX_KUT + my_FTX_KUT_flowless): CR_QUOTE_CCY_DICT[ccy] = 4
  for ccy in (my_FTX_BBT_KUT + my_FTX_BBT_KUT_flowless + my_FTX_BBT + my_FTX_BBT_flowless + my_FTX_KUT + my_FTX_KUT_flowless):  CR_AG_CCY_DICT[ccy] = 0
  CR_FTX_FLOWS_CCYS.extend(my_FTX + my_FTX_BBT_KUT + my_FTX_BBT + my_FTX_KUT)
  for ccy in my_FTX: SHARED_CCY_DICT[ccy] = {'futExch': ['ftx']}
  for ccy in (my_FTX_BBT_KUT + my_FTX_BBT_KUT_flowless): SHARED_CCY_DICT[ccy] = {'futExch': ['ftx', 'bbt','kut']}
  for ccy in (my_FTX_BBT + my_FTX_BBT_flowless): SHARED_CCY_DICT[ccy] = {'futExch': ['ftx', 'bbt']}
  for ccy in (my_FTX_KUT + my_FTX_KUT_flowless): SHARED_CCY_DICT[ccy] = {'futExch': ['ftx', 'kut']}
  SHARED_CCY_DICT['BTC']['futExch'].remove('bbt')
  SHARED_CCY_DICT['ETH']['futExch'].remove('bbt')
  SHARED_CCY_DICT['FTT']['futExch'].remove('bbt')
  #SHARED_CCY_DICT['BTC']['futExch'].remove('kut')
  #SHARED_CCY_DICT['ETH']['futExch'].remove('kut')
  #SHARED_CCY_DICT['XRP']['futExch'].append('bb')
  #####
  #CR_AG_CCY_DICT['BTC']=2.523 #bbftx
  #CR_AG_CCY_DICT['ETH']=33.995 #bbftx
  #CR_AG_CCY_DICT['XRP'] = 261190 #bbftx
  #CR_EXT_DELTA_USDT = 40000 #bbftx
