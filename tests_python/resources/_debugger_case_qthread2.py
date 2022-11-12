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

# Subclassing QObject and using moveToThread
# http://labs.qt.nokia.com/2007/07/05/qthreads-no-longer-abstract/
class SomeObject(QtCore.QObject):

    try:
        finished = QtCore.Signal()  # @UndefinedVariable
    except:
        finished = QtCore.pyqtSignal()  # @UndefinedVariable

    def long_running(self):
        count = 0
        while count < 5:
            print("Increasing")  # break here
            count += 1
        self.finished.emit()

app = QtCore.QCoreApplication([])
objThread = QtCore.QThread()
obj = SomeObject()
obj.moveToThread(objThread)
obj.finished.connect(objThread.quit)
objThread.started.connect(obj.long_running)
objThread.finished.connect(app.exit)
objThread.start()
# Qt6: exec_ is deprecated/removed
if hasattr(app, 'exec'):
    app.exec()
else:
    app.exec_()
print('TEST SUCEEDED!')
