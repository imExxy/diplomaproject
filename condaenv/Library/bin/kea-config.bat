@echo off

IF "%1"=="" (
   echo kea-config.bat [OPTIONS]
   echo Options:
   echo     [--prefix]
   echo     [--version]
   echo     [--libs]
   echo     [--cflags]
   echo     [--includes]
   EXIT /B 1
) ELSE (
:printValue
    if "%1" neq "" (
	    IF "%1"=="--prefix" echo D:/xxx/Documents/geeproject/condaenv/Library
	    IF "%1"=="--version" echo 1.5.3
	    IF "%1"=="--cflags" echo -ID:/xxx/Documents/geeproject/condaenv/Library/include
	    IF "%1"=="--libs" echo -LIBPATH:D:/xxx/Documents/geeproject/condaenv/Library/lib libkea.lib 
	    IF "%1"=="--includes" echo D:/xxx/Documents/geeproject/condaenv/Library/include
		shift
		goto :printValue
    )
	EXIT /B 0
)
