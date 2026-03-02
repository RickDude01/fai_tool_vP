@echo off
echo ============================================================
echo  FAI Inspection Tool -- PyInstaller build
echo ============================================================
echo.

REM Ensure required packages are installed
pip install pyinstaller pywebview --quiet

echo Building...
pyinstaller fai_tool.spec --clean --noconfirm

echo.
if exist "dist\FAI_Tool.exe" (
    echo  Build successful: dist\FAI_Tool.exe
) else (
    echo  Build FAILED -- check the output above for errors.
    exit /b 1
)
echo ============================================================
