from threading import *


try:
    from gevent import monkey
    saved = monkey.saved['threading']
    for key, val in saved.items():
        globals()[key] = val
except:
    pass
