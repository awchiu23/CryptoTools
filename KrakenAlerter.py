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
  spotEUR = cl.ftxGetMid(ftx, 'EUR/USD')
  spot_xxbtzusd = float(kr.public_get_ticker({'pair': 'XXBTZUSD'})['result']['XXBTZUSD']['c'][0])
  spot_xxbtzeur = float(kr.public_get_ticker({'pair': 'XXBTZEUR'})['result']['XXBTZEUR']['c'][0])
  basisUSD=spot_xxbtzusd/spotBTC-1
  basisEUR=spot_xxbtzeur*spotEUR/spotBTC-1
  z='XXBTZUSD:'+str(round(basisUSD*10000))
  z2='XXBTZEUR: '+str(round(basisEUR*10000))+' (f/x='+str(round(spotEUR,4))+')'
  print(cl.getCurrentTime().ljust(30)+termcolor.colored(z.ljust(25),'blue')+termcolor.colored(z2,'magenta'))
  time.sleep(3)