import time
import sys

try:
    try:
        from PySide import QtCore  # @UnresolvedImport
    except:
        try:
            from PySide2 import QtCore  # @UnresolvedImport
        except:
            from PySide6 import QtCore  # @UnresolvedImport
except:
    try:
        from PyQt4 import QtCore # @UnresolvedImport
    except:
        try:
            from PyQt5 import QtCore # @UnresolvedImport
        except:
            from PyQt6 import QtCore  # @UnresolvedImport

# Subclassing QThread
# http://doc.qt.nokia.com/latest/qthread.html
class AThread(QtCore.QThread):

    def run(self):
        count = 0
        while count < 5:
            print("Increasing", count)  # break here
            sys.stdout.flush()
            count += 1

app = QtCore.QCoreApplication([])
thread = AThread()
thread.finished.connect(app.exit)
thread.start()
# Qt6: exec_ is deprecated/removed
if hasattr(app, 'exec'):
    app.exec()
else:
    app.exec_()
print('TEST SUCEEDED!')
