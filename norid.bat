@echo off
REM Norid CLI - Interaktivt menysystem for Windows
REM Kjor med: norid.bat

setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

set SCRIPT_DIR=%~dp0
set USE_TEST=
set ENV_NAME=Produksjon

REM Opprett venv hvis det ikke finnes
if not exist "%SCRIPT_DIR%venv" (
    echo Oppretter virtuelt miljo...
    python -m venv "%SCRIPT_DIR%venv"
    echo Installerer avhengigheter...
    "%SCRIPT_DIR%venv\Scripts\pip.exe" install -q -r "%SCRIPT_DIR%requirements.txt"
    echo Ferdig!
    timeout /t 1 >nul
)

goto main_menu

:show_logo
cls
echo.
echo   [36m _   _            _     _    ____ _     ___ [0m
echo   [36m^| \ ^| ^| ___  _ __(_) __^| ^|  / ___^| ^|   ^|_ _^|[0m
echo   [36m^|  \^| ^|/ _ \^| '__^| ^|/ _` ^| ^| ^|   ^| ^|    ^| ^| [0m
echo   [36m^| ^|\  ^| (_) ^| ^|  ^| ^| (_^| ^| ^| ^|___^| ^|___ ^| ^| [0m
echo   [36m^|_^| \_^|\___/^|_^|  ^|_^|\__,_^|  \____^|_____^|___^|[0m
echo.
echo   [90m--------------------------------------------------[0m
echo   [90m  Sla opp .no-domener uten autentisering[0m
echo   [90m--------------------------------------------------[0m
echo.
goto :eof

:run_cmd
echo.
"%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%norid_cli.py" %USE_TEST% %*
echo.
echo [90mTrykk Enter for a fortsette...[0m
pause >nul
goto :eof

:main_menu
call :show_logo
echo [1mHOVEDMENY[0m [90m[%ENV_NAME%][0m
echo.
echo   [36m1)[0m Domeneoppslag (RDAP)
echo   [36m2)[0m Sjekk om ledig (DAS)
echo   [36m3)[0m Whois-oppslag
echo   [36m4)[0m Entitetsoppslag
echo   [36m5)[0m Navneserveroppslag
echo.
echo   [36m8)[0m Innstillinger
echo   [36m9)[0m Avansert modus
echo   [36m0)[0m Avslutt
echo.
set /p choice="Valg: "

if "%choice%"=="1" goto menu_domain
if "%choice%"=="2" goto do_das
if "%choice%"=="3" goto do_whois
if "%choice%"=="4" goto menu_entity
if "%choice%"=="5" goto menu_nameserver
if "%choice%"=="8" goto menu_settings
if "%choice%"=="9" goto advanced_mode
if "%choice%"=="0" goto exit_app
if "%choice%"=="" goto exit_app
goto main_menu

:menu_domain
call :show_logo
echo [1mDOMENEOPPSLAG (RDAP)[0m [90m[%ENV_NAME%][0m
echo.
echo   [36m1)[0m Sla opp domene
echo   [36m2)[0m Sjekk om domene eksisterer
echo   [36m3)[0m Vis som JSON
echo.
echo   [36m0)[0m Tilbake til hovedmeny
echo.
set /p choice="Valg: "

if "%choice%"=="1" (
    echo.
    set /p domain="Domenenavn (f.eks. norid.no): "
    if not "!domain!"=="" call :run_cmd domain "!domain!"
)
if "%choice%"=="2" (
    echo.
    set /p domain="Domenenavn (f.eks. norid.no): "
    if not "!domain!"=="" call :run_cmd domain "!domain!" --available
)
if "%choice%"=="3" (
    echo.
    set /p domain="Domenenavn (f.eks. norid.no): "
    if not "!domain!"=="" call :run_cmd domain "!domain!" --json
)
if "%choice%"=="0" goto main_menu
if "%choice%"=="" goto main_menu
goto menu_domain

:do_das
call :show_logo
echo [1mSJEKK OM DOMENE ER LEDIG (DAS)[0m [90m[%ENV_NAME%][0m
echo.
set /p domain="Domenenavn (f.eks. example.no): "
if not "%domain%"=="" call :run_cmd das "%domain%"
goto main_menu

:do_whois
call :show_logo
echo [1mWHOIS-OPPSLAG[0m [90m[%ENV_NAME%][0m
echo.
set /p domain="Domenenavn (f.eks. norid.no): "
if not "%domain%"=="" call :run_cmd whois "%domain%"
goto main_menu

:menu_entity
call :show_logo
echo [1mENTITETSOPPSLAG[0m [90m[%ENV_NAME%][0m
echo.
echo   [36m1)[0m Sla opp registrar
echo   [36m2)[0m Sla opp kontaktperson
echo   [36m3)[0m Vis som JSON
echo.
echo   [36m0)[0m Tilbake til hovedmeny
echo.
set /p choice="Valg: "

if "%choice%"=="1" (
    echo.
    echo [90mEksempel: reg1-NORID, reg1103-NORID[0m
    set /p handle="Registrar-handle: "
    if not "!handle!"=="" call :run_cmd entity "!handle!"
)
if "%choice%"=="2" (
    echo.
    echo [90mEksempel: NH55R-NORID[0m
    set /p handle="Kontakt-handle: "
    if not "!handle!"=="" call :run_cmd entity "!handle!"
)
if "%choice%"=="3" (
    echo.
    set /p handle="Handle: "
    if not "!handle!"=="" call :run_cmd entity "!handle!" --json
)
if "%choice%"=="0" goto main_menu
if "%choice%"=="" goto main_menu
goto menu_entity

:menu_nameserver
call :show_logo
echo [1mNAVNESERVEROPPSLAG[0m [90m[%ENV_NAME%][0m
echo.
echo   [36m1)[0m Sla opp navneserver (via handle)
echo   [36m2)[0m Sok etter navneservere (via hostname)
echo   [36m3)[0m Vis som JSON
echo.
echo   [36m0)[0m Tilbake til hovedmeny
echo.
set /p choice="Valg: "

if "%choice%"=="1" (
    echo.
    echo [90mEksempel: X11H-NORID[0m
    set /p handle="Navneserver-handle: "
    if not "!handle!"=="" call :run_cmd nameserver "!handle!"
)
if "%choice%"=="2" (
    echo.
    echo [90mEksempel: x.nic.no eller *.nic.no[0m
    set /p pattern="Hostname/monster: "
    if not "!pattern!"=="" call :run_cmd search nameservers "!pattern!"
)
if "%choice%"=="3" (
    echo.
    set /p handle="Navneserver-handle: "
    if not "!handle!"=="" call :run_cmd nameserver "!handle!" --json
)
if "%choice%"=="0" goto main_menu
if "%choice%"=="" goto main_menu
goto menu_nameserver

:menu_settings
call :show_logo
echo [1mINNSTILLINGER[0m
echo.
if "%USE_TEST%"=="" (
    echo   Navaerende miljo: [32mProduksjon[0m
) else (
    echo   Navaerende miljo: [33mTest[0m
)
echo.
echo   [36m1)[0m Bytt til produksjonsmiljo
echo   [36m2)[0m Bytt til testmiljo
echo.
echo   [36m0)[0m Tilbake til hovedmeny
echo.
set /p choice="Valg: "

if "%choice%"=="1" (
    set USE_TEST=
    set ENV_NAME=Produksjon
    echo.
    echo [32mByttet til produksjonsmiljo[0m
    timeout /t 1 >nul
)
if "%choice%"=="2" (
    set USE_TEST=--test
    set ENV_NAME=Test
    echo.
    echo [33mByttet til testmiljo[0m
    timeout /t 1 >nul
)
if "%choice%"=="0" goto main_menu
if "%choice%"=="" goto main_menu
goto menu_settings

:advanced_mode
call :show_logo
echo [1mAVANSERT MODUS[0m - Skriv kommandoer direkte
echo [90mSkriv 'exit' for a ga tilbake til menyen[0m
echo [90mSkriv 'help' for a se tilgjengelige kommandoer[0m
echo.

:advanced_loop
set /p cmd="[32mnorid[0m[1m>[0m "
if "%cmd%"=="exit" goto main_menu
if "%cmd%"=="quit" goto main_menu
if "%cmd%"=="help" (
    "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%norid_cli.py" --help
    echo.
    goto advanced_loop
)
if not "%cmd%"=="" (
    "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%norid_cli.py" %USE_TEST% %cmd%
    echo.
)
goto advanced_loop

:exit_app
call :show_logo
echo [36mHa det![0m
echo.
exit /b 0
