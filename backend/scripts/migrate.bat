@echo off
REM migrate.bat - Run Alembic migrations for this project (Windows CMD)
REM usage: migrate.bat [DATABASE_URL]

setlocal
if "%~1"=="" (
  if not "%DATABASE_URL%"=="" (
    set "DBURL=%DATABASE_URL%"
  ) else (
    set "DBURL=sqlite:///./backend/database.db"
  )
) else (
  set "DBURL=%~1"
)
set DATABASE_URL=%DBURL%
if defined PYTHONPATH (
  set PYTHONPATH=%PYTHONPATH%;backend
) else (
  set PYTHONPATH=backend
)

echo Using DATABASE_URL=%DATABASE_URL%

if exist backend\.venv\Scripts\activate.bat (
  call backend\.venv\Scripts\activate.bat
)

python -m alembic upgrade head
endlocal
