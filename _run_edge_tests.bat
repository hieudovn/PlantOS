@echo off
set PYTHONPATH=.
set EDGE_DEV_INSECURE_AUTH=true
python -m pytest edge-v2/tests -v --tb=short --timeout=30 2>&1
echo EXIT: %ERRORLEVEL%
