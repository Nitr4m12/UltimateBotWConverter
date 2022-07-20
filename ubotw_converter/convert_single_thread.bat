@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set /A TOTAL=0
set /A COUNTER=0
FOR %%A IN (%*) DO (
set /A TOTAL+=1
)
echo +++++++++++++++++++++++++++
echo + Ultimate BotW Converter +
echo +++++++++++++++++++++++++++
FOR %%A IN (%*) DO (
echo.
set /A COUNTER+=1
echo Attempting to convert !COUNTER! of %TOTAL% mods, please wait...
echo.
python converter.py -s %%A
)
echo.
echo Processed %COUNTER% mods.
echo.
pause
