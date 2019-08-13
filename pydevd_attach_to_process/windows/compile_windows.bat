SET FUNCHOOK_INCLUDEPATH=X:\funchook\include
SET FUNCHOOK_LIBPATH=X:\funchook\win32\Release

:: call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" x86
:: nmake all
:: 
:: copy attach_x86.dll ..\dlls\win_x86\attach_x86.dll /Y
:: copy attach_x86.pdb ..\dlls\win_x86\attach_x86.pdb /Y
:: copy %FUNCHOOK_LIBPATH%\funchook.dll ..\dlls\win_x86\funchook.dll /Y
:: 
:: nmake clean


SET FUNCHOOK_INCLUDEPATH=X:\funchook\include
SET FUNCHOOK_LIBPATH=X:\funchook\win32\x64\Release

:: call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" x64
SET TARGET_PLATFORM=amd64
nmake all

copy attach_amd64.dll ..\dlls\win_amd64\attach_amd64.dll /Y
copy attach_amd64.pdb ..\dlls\win_amd64\attach_amd64.pdb /Y
copy %FUNCHOOK_LIBPATH%\funchook.dll ..\dlls\win_amd64\funchook.dll /Y

nmake clean

