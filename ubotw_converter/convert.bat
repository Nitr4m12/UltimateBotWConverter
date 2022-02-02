@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set /A TOTAL=0
set /A COUNTER=0
FOR %%A IN (%*) DO (
set /A TOTAL+=1
)
echo                                          Z                                      
echo ZZZZZ  ZZZZ  ZZZ   ZZZZZZZ  ZZZ ZZZ     ZZ    ZZ    ZZZZZZZ  ZZZZZZZ            
echo  ZZZ    ZZZ  ZZZ     ZZZ  Z ZZZ  ZZZ   ZZZ    ZZZ     ZZZ  Z ZZZ   Z            
echo  ZZZ    ZZ   ZZZ     ZZZ    ZZZ  ZZZZZZZZZ   ZZZZ     ZZZ    ZZZ Z              
echo  ZZZ    ZZZ  ZZZ     ZZZ    ZZZ  ZZ ZZZ ZZ   ZZZZZ    ZZZ    ZZZ Z              
echo  ZZZ    ZZZ  ZZZ  Z  ZZZ    ZZZ  ZZ     ZZ  ZZ  ZZ    ZZZ    ZZZ   Z            
echo  ZZZ    ZZ   ZZZZZZ  ZZZ    ZZZ  ZZ    ZZZ ZZ   ZZZ   ZZZ    ZZZZZZZ            
echo  ZZZ   ZZZ                                                                      
echo   ZZZ  ZZ    ZZZZZZZ      ZZZZ   ZZZZZZZZ  ZZZZ   ZZ    ZZ                      
echo    ZZZZZ     ZZZ   ZZZ  ZZ   ZZZ Z  ZZ  Z   ZZZ   ZZ    ZZ                      
echo               ZZ   ZZZ ZZZ Z ZZZ    ZZ      ZZZ   ZZZ  ZZ                       
echo               ZZ   ZZZ ZZZ ZZZZZ    ZZ       ZZ  ZZZZ  ZZ                       
echo               ZZZZZZZ   ZZ   ZZZ    ZZ       ZZZZZZZZZZZ                        
echo              ZZZ   ZZZ   ZZZZZ      ZZ        ZZZZ  ZZZZ                        
echo              ZZZ    ZZZ                       ZZZ   ZZZ                         
echo              ZZZ   ZZZZ                        ZZ    ZZ                         
echo              ZZZZZZZZZ                         Z     Z                          
echo.
echo    ZZZZZZ   ZZZZZZ  ZZZ  ZZZ ZZZ   ZZ ZZZZZZZ ZZZZZZZ ZZZZZZZZ  ZZZZZZZ ZZZZZZZ 
echo  ZZZ   ZZ  ZZ   ZZZ  ZZZ ZZ   ZZ  ZZ  ZZZ   Z ZZZ  ZZZZ  ZZZ    ZZZ   Z ZZZ  ZZ 
echo  ZZZ      ZZZ ZZ ZZ  ZZZZZZZ  ZZZ Z   ZZZZZ   ZZZZZZZ    ZZZ    ZZZZZ   ZZZZZZZ 
echo ZZZZ       ZZ Z  ZZ  ZZ ZZZ    ZZZZ   ZZZ Z   ZZZZZ      ZZZ    ZZZ Z   ZZZZZ   
echo ZZZZ       ZZ   ZZZ  ZZ  ZZ    ZZZ    ZZZ   Z ZZZ ZZ     ZZZ    ZZZ   Z ZZZ ZZ  
echo ZZZZ        ZZZZZ   ZZZ   ZZ   ZZZ    ZZZZZZZ ZZZ  ZZZ   ZZZ    ZZZZZZZ ZZZ  ZZ 
echo  ZZZ    Z                                                                       
echo  ZZZZ  ZZ                                                                       
echo    ZZZZZZ                                                                       
FOR %%A IN (%*) DO (
echo.
set /A COUNTER+=1
echo Attempting to convert !COUNTER! of %TOTAL% mods, please wait...
echo.
python converter.py %%A
)
echo.
echo Processed %COUNTER% mods.
echo.
pause
