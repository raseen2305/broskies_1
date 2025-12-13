@echo off
REM Clear MongoDB Collections - Windows Batch Script
REM Usage: clear_collections.bat [all|list|specific collection1,collection2]

echo.
echo MongoDB Collection Cleaner
echo ============================================================
echo.

if "%1"=="" (
    echo Usage: clear_collections.bat [command] [options]
    echo.
    echo Commands:
    echo   all                    - Clear ALL collections
    echo   list                   - List all collections
    echo   specific names         - Clear specific collections
    echo.
    echo Examples:
    echo   clear_collections.bat all
    echo   clear_collections.bat list
    echo   clear_collections.bat specific users,repositories
    echo.
    exit /b 1
)

cd /d "%~dp0.."
python scripts/clear_all_collections.py %*
