@echo off
REM Markdown Converter Launcher
REM Quick launcher for converting markdown files to HTML/PDF

title Markdown Converter

:menu
cls
echo ===============================================
echo        Markdown to HTML/PDF Converter
echo ===============================================
echo.
echo 1. Convert single file to HTML
echo 2. Convert single file to PDF
echo 3. Convert all markdown files in a directory to HTML
echo 4. Convert all markdown files in a directory to PDF
echo 5. Generate default CSS file
echo 6. Help / Usage Examples
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto single_html
if "%choice%"=="2" goto single_pdf
if "%choice%"=="3" goto dir_html
if "%choice%"=="4" goto dir_pdf
if "%choice%"=="5" goto gen_css
if "%choice%"=="6" goto help
if "%choice%"=="7" goto end
goto menu

:single_html
cls
echo Convert Single File to HTML
echo ============================
echo.
set /p mdfile="Enter markdown file path (or drag & drop): "
set mdfile=%mdfile:"=%
python "%~dp0md_converter.py" "%mdfile%"
echo.
pause
goto menu

:single_pdf
cls
echo Convert Single File to PDF
echo ===========================
echo.
set /p mdfile="Enter markdown file path (or drag & drop): "
set mdfile=%mdfile:"=%
python "%~dp0md_converter.py" "%mdfile%" -f pdf
echo.
pause
goto menu

:dir_html
cls
echo Convert Directory to HTML
echo ==========================
echo.
set /p directory="Enter directory path: "
set directory=%directory:"=%
set /p recursive="Include subdirectories? (y/n): "
if /i "%recursive%"=="y" (
    python "%~dp0md_converter.py" -d "%directory%" -r
) else (
    python "%~dp0md_converter.py" -d "%directory%"
)
echo.
pause
goto menu

:dir_pdf
cls
echo Convert Directory to PDF
echo =========================
echo.
set /p directory="Enter directory path: "
set directory=%directory:"=%
set /p recursive="Include subdirectories? (y/n): "
if /i "%recursive%"=="y" (
    python "%~dp0md_converter.py" -d "%directory%" -f pdf -r
) else (
    python "%~dp0md_converter.py" -d "%directory%" -f pdf
)
echo.
pause
goto menu

:gen_css
cls
echo Generate Default CSS File
echo ==========================
python "%~dp0md_converter.py" --generate-css
echo.
pause
goto menu

:help
cls
echo ===============================================
echo        Markdown Converter - Help
echo ===============================================
echo.
echo COMMAND LINE USAGE:
echo -------------------
echo python md_converter.py input.md
echo   Convert single file to HTML
echo.
echo python md_converter.py input.md -f pdf
echo   Convert single file to PDF
echo.
echo python md_converter.py -d ./reports/
echo   Convert all .md files in directory
echo.
echo python md_converter.py -d ./reports/ -r
echo   Convert recursively (include subdirectories)
echo.
echo python md_converter.py input.md -o output.html
echo   Specify custom output filename
echo.
echo python md_converter.py input.md --css custom.css
echo   Use custom CSS styling
echo.
echo.
echo REQUIREMENTS:
echo -------------
echo - Python 3.6 or higher
echo - pip install markdown
echo - pip install weasyprint (for PDF support)
echo.
echo.
echo PDF Note: WeasyPrint may require additional
echo system dependencies on Linux/macOS
echo.
pause
goto menu

:end
exit /b 0
