@echo off
setlocal
chcp 65001 >nul
rem ============================================================
rem  pgvector 설치 (Windows + PostgreSQL 18)
rem  사용법: 이 파일을 마우스 오른쪽 클릭 -> "관리자 권한으로 실행"
rem ============================================================

set "PGVECTOR_VERSION=v0.8.1"
if "%PGROOT%"=="" set "PGROOT=C:\Program Files\PostgreSQL\18"
set "SRC=%TEMP%\pgvector"

echo [1/5] 관리자 권한 확인...
net session >nul 2>&1
if errorlevel 1 (
    echo   [실패] 관리자 권한이 아닙니다. 파일을 우클릭 -^> "관리자 권한으로 실행" 하세요.
    goto :fail
)

echo [2/5] PostgreSQL 확인...
if not exist "%PGROOT%\include\server\postgres.h" (
    echo   [실패] PostgreSQL 을 찾을 수 없습니다: %PGROOT%
    echo          다른 경로에 설치했다면 PGROOT 를 수정하세요.
    goto :fail
)

echo [3/5] Visual Studio C++ 빌드 도구 찾는 중...
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    echo   [실패] Visual Studio / Build Tools 가 없습니다.
    echo          "C++를 사용한 데스크톱 개발" 워크로드를 포함해 설치하세요.
    goto :fail
)
set "VSPATH="
for /f "usebackq delims=" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSPATH=%%i"
if "%VSPATH%"=="" (
    echo   [실패] C++ 빌드 도구가 없습니다. Visual Studio Installer 에서
    echo          "C++를 사용한 데스크톱 개발" 워크로드를 추가하세요.
    goto :fail
)
call "%VSPATH%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 goto :fail

echo [4/5] pgvector %PGVECTOR_VERSION% 다운로드 및 빌드...
if exist "%SRC%" rmdir /s /q "%SRC%"
mkdir "%SRC%"
curl -sSfL -o "%SRC%\pgvector.zip" https://github.com/pgvector/pgvector/archive/refs/tags/%PGVECTOR_VERSION%.zip
if errorlevel 1 goto :fail
tar -xf "%SRC%\pgvector.zip" -C "%SRC%"
if errorlevel 1 goto :fail
cd /d "%SRC%\pgvector-%PGVECTOR_VERSION:~1%"
if errorlevel 1 goto :fail
nmake /nologo /F Makefile.win
if errorlevel 1 goto :fail

echo [5/5] PostgreSQL 에 설치...
nmake /nologo /F Makefile.win install
if errorlevel 1 goto :fail

if not exist "%PGROOT%\lib\vector.dll" goto :fail
echo.
echo ============================================================
echo  설치 완료: %PGROOT%\lib\vector.dll
echo  이제 python embedding_postgre.py 를 다시 실행하세요.
echo ============================================================
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  설치 실패 - 위 메시지를 캡처해서 공유해 주세요.
echo ============================================================
pause
exit /b 1
