import CryptoLib as cl
import pandas as pd
import requests

########
# Params
########
NETWORKS = ['ETH','MATIC']
ADDRESS = '' # Put your wallet address here

###########
# Functions
###########
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
    df=df.append(df2[['network','qty','spot','usdValue']])
  return df

def dbGetStakedNAV():
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
      coin_1 = supply[0]['optimized_symbol']
      coin_1_qty = supply[0]['amount']
      coin_2 = supply[1]['optimized_symbol']
      coin_2_qty = supply[1]['amount']
      reward = stake['detail']['reward_token_list'][0]
      reward_symbol = reward['optimized_symbol']
      reward_qty = reward['amount']
      reward_usd = reward_qty * reward['price']
      print(f'{coin_1}({coin_1_qty:,.0f})/{coin_2}({coin_2_qty:,.0f})     Reward: {reward_qty:.1f} {reward_symbol} (${reward_usd:.0f})     APR: {APR:.0%}')

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
df=dbGetWalletDf()
print(df)
print()

walletNAV=df['usdValue'].sum()
stakedNAV=dbGetStakedNAV()
print('Wallet NAV: $'+str(round(walletNAV)))
print('Staked NAV: $'+str(round(stakedNAV)))
print('Total NAV:  $'+str(round(walletNAV+stakedNAV)))
print()

dbPrintProjects()