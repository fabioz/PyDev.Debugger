call "C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\vcvarsall.bat" x86

cl -DUNICODE -D_UNICODE /EHsc /LD attach.cpp /link /out:attach_x86.dll

call "C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\vcvarsall.bat" x86_amd64

cl -DUNICODE -D_UNICODE /EHsc /LD attach.cpp /link /out:attach_amd64.dll