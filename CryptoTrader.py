import CryptoLib as cl

########
# Params
########
isActivated=True      # Turn on at your own risk!
config='FTX_BTC'      # Chosen config in CryptoLib

######
# Main
######
if isActivated:
  cl.cryptoTraderRun(config)
