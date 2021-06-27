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

CT_CONFIGS_DICT['FTX_DISTANCE_TO_BEST_BPS']=-1       # Execution setting
CT_CONFIGS_DICT['BBT_DISTANCE_TO_BEST_BPS']=-1       # Execution setting
CT_CONFIGS_DICT['BNT_DISTANCE_TO_BEST_BPS']=0        # Execution setting
CT_CONFIGS_DICT['KF_DISTANCE_TO_BEST_BPS']=0         # Execution setting
CT_CONFIGS_DICT['BB_DISTANCE_TO_BEST_BPS']=-1        # Execution setting
CT_CONFIGS_DICT['BN_DISTANCE_TO_BEST_BPS']=0         # Execution setting
CT_CONFIGS_DICT['MAX_WAIT_TIME']=10                  # Execution setting

#############################################################################################

CT_CONFIGS_DICT['ROUND_PRICE_FTX']=dict({'BTC':[0,None],'ETH':[0,1],'FTT':[0,3],'DOGE':[1,2e6],'LTC':[1,200],'XRP':[1,40000],
                                         'AAVE':[0,2],'LINK':[1,2000],'SOL':[1,400]})
CT_CONFIGS_DICT['ROUND_PRICE_BBT']=dict({'BTC':[1,2],'ETH':[1,20],'DOGE':[0,4],'LTC':[0,2],'XRP':[0,4],
                                         'AAVE':[1,20],'BCH':[1,20],'LINK':[0,3]})
CT_CONFIGS_DICT['ROUND_PRICE_BNT']=dict({'BTC':[0,2],'ETH':[0,2],'DOGE':[0,5],'LTC':[0,2],'MATIC':[0,5],'XRP':[0,4],
                                         'AAVE':[0,2],'BCH':[0,2],'BNB':[0,3],'LINK':[0,3]})
CT_CONFIGS_DICT['ROUND_PRICE_KF']=dict({'BTC':[1,2],'ETH':[1,20],'LTC':[0,2],'XRP':[0,4]})
CT_CONFIGS_DICT['ROUND_PRICE_BB']=dict({'BTC':[1,2],'ETH':[1,20],'XRP':[0,4]})
CT_CONFIGS_DICT['ROUND_PRICE_BN']=dict({'BTC':[0,1],'ETH':[0,2],'LTC':[0,2],'XRP':[0,4],
                                        'BNB':[0,3]})

# Default # digits for rounding = 3
CT_CONFIGS_DICT['ROUND_QTY_FTX']=dict({'BTC':4, 'ETH':3, 'FTT':1, 'DOGE':None, 'LTC':2, 'MATIC':-1,'XRP':None,
                                       'AAVE':2,'BCH':3, 'BNB':1, 'LINK':1})
CT_CONFIGS_DICT['ROUND_QTY_BNT']=dict({'DOGE':None,'MATIC':None,'XRP':1,
                                       'AAVE':1,'BNB':2,'LINK':2})

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
CR_QUOTE_CCY_DICT = dict({'BTC':1, 'ETH':1, 'FTT':1, 'USDT':4})  # Quoted currencies; values are # digits for display rounding
CR_AG_CCY_DICT = dict({'BTC': 0, 'ETH': 0})                      # Aggregated currencies; values are external deltas (# coins)
CR_FTX_FLOWS_CCYS = ['BTC', 'ETH']                               # FTX-flows currencies; borrow/lending cash flows are calculated for use in income calculations
CR_EXT_DELTA_USDT = 0

########
# Shared
########
SHARED_EXCH_DICT=dict({'ftx':1,'bbt':1,'bnt':1,'kf':1,'bb':1,'bn':1})
SHARED_CCY_DICT=dict()
SHARED_CCY_DICT['BTC'] = {'futExch': ['ftx', 'bbt', 'bnt', 'kf', 'bb', 'bn']}
SHARED_CCY_DICT['ETH'] = {'futExch': ['ftx', 'bbt', 'bnt', 'kf', 'bb', 'bn']}
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
  #####
  #CR_IS_ENABLE_BN_ISOLATED_MARGIN = True
  SHARED_EXCH_DICT = dict({'ftx': 1, 'bbt': 1, 'bnt': 1, 'kf': 1, 'bb': 1, 'bn': 0})
  CR_QUOTE_CCY_DICT['XRP'] = 4
  CR_QUOTE_CCY_DICT['MATIC'] = 4
  CR_AG_CCY_DICT['XRP'] = 0
  CR_AG_CCY_DICT['MATIC'] = 0
  CR_FTX_FLOWS_CCYS.extend(['XRP','MATIC'])
  SHARED_CCY_DICT['XRP'] = {'futExch': ['ftx', 'bbt', 'bnt', 'kf','bb']}
  SHARED_CCY_DICT['MATIC'] = {'futExch': ['ftx', 'bnt']}
  SHARED_CCY_DICT['BNB'] = {'futExch': ['bnt']}
  #####
  CR_AG_CCY_DICT['BTC']=9.01 #bbftx
  #CR_AG_CCY_DICT['ETH']=54.43 #ftxkf
  #CR_AG_CCY_DICT['XRP'] = 360530 #bb:ftx
  #CR_EXT_DELTA_USDT = 150000 #ftxbb
