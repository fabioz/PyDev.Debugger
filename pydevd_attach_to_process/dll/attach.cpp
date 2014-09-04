/* ****************************************************************************
*
* Copyright (c) Microsoft Corporation.
*
* This source code is subject to terms and conditions of the Apache License, Version 2.0. A
* copy of the license can be found in the License.html file at the root of this distribution. If
* you cannot locate the Apache License, Version 2.0, please send an email to
* vspython@microsoft.com. By using this source code in any fashion, you are agreeing to be bound
* by the terms of the Apache License, Version 2.0.
*
* You must not remove this notice, or any other, from this software.
*
* Contributor: Fabio Zadrozny
*
* Based on PyDebugAttach.cpp from PVTS. Windows only.
* Initially we did an attach completely based on shellcode which got the
* GIL called PyRun_SimpleString with the needed code and was done with it
* (so, none of this code was needed).
* Now, newer version of Python don't initialize threading by default, so,
* most of this code is done only to overcome this limitation (and as a plus,
* if there's no code running, we also pause the threads to make our code run).
*
* On Linux the approach is still the simpler one (using gdb), so, on newer
* versions of Python it may not work unless the user has some code running
* and threads are initialized.
* I.e.:
*
* The user may have to add the code below in the start of its script for
* a successful attach (if he doesn't already use threads).
*
* from threading import Thread
* Thread(target=str).start()
*
* -- this is the workaround for the fact that we can't get the gil
* if there aren't any threads (PyGILState_Ensure gives an error).
* ***************************************************************************/



// Access to std::cout and std::endl
#include <iostream>

// DECLDIR will perform an export for us
#define DLL_EXPORT

#include "attach.h"
#include "stdafx.h"
#include "python.h"

#pragma comment(lib, "kernel32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "advapi32.lib")
#pragma comment(lib, "psapi.lib")

using namespace std;

typedef int (Py_IsInitialized)();
typedef void (PyEval_Lock)(); // Acquire/Release lock
typedef void (PyThreadState_API)(PyThreadState *); // Acquire/Release lock
typedef PyInterpreterState* (PyInterpreterState_Head)();
typedef PyThreadState* (PyInterpreterState_ThreadHead)(PyInterpreterState* interp);
typedef PyThreadState* (PyThreadState_Next)(PyThreadState *tstate);
typedef PyThreadState* (PyThreadState_Swap)(PyThreadState *tstate);
typedef int (PyRun_SimpleString)(const char *command);
typedef PyObject* (PyDict_New)();
typedef PyObject* (PyModule_New)(const char *name);
typedef PyObject* (PyModule_GetDict)(PyObject *module);
typedef PyObject* (Py_CompileString)(const char *str, const char *filename, int start);
typedef PyObject* (PyEval_EvalCode)(PyObject *co, PyObject *globals, PyObject *locals);
typedef PyObject* (PyDict_GetItemString)(PyObject *p, const char *key);
typedef PyObject* (PyObject_CallFunctionObjArgs)(PyObject *callable, ...);    // call w/ varargs, last arg should be NULL
typedef void (PyErr_Fetch)(PyObject **, PyObject **, PyObject **);
typedef PyObject* (PyEval_GetBuiltins)();
typedef int (PyDict_SetItemString)(PyObject *dp, const char *key, PyObject *item);
typedef int (PyEval_ThreadsInitialized)();
typedef void (Py_AddPendingCall)(int (*func)(void *), void*);
typedef PyObject* (PyInt_FromLong)(long);
typedef PyObject* (PyString_FromString)(const char* s);
typedef void PyEval_SetTrace(Py_tracefunc func, PyObject *obj);
typedef void (PyErr_Restore)(PyObject *type, PyObject *value, PyObject *traceback);
typedef void (PyErr_Fetch)(PyObject **ptype, PyObject **pvalue, PyObject **ptraceback);
typedef PyObject* (PyErr_Occurred)();
typedef PyObject* (PyErr_Print)();
typedef PyObject* (PyImport_ImportModule) (const char *name);
typedef PyObject* (PyObject_GetAttrString)(PyObject *o, const char *attr_name);
typedef PyObject* (PyObject_SetAttrString)(PyObject *o, const char *attr_name, PyObject* value);
typedef PyObject* (PyBool_FromLong)(long v);
typedef enum { PyGILState_LOCKED, PyGILState_UNLOCKED } PyGILState_STATE;
typedef PyGILState_STATE(PyGILState_Ensure)();
typedef void (PyGILState_Release)(PyGILState_STATE);
typedef unsigned long (_PyEval_GetSwitchInterval)(void);
typedef void (_PyEval_SetSwitchInterval)(unsigned long microseconds);
typedef void* (PyThread_get_key_value)(int);
typedef int (PyThread_set_key_value)(int, void*);
typedef void (PyThread_delete_key_value)(int);
typedef PyGILState_STATE PyGILState_EnsureFunc(void);
typedef void PyGILState_ReleaseFunc(PyGILState_STATE);
typedef PyObject* PyInt_FromSize_t(size_t ival);
typedef PyThreadState *PyThreadState_NewFunc(PyInterpreterState *interp);


