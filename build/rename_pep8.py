import re
_CAMEL_RE = re.compile(r'(?<=[a-z])([A-Z])')

def _normalize(name):
    return _CAMEL_RE.sub(lambda x: '_' + x.group(1).lower(), name).lower()

def main():
    import os

    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(__file__))):
        for filename in files:
            if filename.endswith('.py') and filename != 'rename_pep8.py':
                path = os.path.join(root, filename)
                with open(path, 'rb') as stream:
                    initial_contents = stream.read()
                for key, val in name_to_new_val.iteritems():
                    contents = re.sub(key, val, initial_contents)

                if contents != initial_contents:
                    if re.findall(r'\b%s\b' % (val,), initial_contents):
                        raise AssertionError('Error in:\n%s\n%s is already being used (and changes may conflict).' % (path, val,))
                    
                with open(path, 'wb') as stream:
                    stream.write(contents)


_NAMES = '''
sendCaughtExceptionStack
sendBreakpointConditionException
setSuspend
processThreadNotAlive
sendCaughtExceptionStackProceeded
doWaitSuspend
SetTraceForFrameAndParents
prepareToRun
processCommandLine
initStdoutRedirect
initStderrRedirect
OnRun
doKillPydevThread
stopTrace
handleExcept
processCommand
processNetCommand
addCommand
StartClient


getNextSeq
makeMessage
StartServer

threadToXML
makeErrorMessage


makeThreadCreatedMessage
makeCustomFrameCreatedMessage
makeListThreadsMessage
makeVariableChangedMessage
makeIoMessage    


makeVersionMessage
makeThreadKilledMessage
makeThreadSuspendStr
makeValidXmlValue
makeThreadSuspendMessage
makeThreadRunMessage
makeGetVariableMessage
makeGetArrayMessage
makeGetFrameMessage
makeEvaluateExpressionMessage
makeGetCompletionsMessage
makeGetFileContents
makeSendBreakpointExceptionMessage
makeSendCurrExceptionTraceMessage
makeSendCurrExceptionTraceProceededMessage
makeSendConsoleMessage
makeCustomOperationMessage
makeLoadSourceMessage
makeShowConsoleMessage


makeExitMessage
canBeExecutedBy
doIt
additionalInfo
cmdFactory
GetExceptionTracebackStr
_GetStackStr
_InternalSetTrace
ReplaceSysSetTraceFunc
RestoreSysSetTraceFunc
'''
name_to_new_val = {}
for n in _NAMES.splitlines():
    n = n.strip()
    if not n.startswith('#') and n:
        name_to_new_val[r'\b'+n+r'\b'] = _normalize(n)

if __name__ == '__main__':
    main()

