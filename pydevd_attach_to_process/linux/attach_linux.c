//compile with: gcc -shared -o attach_linux.so -fPIC -nostartfiles attach_linux.c

#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <stdbool.h>
#include "python.h"

// Exported function: hello(): Just to print something and check that we've been
// able to connect.
extern int hello(void);

int hello()
{
    printf("Hello world!\n");
    void *hndl = dlsym (NULL, "PyGILState_Ensure");
    if(hndl == NULL){
        printf("NULL\n");

    }else{
        printf("Worked (found PyGILState_Ensure)!\n");

    }
    printf("%d", GetPythonVersion());


    return 2;
}


// This is the function which enables us to set the sys.settrace for all the threads
// which are already running.
// isDebug is pretty important! Must be true on python debug builds (python_d)
// If this value is passed wrongly the program will crash.
extern int SetSysTraceFunc(bool showDebugInfo, bool isDebug);

// Internal function to keep on the tracing
int _PYDEVD_ExecWithGILSetSysStrace(bool showDebugInfo, bool isDebug);

// Implementation details below
typedef int (*Py_IsInitialized) ();
typedef PyInterpreterState* (*PyInterpreterState_Head)();
typedef enum { PyGILState_LOCKED, PyGILState_UNLOCKED } PyGILState_STATE;
typedef PyGILState_STATE(*PyGILState_Ensure)();
typedef void (*PyGILState_Release)(PyGILState_STATE);
typedef PyObject* (*PyBool_FromLong)(long v);
typedef PyObject* (*PyImport_ImportModule) (const char *name);
typedef PyObject* (*PyObject_HasAttrString)(PyObject *o, const char *attr_name);
typedef PyObject* (*PyObject_GetAttrString)(PyObject *o, const char *attr_name);
typedef PyObject* (*PyObject_CallFunctionObjArgs)(PyObject *callable, ...);    // call w/ varargs, last arg should be NULL


// Helper so that we get a PyObject where we can access its fields (in debug or release).
PyObject* GetPyObjectPointerNoDebugInfo(bool isDebug, PyObject* object) {
    if (object != NULL && isDebug) {
        // debug builds have 2 extra pointers at the front that we don't care about
        return (PyObject*)((size_t*)object + 2);
    }
    return object;
}

// Helper so that we get a PyObject where we can access its fields (in debug or release).
PyTypeObject * GetPyObjectPointerNoDebugInfo2(bool isDebug, PyTypeObject * object) {
    if (object != NULL && isDebug) {
        // debug builds have 2 extra pointers at the front that we don't care about
        return (PyTypeObject *)((size_t*)object + 2);
    }
    return object;
}

// Helper which will decrement the reference count of an object and dealloc it if
// it's not there.
 void DecRef(PyObject* object, bool isDebug) {
     PyObject* noDebug = GetPyObjectPointerNoDebugInfo(isDebug, object);

     if (noDebug != NULL && --noDebug->ob_refcnt == 0) {
        PyTypeObject *temp = GetPyObjectPointerNoDebugInfo2(isDebug, noDebug->ob_type);
        temp->tp_dealloc(object);
     }
 }

// Helper to increment the reference count to some object.
void IncRef(PyObject* object, bool isDebug) {
     PyObject* noDebug = GetPyObjectPointerNoDebugInfo(isDebug, object);

     if (noDebug != NULL){
        noDebug->ob_refcnt++;
    }
}

class PyObjectHolder {
private:
    PyObject* _object;
    bool _isDebug;
public:
    PyObjectHolder(bool isDebug, PyObject *object) {
        _object = object;
        _isDebug = isDebug;
    };

    PyObject* ToPython() {
        return _object;
    }

    ~PyObjectHolder() {
        if(_object != NULL){
            DecRef(_object, _isDebug);
        }
    }
};


# define CHECK_NULL(ptr, msg, returnVal) if(ptr == NULL){if(showDebugInfo){printf(msg);} return returnVal;}

int DoAttach(bool isDebug, const char *command, bool showDebugInfo)
{
    Py_IsInitialized isInitFunc;
    *(void**)(&isInitFunc) = dlsym(0, "Py_IsInitialized");
    CHECK_NULL(isInitFunc, "Py_IsInitialized not found.\n", 1);

    if(!isInitFunc()){
        if(showDebugInfo){
            printf("Py_IsInitialized returned false.\n");
        }
        return 2;
    }

    PythonVersion version = GetPythonVersion();

    PyInterpreterState_Head interpHeadFunc;
    *(void**)(&interpHeadFunc) = dlsym(0, "PyInterpreterState_Head");
    CHECK_NULL(interpHeadFunc, "PyInterpreterState_Head not found.\n", 3);

    PyInterpreterState* head = interpHeadFunc();
    CHECK_NULL(head, "Interpreter not initialized.\n", 4);

    bool threadSafeAddPendingCall = false;

    // check that we're a supported version
    if (version == PythonVersion_Unknown) {
        if(showDebugInfo){
            printf("Python version unknown!\n");
        }
        return 5;
    } else if (version >= PythonVersion_27 && version != PythonVersion_30) {
        threadSafeAddPendingCall = true;
    }

    printf("\n\n\n%s\n\n\n", command);

}


