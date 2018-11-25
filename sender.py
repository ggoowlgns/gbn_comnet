import logging
import sys
from gbn import GBNsend
# from hong.gbn import GBNsend  # Comment out to use hong's

# Replace the level INFO with DEBUG for debugging or
# with WARNING to suppress log messages
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)-15s %(message)s')

def textlines(lines):
    for i in range(lines):
        yield '%05d abcdefghijklmnopqrstuvwxyz\n' % i

def app_sender(gs):
    print('app sender started')
    # infile = open('input.txt')
    # for line in infile:
    for line in textlines(16):
        gs.send(line.encode('utf-8'))
    gs.close()
    print('app sender terminated')

gbnsend = GBNsend('localhost')
gbnsend.start()
app_sender(gbnsend)
gbnsend.join()