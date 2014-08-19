from threading import enumerate, currentThread, Condition, Event, Timer, settrace, Thread

try:
    from gevent import monkey
    saved = monkey.saved['threading']
    for key, val in saved.items():
        globals()[key] = val
except:
    pass
