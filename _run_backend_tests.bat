@echo off
cd backend
set DEBUG=true
set POSTGRES_HOST=127.0.0.1
set POSTGRES_USER=plantos
set POSTGRES_PASSWORD=plantos_test
set POSTGRES_DB=plantos_test
python -m pytest tests -v --tb=short --timeout=30 2>&1
echo EXIT: %ERRORLEVEL%
