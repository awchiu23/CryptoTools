import CryptoLib as cl
import pandas as pd

###########
# Functions
###########
def ftxPrintFundingRate(ftx,ccy):
  df=pd.DataFrame(ftx.private_get_funding_payments({'limit':1000,'future':ccy+'-PERP'})['result']).set_index('time').sort_index()
  print ('Average '+ccy+' funding rate since '+str(df.index[0][:10])+': '+str(round(df['rate'].mean()*24*365*100))+'%')

######
# Init
######
cl.printHeader('CryptoStats')
ftx=cl.ftxCCXTInit()
bn = cl.bnCCXTInit()
bb = cl.bbCCXTInit()

df=pd.DataFrame(ftx.private_get_spot_margin_borrow_history({'limit':1000})['result']).set_index('time').sort_index()
print ('Average USD borrow rate since '+str(df.index[0][:10])+': '+str(round(df['rate'].mean()*24*365*100))+'%')


ftxPrintFundingRate(ftx,'BTC')
ftxPrintFundingRate(ftx,'ETH')
ftxPrintFundingRate(ftx,'FTT')
