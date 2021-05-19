import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='MATIC'
color='cyan'

SHARED_CCY_DICT[ccy] = {'futExch': ['ftx']}

######
# Main
######
cl.caRun(ccy,color)
