//compile with: gcc -shared -o attach_linux.so -fPIC -nostartfiles attach_linux.c

#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include "python.h"

extern int hello(void);
extern int hello2(void);


int hello2(){
	printf("Hello2!\n");
}


int hello()
{
    printf("Hello world!\n");


    void *hndl = dlsym (NULL, "PyGILState_Ensure");
    if(hndl == NULL){
	    printf("NULL\n");

    }else{
	    printf("Worked!\n");

    }
//     void *hndl = dlopen (NULL, RTLD_LAZY);
//     if (!hndl) {
//     	fprintf(stderr, "dlopen failed: %s\n", dlerror());
//     	return 3;
//     };
//
//     void (*fptr) (void) = dlsym (hndl, buf);
//     if (fptr != NULL){
//       fprintf(stderr, "dlsym %s failed: %s\n", buf, dlerror());
//       fptr ();
//     }else{
//       fprintf(stderr, "dlsym %s failed: %s\n", buf, dlerror());
//   	}
//     dlclose (hndl);


    return 2;
}

// gdb -p 4957
// call dlopen("/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so", 1|8)
// call dlsym($1, "hello")
// call hello()


// call open("/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so", 2)
// call mmap(0, 6215, 1 | 2 | 4, 1, 3 , 0)

// call dlopen("/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so", 1|8)
// call dlsym($1, "hello")
// call hello()


// file attach_linux.so