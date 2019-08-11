# Specify compiler
CC=cl.exe

# Specify linker
LINK=link.exe

CC_FLAGS=/EHsc -I"$(FUNCHOOK_INCLUDEPATH)" -DUNICODE -D_UNICODE /EHsc /Zi /O1 /W3

TARGET_NAME=attach_$(TARGET_PLATFORM)

# Link the object files into a binary
all : attach.o
    $(LINK) /DLL /DEBUG /OPT:REF /OPT:ICF /LIBPATH:"$(FUNCHOOK_LIBPATH)" /out:$(TARGET_NAME).dll attach.o

# Compile the source files into object files
attach.o : attach.cpp
    $(CC) /c attach.cpp $(CC_FLAGS) /Foattach.o
    
# Clean target
clean :
    del $(TARGET_NAME).dll
    del $(TARGET_NAME).exp
    del $(TARGET_NAME).lib
    del *.o
    del *.pdb