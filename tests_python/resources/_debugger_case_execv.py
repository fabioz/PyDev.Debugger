import sys, os
import threading

print("break here")
if len(sys.argv) == 1:
    os.execv(sys.executable, [sys.executable] + sys.argv + ["1"])

if len(sys.argv) == 2:
    print("TEST SUCEEDED")