// holder to ensure we release the GIL even in error conditions
class GilHolder {
    PyGILState_STATE _gilState;
    PyGILState_Release* _release;
public:
    GilHolder(PyGILState_Ensure* acquire, PyGILState_Release* release) {
        _gilState = acquire();
        _release = release;
    }

    ~GilHolder() {
        _release(_gilState);
    }
};

// create a custom heap for our unordered map.  This is necessary because if we suspend a thread while in a heap function
// then we could deadlock here.  We need to be VERY careful about what we do while the threads are suspended.
static HANDLE g_heap = 0;

template<typename T>
class PrivateHeapAllocator {
public:
    typedef size_t    size_type;
    typedef ptrdiff_t difference_type;
    typedef T*        pointer;
    typedef const T*  const_pointer;
    typedef T&        reference;
    typedef const T&  const_reference;
    typedef T         value_type;

    template<class U>
    struct rebind {
        typedef PrivateHeapAllocator<U> other;
    };

    explicit PrivateHeapAllocator() {}

    PrivateHeapAllocator(PrivateHeapAllocator const&) {}

    ~PrivateHeapAllocator() {}

    template<typename U>
    PrivateHeapAllocator(PrivateHeapAllocator<U> const&) {}

    pointer allocate(size_type size, allocator<void>::const_pointer hint = 0) {
        if (g_heap == nullptr) {
            g_heap = HeapCreate(0, 0, 0);
        }
        auto mem = HeapAlloc(g_heap, 0, size * sizeof(T));
        return static_cast<pointer>(mem);
    }

    void deallocate(pointer p, size_type n) {
        HeapFree(g_heap, 0, p);
    }

    size_type max_size() const {
        return (std::numeric_limits<size_type>::max)() / sizeof(T);
    }

    void construct(pointer p, const T& t) {
        new(p) T(t);
    }

    void destroy(pointer p) {
        p->~T();
    }
};

HANDLE g_initedEvent;
int AttachCallback(void *initThreads) {
    // initialize us for threading, this will acquire the GIL if not already created, and is a nop if the GIL is created.
    // This leaves us in the proper state when we return back to the runtime whether the GIL was created or not before
    // we were called.
    ((PyEval_Lock*)initThreads)();
    SetEvent(g_initedEvent);
    return 0;
}

// Ensures handles are closed when they go out of scope
class HandleHolder {
    HANDLE _handle;
public:
    HandleHolder(HANDLE handle) : _handle(handle) {
    }

    ~HandleHolder() {
        CloseHandle(_handle);
    }
};

typedef unordered_map<DWORD, HANDLE, std::hash<DWORD>, std::equal_to<DWORD>, PrivateHeapAllocator<pair<DWORD, HANDLE>>> ThreadMap;


