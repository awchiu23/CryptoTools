import CryptoLib as cl
from CryptoParams import *

########
# Params
########
ccy='MATIC'
color='green'

SHARED_CCY_DICT[ccy] = {'futExch': ['ftx']}

######
# Main
######
cl.caRun(ccy,color)
