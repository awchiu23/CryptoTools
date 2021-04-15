import CryptoLib as cl
import time
import termcolor
import datetime
import pandas as pd
import ccxt
from retrying import retry

########
# Params
########
API_KEY_DB = ''
API_SECRET_DB = ''

####################################
# Simon's section -- can leave alone
####################################
import os
if os.environ.get('USERNAME')=='Simon':
  import SimonLib as sl
  API_KEY_DB = sl.jLoad('API_KEY_DB')
  API_SECRET_DB = sl.jLoad('API_SECRET_DB')

###########
# Functions
###########
####################
# From CryptoAlerter
####################
# Get current time
def getCurrentTimeCondensed():
  return datetime.datetime.today().strftime('%H:%M:%S')

def process(config,smartBasisDict,color,funding,funding2=None):
  tmp=config.split('_')
  prefix=tmp[0].lower()+tmp[1]
  smartBasisBps = smartBasisDict[prefix+'SmartBasis'] * 10000
  basisBps = smartBasisDict[prefix + 'Basis'] * 10000
  z=tmp[0]+': ' + str(round(smartBasisBps)) + '/' +str(round(basisBps)) +'bps('+str(round(funding*100))
  if funding2 is None:
    n=19
  else:
    z=z+'/'+str(round(funding2*100))
    n=23
  z+=')'
  print(termcolor.colored(z.ljust(n), color), end='')

##############################################################

################
# From CryptoLib
################
def dbCCXTInit():
  return  ccxt.deribit({'apiKey': API_KEY_DB, 'secret': API_SECRET_DB, 'enableRateLimit': True})

@retry(wait_fixed=1000)
def dbGetEstFunding(db,ccy,mins=15):
  now=datetime.datetime.now()
  start_timestamp = int(datetime.datetime.timestamp(now - pd.DateOffset(minutes=mins)))*1000
  end_timestamp = int(datetime.datetime.timestamp(now))*1000
  return float(db.public_get_get_funding_rate_value({'instrument_name': ccy+'-PERPETUAL', 'start_timestamp': start_timestamp, 'end_timestamp': end_timestamp})['result'])*(60/mins)*24*365

########################
# Smart basis models mod
########################
def getFundingDictMod(ftx,db):
  def getMarginal(ftxWallet,borrowS,lendingS,ccy):
    if ftxWallet.loc[ccy, 'total'] >= 0:
      return lendingS[ccy]
    else:
      return borrowS[ccy]
  #####
  ftxWallet = cl.ftxGetWallet(ftx)
  borrowS = cl.ftxGetEstBorrow(ftx)
  lendingS = cl.ftxGetEstLending(ftx)
  d=dict()
  d['ftxEstBorrowUSD'] = borrowS['USD']
  d['ftxEstLendingUSD'] = lendingS['USD']
  d['ftxEstMarginalUSD'] = getMarginal(ftxWallet,borrowS,lendingS,'USD')
  d['ftxEstLendingBTC']=  lendingS['BTC']
  d['ftxEstLendingETH']=  lendingS['ETH']
  d['ftxEstSpot']=d['ftxEstMarginalUSD']-(d['ftxEstLendingBTC']+d['ftxEstLendingETH'])/2
  d['dbEstFundingBTC'] = dbGetEstFunding(db, 'BTC')
  d['dbEstFundingETH'] = dbGetEstFunding(db, 'ETH')
  return d

#############################################################################################

@retry(wait_fixed=1000)
def dbGetOneDayShortFutEdge(fundingDict, ccy, basis):
  edge = basis - cl.getOneDayDecayedValues(basis, cl.BASE_BASIS, cl.HALF_LIFE_HOURS_BASIS)[-1] # basis
  edge += cl.getOneDayDecayedMean(fundingDict['dbEstFunding' + ccy], cl.BASE_FUNDING_RATE, cl.HALF_LIFE_HOURS_FUNDING) / 365 # funding
  return edge

#############################################################################################

def getSmartBasisDictMod(ftx, db, fundingDict):
  @retry(wait_fixed=1000)
  def ftxGetMarkets(ftx):
      return pd.DataFrame(ftx.public_get_markets()['result']).set_index('name')
  #####
  def ftxGetMid(ftxMarkets, name):
    return (float(ftxMarkets.loc[name,'bid']) + float(ftxMarkets.loc[name,'ask'])) / 2
  #####
  @retry(wait_fixed=1000)
  def dbGetMid(db,ccy):
    d=db.public_get_ticker({'instrument_name': ccy+'-PERPETUAL'})['result']
    return (float(d['best_bid_price'])+float(d['best_ask_price']))/2
  #####
  oneDayShortSpotEdge = cl.getOneDayShortSpotEdge(fundingDict)
  ftxMarkets = ftxGetMarkets(ftx)
  spotBTC = ftxGetMid(ftxMarkets, 'BTC/USD')
  spotETH = ftxGetMid(ftxMarkets, 'ETH/USD')
  dbBTCAdj=0
  dbETHAdj=0
  #####
  d = dict()
  d['dbBTCBasis'] = dbGetMid(db, 'BTC') / spotBTC - 1
  d['dbETHBasis'] = dbGetMid(db, 'ETH') / spotETH - 1
  d['dbBTCSmartBasis'] = dbGetOneDayShortFutEdge(fundingDict, 'BTC', d['dbBTCBasis']) - oneDayShortSpotEdge + dbBTCAdj
  d['dbETHSmartBasis'] = dbGetOneDayShortFutEdge(fundingDict, 'ETH', d['dbETHBasis']) - oneDayShortSpotEdge + dbETHAdj
  return d

##############################################################

######
# Main
######
cl.printHeader('DeribitAlerter')

ftx=cl.ftxCCXTInit()
db=dbCCXTInit()

while True:
  fundingDict = getFundingDictMod(ftx,db)
  smartBasisDict = getSmartBasisDictMod(ftx, db, fundingDict)
  print(getCurrentTimeCondensed().ljust(10),end='')
  process('DB_BTC', smartBasisDict, 'blue', fundingDict['dbEstFundingBTC'])
  process('DB_ETH', smartBasisDict, 'magenta', fundingDict['dbEstFundingETH'])
  print()
  time.sleep(cl.CT_SLEEP)