// Checks to see if the specified module is likely a Python interpreter.
bool IsPythonModule(HMODULE module, bool &isDebug) {
    wchar_t mod_name[MAX_PATH];
    isDebug = false;
    if (GetModuleBaseName(GetCurrentProcess(), module, mod_name, MAX_PATH)) {
        if (_wcsnicmp(mod_name, L"python", 6) == 0) {
            if (wcslen(mod_name) >= 10 && _wcsnicmp(mod_name + 8, L"_d", 2) == 0) {
                isDebug = true;
            }
            return true;
        }
    }
    return false;
}


void ResumeThreads(ThreadMap &suspendedThreads) {
    for (auto start = suspendedThreads.begin();  start != suspendedThreads.end(); start++) {
        ResumeThread((*start).second);
        CloseHandle((*start).second);
    }
    suspendedThreads.clear();
}

// Suspends all threads ensuring that they are not currently in a call to Py_AddPendingCall.
void SuspendThreads(ThreadMap &suspendedThreads, Py_AddPendingCall* addPendingCall, PyEval_ThreadsInitialized* threadsInited) {
    DWORD curThreadId = GetCurrentThreadId();
    DWORD curProcess = GetCurrentProcessId();
    // suspend all the threads in the process so we can do things safely...
    bool suspended;

    do {
        suspended = false;
        HANDLE h = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        if (h != INVALID_HANDLE_VALUE) {

            THREADENTRY32 te;
            te.dwSize = sizeof(te);
            if (Thread32First(h, &te)) {
                do {
                    if (te.dwSize >= FIELD_OFFSET(THREADENTRY32, th32OwnerProcessID) + sizeof(te.th32OwnerProcessID) && te.th32OwnerProcessID == curProcess) {


                        if (te.th32ThreadID != curThreadId && suspendedThreads.find(te.th32ThreadID) == suspendedThreads.end()) {
                            auto hThread = OpenThread(THREAD_ALL_ACCESS, FALSE, te.th32ThreadID);
                            if (hThread != nullptr) {
                                SuspendThread(hThread);

                                bool addingPendingCall = false;

                                CONTEXT context;
                                memset(&context, 0x00, sizeof(CONTEXT));
                                context.ContextFlags = CONTEXT_ALL;
                                GetThreadContext(hThread, &context);

#if defined(_X86_)
                                if(context.Eip >= *((DWORD*)addPendingCall) && context.Eip <= (*((DWORD*)addPendingCall)) + 0x100) {
                                    addingPendingCall = true;
                                }
#elif defined(_AMD64_)
                                if (context.Rip >= *((DWORD64*)addPendingCall) && context.Rip <= *((DWORD64*)addPendingCall + 0x100)) {
                                    addingPendingCall = true;
                                }
#endif

                                if (addingPendingCall) {
                                    // we appear to be adding a pending call via this thread - wait for this to finish so we can add our own pending call...
                                    ResumeThread(hThread);
                                    SwitchToThread();   // yield to the resumed thread if it's on our CPU...
                                    CloseHandle(hThread);
                                } else {
                                    suspendedThreads[te.th32ThreadID] = hThread;
                                }
                                suspended = true;
                            }
                        }
                    }

                    te.dwSize = sizeof(te);
                } while (Thread32Next(h, &te) && !threadsInited());
            }
            CloseHandle(h);
        }
    } while (suspended && !threadsInited());
}

wstring GetCurrentModuleFilename() {
    HMODULE hModule = NULL;
    if (GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCTSTR)GetCurrentModuleFilename, &hModule) != 0) {
        wchar_t filename[MAX_PATH];
        GetModuleFileName(hModule, filename, MAX_PATH);
        return filename;
    }
    return wstring();
}

