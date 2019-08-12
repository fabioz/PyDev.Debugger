SET FUNCHOOK_INCLUDEPATH=X:\funchook\include
SET FUNCHOOK_LIBPATH=X:\funchook\win32\Release

call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" x86
nmake all

copy attach_x86.dll ..\win_x86\attach_x86.dll /Y
copy attach_x86.pdb ..\win_x86\attach_x86.pdb /Y

nmake clean


call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" x86_amd64
SET TARGET_PLATFORM=amd64
nmake all

copy attach_amd64.dll ..\win_amd64\attach_amd64.dll /Y
copy attach_amd64.pdb ..\win_amd64\attach_amd64.pdb /Y

nmake clean

