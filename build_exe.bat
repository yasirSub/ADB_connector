@echo off

echo Building ADB Connector Executable...
echo.

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

REM Build the executable
pyinstaller --onefile --windowed --name "ADB_Connector" main.py

echo.
echo Build completed!
echo Executable location: dist\ADB_Connector.exe
echo.
pause
