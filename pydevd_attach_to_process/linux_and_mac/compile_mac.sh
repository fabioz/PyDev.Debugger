g++ -fPIC -D_REENTRANT -std=c++11 -arch x86_64 -c -o attach_amd64.o attach.cpp
g++ -dynamiclib -nostartfiles -arch x86_64 -o attach_amd64.dylib attach_amd64.o -lc
rm attach_amd64.o
mv attach_amd64.dylib ../attach_amd64.dylib


g++ -fPIC -D_REENTRANT -std=c++11 -arch i386 -c -o attach_x86.o attach.cpp
g++ -dynamiclib -nostartfiles -arch i386 -o attach_x86.dylib attach_x86.o -lc
rm attach_x86.o
mv attach_x86.dylib ../attach_x86.dylib

