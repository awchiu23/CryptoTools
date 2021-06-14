import CryptoLib as cl
import pandas as pd
import requests
import termcolor
import sys

########
# Params
########
ADDRESS = '' # Put your wallet address here
NETWORKS = ['ETH','MATIC']

###########
# Functions
###########
def colored(text, color):
  if '--nocolor' in sys.argv:
    return text
  else:
    return termcolor.colored(text,color)

def dbRefresh():
  url = 'https://api2.debank.com/mp?url=https://debank.com/profile/' + ADDRESS
  headers = {'User-Agent': 'Mozilla/5.0'}
  requests.get(url, headers=headers)

def dbGetWalletDf():
  df=pd.DataFrame()
  for network in NETWORKS:
    url = 'https://api.debank.com/token/balance_list?chain=' + network + '&is_all=true&user_addr=' + ADDRESS
    headers = {'User-Agent': 'Mozilla/5.0'}
    df2=pd.DataFrame(requests.get(url, headers=headers).json()['data']).set_index('optimized_symbol')
    df2['network'] = network
    df2['qty'] = df2['balance'] / (10 ** df2['decimals'])
    df2['spot'] = df2['price']
    df2['usdValue'] = df2['qty']*df2['spot']
    df=df.append(df2[['network','qty','spot','usdValue']]).sort_values('usdValue',ascending=False)
  return df

def dbGetProjectsNAV():
  url = 'https://api.debank.com/user/addr?addr=' + ADDRESS
  headers = {'User-Agent': 'Mozilla/5.0'}
  return pd.DataFrame(requests.get(url, headers=headers).json()['data']['projects'])['net_usd_value'].sum()

def dbPrintProjects():
  url = 'https://api.debank.com/portfolio/project_list?user_addr=' + ADDRESS
  headers = {'User-Agent': 'Mozilla/5.0'}
  for data in requests.get(url, headers=headers).json()['data']:
    for stake in data['portfolio_list']:
      APR = stake['detail']['daily_farm_rate'] * 365
      supply = stake['detail']['supply_token_list']
      coin1 = supply[0]['optimized_symbol']
      coin2 = supply[1]['optimized_symbol']
      unclaimed = stake['detail']['reward_token_list'][0]
      unclaimedSymbol = unclaimed['optimized_symbol']
      unclaimedUSD = unclaimed['amount'] * unclaimed['price']
      print(f'{coin1}/{coin2}          Unclaimed: {unclaimedSymbol} (${unclaimedUSD:.0f})          APR: {APR:.0%}')

##################################
# Simon's section -- please ignore
##################################
import os
if os.environ.get('USERNAME')=='Simon':
  import SimonLib as sl
  ADDRESS = sl.jLoad('API_ADDRESS_DEBANK')

######
# Main
######
cl.printHeader('DEFIUtil')
dbRefresh()
walletDf=dbGetWalletDf()
walletNAV=walletDf['usdValue'].sum()
stakedNAV=dbGetProjectsNAV()
nav=walletNAV+stakedNAV

print(colored('NAV as of '+cl.getCurrentTime()+': $'+str(round(nav))+' (Wallet: $'+str(round(walletNAV/1000))+'K / Projects: $'+str(round(stakedNAV/1000))+'K)','blue'))

cl.printHeader('Wallet')
print(walletDf)

cl.printHeader('Projects')
dbPrintProjects()