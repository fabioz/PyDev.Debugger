def jython_execfile(argv):
    import org.python.util.PythonInterpreter as PythonInterpreter  # @UnresolvedImport
    interpreter = PythonInterpreter()
    state = interpreter.getSystemState()
    state.argv = argv
    interpreter.execfile(argv[0])