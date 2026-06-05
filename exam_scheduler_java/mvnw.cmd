@echo off
setlocal enableextensions

set "MAVEN_VERSION=3.9.9"
set "MAVEN_HOME=%~dp0.mvn\apache-maven-%MAVEN_VERSION%"
set "MAVEN_URL=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/%MAVEN_VERSION%/apache-maven-%MAVEN_VERSION%-bin.zip"
set "MAVEN_ZIP=%~dp0.mvn\maven.zip"

:: 1. Use system Maven if available
where mvn >nul 2>&1
if %ERRORLEVEL%==0 (
    mvn %*
    exit /b %ERRORLEVEL%
)

:: 2. Use locally downloaded Maven if present
if exist "%MAVEN_HOME%\bin\mvn.cmd" goto :run_local

:: 3. Download Maven
echo Maven not found. Downloading Apache Maven %MAVEN_VERSION%...
if not exist "%~dp0.mvn" mkdir "%~dp0.mvn"

powershell -NoProfile -Command ^
  "$wc = New-Object System.Net.WebClient; $wc.DownloadFile('%MAVEN_URL%', '%MAVEN_ZIP%'); Write-Host 'Downloaded.'"
if %ERRORLEVEL% neq 0 ( echo ERROR: Download failed. && exit /b 1 )

echo Extracting...
powershell -NoProfile -Command ^
  "Expand-Archive -Path '%MAVEN_ZIP%' -DestinationPath '%~dp0.mvn\' -Force; Remove-Item '%MAVEN_ZIP%'"
if %ERRORLEVEL% neq 0 ( echo ERROR: Extraction failed. && exit /b 1 )
echo Maven ready.

:run_local
set "PATH=%MAVEN_HOME%\bin;%PATH%"
mvn %*
endlocal