int SetSysTraceFunc(bool showDebugInfo, bool isDebug)
{
    if(showDebugInfo){
        printf("SetSysTraceFunc started.\n");
    }
    Py_IsInitialized isInitFunc;
    *(void**)(&isInitFunc) = dlsym(0, "Py_IsInitialized");
    CHECK_NULL(isInitFunc, "Py_IsInitialized not found.\n", 1);

    if(!isInitFunc()){
        if(showDebugInfo){
            printf("Py_IsInitialized returned false.\n");
        }
        return 2;
    }

    PythonVersion version = GetPythonVersion();

    PyInterpreterState_Head interpHeadFunc;
    *(void**)(&interpHeadFunc) = dlsym(0, "PyInterpreterState_Head");
    CHECK_NULL(interpHeadFunc, "PyInterpreterState_Head not found.\n", 3);

    PyInterpreterState* head = interpHeadFunc();
    CHECK_NULL(head, "Interpreter not initialized.\n", 4);

    PyGILState_Ensure pyGilStateEnsureFunc;
    *(void**)(&pyGilStateEnsureFunc) = dlsym(0, "PyGILState_Ensure");
    CHECK_NULL(pyGilStateEnsureFunc, "PyGILState_Ensure not found.\n", 5);

    PyGILState_Release pyGilStateReleaseFunc;
    *(void**)(&pyGilStateReleaseFunc) = dlsym(0, "PyGILState_Release");
    CHECK_NULL(pyGilStateReleaseFunc, "PyGILState_Release not found.\n", 6);

    PyGILState_STATE pyGILState = pyGilStateEnsureFunc();
    int ret = _PYDEVD_ExecWithGILSetSysStrace(showDebugInfo, isDebug);
    //No matter what happens we have to release it.
    pyGilStateReleaseFunc(pyGILState);
    return ret;
}


int _PYDEVD_ExecWithGILSetSysStrace(bool showDebugInfo, bool isDebug){
    PyBool_FromLong boolFromLongFunc;
    *(void**)(&boolFromLongFunc) = dlsym(0, "PyBool_FromLong");
    CHECK_NULL(boolFromLongFunc, "PyBool_FromLong not found.\n", 7);

    PyObject_HasAttrString pyHasAttrFunc;
    *(void**)(&pyHasAttrFunc) = dlsym(0, "PyObject_HasAttrString");
    CHECK_NULL(pyHasAttrFunc, "PyObject_HasAttrString not found.\n", 7);

    auto PyObjectHolder pyTrue = PyObjectHolder(isDebug, boolFromLongFunc(1));
    auto PyObjectHolder pyFalse = PyObjectHolder(isDebug, boolFromLongFunc(0));

    PyImport_ImportModule pyImportModFunc;
    *(void**)(&pyImportModFunc) = dlsym(0, "PyImport_ImportModule");
    CHECK_NULL(pyImportModFunc, "PyImport_ImportModule not found.\n", 8);

    auto PyObjectHolder pydevdTracingMod = PyObjectHolder(isDebug, pyImportModFunc("pydevd_tracing"));
    CHECK_NULL(pydevdTracingMod.ToPython(), "pydevd_tracing module null.\n", 9);

    if(!pyHasAttrFunc(pydevdTracingMod.ToPython(), "_original_settrace")){
        if(showDebugInfo){
            printf("pydevd_tracing module has no _original_settrace! ");
        }
        return 8;
    }


    auto PyObjectHolder pydevdMod = PyObjectHolder(isDebug, pyImportModFunc("pydevd"));
    CHECK_NULL(pydevdMod.ToPython(), "pydevd module null.\n", 10);

    PyObject_GetAttrString pyGetAttr;
    *(void**)(&pyGetAttr) = dlsym(0, "PyObject_GetAttrString");
    CHECK_NULL(pyGetAttr, "PyObject_GetAttrString not found.\n", 8);

    auto PyObjectHolder getGlobalDebugger = PyObjectHolder(isDebug, pyGetAttr(pydevdMod.ToPython(), "GetGlobalDebugger"));
    CHECK_NULL(getGlobalDebugger.ToPython(), "pydevd.GetGlobalDebugger null.\n", 11);

    PyObject_CallFunctionObjArgs call;
    *(void**)(&call) = dlsym(0, "PyObject_CallFunctionObjArgs");
    CHECK_NULL(call, "PyObject_CallFunctionObjArgs not found.\n", 11);

    auto PyObjectHolder globalDbg = PyObjectHolder(isDebug, call(getGlobalDebugger.ToPython(), NULL));
    CHECK_NULL(globalDbg.ToPython(), "pydevd.GetGlobalDebugger() returned null.\n", 12);

    if(!pyHasAttrFunc(globalDbg.ToPython(), "trace_dispatch")){
        if(showDebugInfo){
            printf("pydevd.GetGlobalDebugger() has no attribute trace_dispatch!\n");
        }
        return 13;
    }

    return 0;
}
