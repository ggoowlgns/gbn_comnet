import logging
import time, sys
from gbn import GBNrecv
# from hong.gbn import GBNrecv # Comment out to use hong's

# Replace the level INFO with DEBUG for debugging or
# with WARNING to suppress log messages
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)-15s %(message)s')

def app_receiver(gr):

    print('app receiver started')
    while True:
        data = gr.recv()
        if data == b'':
            break
        print(data.decode('utf-8'), end='')

gbnrecv = GBNrecv('localhost')
gbnrecv.start()
app_receiver(gbnrecv)
gbnrecv.join()