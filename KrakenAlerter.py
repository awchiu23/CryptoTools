import CryptoLib as cl
import time
import termcolor

######
# Main
######
cl.printHeader('KrakenAlerter')
ftx=cl.ftxCCXTInit()
kr=cl.krCCXTInit()
while True:
  spotBTC = cl.ftxGetMid(ftx, 'BTC/USD')
  spot_xxbtzusd = float(kr.public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
  basisUSD=spot_xxbtzusd/spotBTC-1
  z='XXBTZUSD:'+str(round(basisUSD*10000))
  print(cl.getCurrentTime().ljust(30)+termcolor.colored(z.ljust(25),'blue'))
  time.sleep(3)