/* ****************************************************************************
 *
 * Copyright (c) Brainwy software Ltda.
 *
 * This source code is subject to terms and conditions of the Apache License, Version 2.0. A
 * copy of the license can be found in the License.html file at the root of this distribution. If
 * you cannot locate the Apache License, Version 2.0, please send an email to
 * vspython@microsoft.com. By using this source code in any fashion, you are agreeing to be bound
 * by the terms of the Apache License, Version 2.0.
 *
 * You must not remove this notice, or any other, from this software.
 *
 * ***************************************************************************/

#ifndef _ATTACH_DLL_H_
#define _ATTACH_DLL_H_

#if defined DLL_EXPORT
#define DECLDIR __declspec(dllexport)
#else
#define DECLDIR __declspec(dllimport)
#endif


extern "C"
{
    DECLDIR int AttachAndRunPythonCode(const char *command, int *result );
    
    DECLDIR int GetMainThreadId();
    
    /*
     * Helper to print debug information from the current process
     */
    DECLDIR int PrintDebugInfo();
    
    /*
     * Helper to cast to a pyobject in the library. Actual work
     * is done by declaring the below in the python side.
     * 
     * lib.cast_to_pyobject.argtypes = (ctypes.c_voidp,)
     * lib.cast_to_pyobject.restype = ctypes.py_object
     */
    DECLDIR void* cast_to_pyobject(void* obj) { return obj; };
    
    /*
     * Returns nullptr or a PyObject* list with the thread ids. 
     */
    DECLDIR void* list_all_thread_ids();
    
    
    /*
    Could be used with ctypes (note that the threading should be initialized, so, 
    doing it in a thread as below is recommended):
    
    def check():
        
        import ctypes
        lib = ctypes.cdll.LoadLibrary(r'C:\...\attach_x86.dll')
        print 'result', lib.AttachDebuggerTracing(0)
        
    t = threading.Thread(target=check)
    t.start()
    t.join()
    */
    DECLDIR int AttachDebuggerTracing(
        bool showDebugInfo, 
        void* pSetTraceFunc, // Actually PyObject*, but we don't want to include it here.
        void* pTraceFunc,  // Actually PyObject*, but we don't want to include it here.
        unsigned int threadId
    );
}

#endif