import CryptoLib as cl
import termcolor
import time

########
# Params
########
ccys = ['BTC','ETH','XRP','DOGE','MATIC']
colors = ['blue','red','green','cyan','cyan']
interval = 60*5

######
# Main
######
cl.printHeader('BORROWa')
ftx=cl.ftxCCXTInit()
while True:
  borrowS = cl.ftxGetEstBorrow(ftx)
  print(cl.getCurrentTime(isCondensed=True).ljust(15),end='')
  for i in range(len(ccys)):
    ccy=ccys[i]
    color=colors[i]
    borrow=borrowS[ccy]
    z = ccy + ':' + str(round(borrow * 100,1))+'%'
    print(termcolor.colored(z.ljust(15), color), end='')
  time.sleep(interval)
  print()