extern "C"
{

    /**
     * The returned value signals the error that happened!
     *
     * Return codes:
     * 0 = all OK.
     * 1 = Py_IsInitialized not found
     * 2 = Py_IsInitialized returned false
     * 3 = Missing Python API
     * 4 = Interpreter not initialized
     * 5 = Python version unknown
     * 6 = Connect timeout
     **/
	int DoAttach(HMODULE module, bool isDebug, const char *command )
	{
        auto isInit = (Py_IsInitialized*)GetProcAddress(module, "Py_IsInitialized");

        if (isInit == nullptr) {
            //std::cout << "Py_IsInitialized not found. " << std::endl << std::flush;
            return 1;
        }
        if (!isInit()) {
            //std::cout << "Py_IsInitialized returned false. " << std::endl << std::flush;
            return 2;
        }

        auto version = GetPythonVersion(module);

        // found initialized Python runtime, gather and check the APIs we need for a successful attach...
        auto addPendingCall = (Py_AddPendingCall*)GetProcAddress(module, "Py_AddPendingCall");
        auto curPythonThread = (PyThreadState**)(void*)GetProcAddress(module, "_PyThreadState_Current");
        auto interpHead = (PyInterpreterState_Head*)GetProcAddress(module, "PyInterpreterState_Head");
        auto gilEnsure = (PyGILState_Ensure*)GetProcAddress(module, "PyGILState_Ensure");
        auto gilRelease = (PyGILState_Release*)GetProcAddress(module, "PyGILState_Release");
        auto threadHead = (PyInterpreterState_ThreadHead*)GetProcAddress(module, "PyInterpreterState_ThreadHead");
        auto initThreads = (PyEval_Lock*)GetProcAddress(module, "PyEval_InitThreads");
        auto acquireLock = (PyEval_Lock*)GetProcAddress(module, "PyEval_AcquireLock");
        auto releaseLock = (PyEval_Lock*)GetProcAddress(module, "PyEval_ReleaseLock");
        auto threadsInited = (PyEval_ThreadsInitialized*)GetProcAddress(module, "PyEval_ThreadsInitialized");
        auto threadNext = (PyThreadState_Next*)GetProcAddress(module, "PyThreadState_Next");
        auto threadSwap = (PyThreadState_Swap*)GetProcAddress(module, "PyThreadState_Swap");
        auto pyDictNew = (PyDict_New*)GetProcAddress(module, "PyDict_New");
        auto pyModuleNew = (PyModule_New*)GetProcAddress(module, "PyModule_New");
        auto pyModuleGetDict = (PyModule_GetDict*)GetProcAddress(module, "PyModule_GetDict");
        auto pyCompileString = (Py_CompileString*)GetProcAddress(module, "Py_CompileString");
        auto pyEvalCode = (PyEval_EvalCode*)GetProcAddress(module, "PyEval_EvalCode");
        auto getDictItem = (PyDict_GetItemString*)GetProcAddress(module, "PyDict_GetItemString");
        auto call = (PyObject_CallFunctionObjArgs*)GetProcAddress(module, "PyObject_CallFunctionObjArgs");
        auto getBuiltins = (PyEval_GetBuiltins*)GetProcAddress(module, "PyEval_GetBuiltins");
        auto dictSetItem = (PyDict_SetItemString*)GetProcAddress(module, "PyDict_SetItemString");
        PyInt_FromLong* intFromLong;
        PyString_FromString* strFromString;
        PyInt_FromSize_t* intFromSizeT;
        if (version >= PythonVersion_30) {
            intFromLong = (PyInt_FromLong*)GetProcAddress(module, "PyLong_FromLong");
            intFromSizeT = (PyInt_FromSize_t*)GetProcAddress(module, "PyLong_FromSize_t");
            if (version >= PythonVersion_33) {
                strFromString = (PyString_FromString*)GetProcAddress(module, "PyUnicode_FromString");
            } else {
                strFromString = (PyString_FromString*)GetProcAddress(module, "PyUnicodeUCS2_FromString");
            }
        } else {
            intFromLong = (PyInt_FromLong*)GetProcAddress(module, "PyInt_FromLong");
            strFromString = (PyString_FromString*)GetProcAddress(module, "PyString_FromString");
            intFromSizeT = (PyInt_FromSize_t*)GetProcAddress(module, "PyInt_FromSize_t");
        }
        auto intervalCheck = (int*)GetProcAddress(module, "_Py_CheckInterval");
        auto errOccurred = (PyErr_Occurred*)GetProcAddress(module, "PyErr_Occurred");
        auto pyErrFetch = (PyErr_Fetch*)GetProcAddress(module, "PyErr_Fetch");
        auto pyErrRestore = (PyErr_Restore*)GetProcAddress(module, "PyErr_Restore");
        auto pyErrPrint = (PyErr_Print*)GetProcAddress(module, "PyErr_Print");
        auto pyImportMod = (PyImport_ImportModule*) GetProcAddress(module, "PyImport_ImportModule");
        auto pyGetAttr = (PyObject_GetAttrString*)GetProcAddress(module, "PyObject_GetAttrString");
        auto pySetAttr = (PyObject_SetAttrString*)GetProcAddress(module, "PyObject_SetAttrString");
        auto pyNone = (PyObject*)GetProcAddress(module, "_Py_NoneStruct");
        auto getSwitchInterval = (_PyEval_GetSwitchInterval*)GetProcAddress(module, "_PyEval_GetSwitchInterval");
        auto setSwitchInterval = (_PyEval_SetSwitchInterval*)GetProcAddress(module, "_PyEval_SetSwitchInterval");
        auto boolFromLong = (PyBool_FromLong*)GetProcAddress(module, "PyBool_FromLong");
        auto pyGilStateEnsure = (PyGILState_EnsureFunc*)GetProcAddress(module, "PyGILState_Ensure");
        auto pyGilStateRelease = (PyGILState_ReleaseFunc*)GetProcAddress(module, "PyGILState_Release");
        auto pyRun_SimpleString = (PyRun_SimpleString*)GetProcAddress(module, "PyRun_SimpleString");

        if (addPendingCall == nullptr || curPythonThread == nullptr || interpHead == nullptr || gilEnsure == nullptr || gilRelease == nullptr || threadHead == nullptr ||
            initThreads == nullptr || releaseLock == nullptr || threadsInited == nullptr || threadNext == nullptr || threadSwap == nullptr ||
            pyDictNew == nullptr || pyCompileString == nullptr || pyEvalCode == nullptr || getDictItem == nullptr || call == nullptr ||
            getBuiltins == nullptr || dictSetItem == nullptr || intFromLong == nullptr || pyErrRestore == nullptr || pyErrFetch == nullptr ||
            errOccurred == nullptr || pyImportMod == nullptr || pyGetAttr == nullptr || pyNone == nullptr || pySetAttr == nullptr || boolFromLong == nullptr ||
            releaseLock == nullptr || pyRun_SimpleString == nullptr ||
            pyGilStateEnsure == nullptr || pyGilStateRelease == nullptr) {
                // we're missing some APIs, we cannot attach.
                //std::cout << "Error, missing Python API!! " << std::endl << std::flush;
                return 3;
        }

        auto head = interpHead();
        if (head == nullptr) {
            // this interpreter is loaded but not initialized.
            //std::cout << "Interpreter not initialized! " << std::endl << std::flush;
            return 4;
        }

        bool threadSafeAddPendingCall = false;

        // check that we're a supported version
        if (version == PythonVersion_Unknown) {
            //std::cout << "Python version unknown! " << std::endl << std::flush;
            return 5;
        } else if (version >= PythonVersion_27 && version != PythonVersion_30) {
            threadSafeAddPendingCall = true;
        }






        if (!threadsInited()) {
             int saveIntervalCheck;
             unsigned long saveLongIntervalCheck;
             if (intervalCheck != nullptr) {
                 // not available on 3.2
                 saveIntervalCheck = *intervalCheck;
                 *intervalCheck = -1;    // lower the interval check so pending calls are processed faster
             } else if (getSwitchInterval != nullptr && setSwitchInterval != nullptr) {
                 saveLongIntervalCheck = getSwitchInterval();
                 setSwitchInterval(0);
             }

             //
             // Multiple thread support has not been initialized in the interpreter.   We need multi threading support
             // to block any actively running threads and setup the debugger attach state.
             //
             // We need to initialize multiple threading support but we need to do so safely.  One option is to call
             // Py_AddPendingCall and have our callback then initialize multi threading.  This is completely safe on 2.7
             // and up.  Unfortunately that doesn't work if we're not actively running code on the main thread (blocked on a lock
             // or reading input).  It's also not thread safe pre-2.7 so we need to make sure it's safe to call on down-level
             // interpreters.
             //
             // Another option is to make sure no code is running - if there is no active thread then we can safely call
             // PyEval_InitThreads and we're in business.  But to know this is safe we need to first suspend all the other
             // threads in the process and then inspect if any code is running.
             //
             // Finally if code is running after we've suspended the threads then we can go ahead and do Py_AddPendingCall
             // on down-level interpreters as long as we're sure no one else is making a call to Py_AddPendingCall at the same
             // time.
             //
             // Therefore our strategy becomes: Make the Py_AddPendingCall on interpreters where it's thread safe.  Then suspend
             // all threads - if a threads IP is in Py_AddPendingCall resume and try again.  Once we've got all of the threads
             // stopped and not in Py_AddPendingCall (which calls no functions its self, you can see this and it's size in the
             // debugger) then see if we have a current thread.   If not go ahead and initialize multiple threading (it's now safe,
             // no Python code is running).  Otherwise add the pending call and repeat.  If at any point during this process
             // threading becomes initialized (due to our pending call or the Python code creating a new thread)  then we're done
             // and we just resume all of the presently suspended threads.

             ThreadMap suspendedThreads;

             g_initedEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
             HandleHolder holder(g_initedEvent);

             bool addedPendingCall = false;
             if (addPendingCall != nullptr && threadSafeAddPendingCall) {
                 // we're on a thread safe Python version, go ahead and pend our call to initialize threading.
                 addPendingCall(&AttachCallback, initThreads);
                 addedPendingCall = true;
             }

 #define TICKS_DIFF(prev, cur) ((cur) >= (prev)) ? ((cur)-(prev)) : ((0xFFFFFFFF-(prev))+(cur))
             const DWORD ticksPerSecond = 1000;

            DWORD startTickCount = GetTickCount();
            do {
                SuspendThreads(suspendedThreads, addPendingCall, threadsInited);

                 if (!threadsInited()) {
                    if (*curPythonThread == nullptr) {
                         // no threads are currently running, it is safe to initialize multi threading.
                         PyGILState_STATE gilState;
                         if (version >= PythonVersion_34) {
                             // in 3.4 due to http://bugs.python.org/issue20891,
                             // we need to create our thread state manually
                             // before we can call PyGILState_Ensure() before we
                             // can call PyEval_InitThreads().

                             // Don't require this function unless we need it.
                             auto threadNew = (PyThreadState_NewFunc*)GetProcAddress(module, "PyThreadState_New");
                             if (threadNew != nullptr) {
                                 threadNew(head);
                             }
                         }

                         if (version >= PythonVersion_32) {
                             // in 3.2 due to the new GIL and later we can't call Py_InitThreads
                             // without a thread being initialized.
                             // So we use PyGilState_Ensure here to first
                             // initialize the current thread, and then we use
                             // Py_InitThreads to bring up multi-threading.
                             // Some context here: http://bugs.python.org/issue11329
                             // http://pytools.codeplex.com/workitem/834
                             gilState = pyGilStateEnsure();
                         }
                         initThreads();

                         if (version >= PythonVersion_32) {
                             // we will release the GIL here
                             pyGilStateRelease(gilState);
                         } else {
                             releaseLock();
                         }
                    } else if (!addedPendingCall) {
                        // someone holds the GIL but no one is actively adding any pending calls.  We can pend our call
                        // and initialize threads.
                        addPendingCall(&AttachCallback, initThreads);
                        addedPendingCall = true;
                    }
                }
                ResumeThreads(suspendedThreads);
            } while (!threadsInited() &&
                (TICKS_DIFF(startTickCount, GetTickCount())) < (ticksPerSecond * 20) &&
                !addedPendingCall);

            if (!threadsInited()) {
                if (addedPendingCall) {
                    // we've added our call to initialize multi-threading, we can now wait
                    // until Python code actually starts running.
                    //std::cout << "Waiting for threads to be initialized! " << std::endl << std::flush;
                    ::WaitForSingleObject(g_initedEvent, INFINITE);
                } else {
                    //std::cout << "Connect timeout! " << std::endl << std::flush;
                    return 6;
                }
            } else {
                //std::cout << "Threads initialized! " << std::endl << std::flush;
            }

             if (intervalCheck != nullptr) {
                 *intervalCheck = saveIntervalCheck;
             } else if (setSwitchInterval != nullptr) {
                 setSwitchInterval(saveLongIntervalCheck);
             }
        } else {
            //std::cout << "Threads already initialized! " << std::endl << std::flush;
        }

        if (g_heap != nullptr) {
            HeapDestroy(g_heap);
            g_heap = nullptr;
        }


        GilHolder gilLock(gilEnsure, gilRelease);   // acquire and hold the GIL until done...
        pyRun_SimpleString(command);
        return 0;

	}



    /**
     * Return codes:
     *
     * -2 = could not allocate memory
     * -3 = could not allocate memory to enumerate processes
     *
     * 0 = all OK.
     * 1 = Py_IsInitialized not found
     * 2 = Py_IsInitialized returned false
     * 3 = Missing Python API
     * 4 = Interpreter not initialized
     * 5 = Python version unknown
     * 6 = Connect timeout
     *
     * result[0] should have the same result from the return function
     **/
    DECLDIR int AttachAndRunPythonCode(const char *command, int *result )
    {
        HANDLE hProcess = GetCurrentProcess();
        DWORD modSize = sizeof(HMODULE) * 1024;
        HMODULE* hMods = (HMODULE*)_malloca(modSize);
        if (hMods == nullptr) {
            result[0] = -2;
            return result[0];
        }

        DWORD modsNeeded;
        while (!EnumProcessModules(hProcess, hMods, modSize, &modsNeeded)) {
            // try again w/ more space...
            _freea(hMods);
            hMods = (HMODULE*)_malloca(modsNeeded);
            if (hMods == nullptr) {
                result[0] = -3;
                return result[0];
            }
            modSize = modsNeeded;
        }
        int attached = -1;
        {
             bool pythonFound = false;
             for (size_t i = 0; i < modsNeeded / sizeof(HMODULE); i++) {
                 bool isDebug;
                 if (IsPythonModule(hMods[i], isDebug)) {
                     pythonFound = true;
                     int temp = DoAttach(hMods[i], isDebug, command);
                     if (temp == 0) {
                         // we've successfully attached the debugger
                         attached = 0;
                         break;
                     }else{
                        if(temp > attached){
                            //I.e.: the higher the value the more significant it is.
                            attached = temp;
                         }
                     }
                 }
             }
        }


        HMODULE hModule = NULL;
        if (attached != 0 &&
            GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCTSTR)GetCurrentModuleFilename, &hModule) != 0) {
                // unload ourselves and exit if we failed to attach...
                FreeLibraryAndExitThread(hModule, 0);
        }
        result[0] = attached;
        return result[0];
    }

}