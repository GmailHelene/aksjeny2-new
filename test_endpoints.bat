@echo off
echo ========================================
echo   API Endpoint Testing with curl
echo ========================================

echo.
echo Testing root endpoint (/)...
curl -s -o nul -w "Status code: %%{http_code}\n" http://localhost:5000/

echo.
echo Testing diagnostic endpoint (/diagnostic/auth-status)...
curl -s -o nul -w "Status code: %%{http_code}\n" http://localhost:5000/diagnostic/auth-status

echo.
echo Testing test access control endpoint (/test/access-control)...
curl -s -o nul -w "Status code: %%{http_code}\n" http://localhost:5000/test/access-control

echo.
echo Testing profile endpoint (/profile/)...
curl -s -o nul -w "Status code: %%{http_code}\n" http://localhost:5000/profile/

echo.
echo Testing portfolio endpoint (/portfolio/)...
curl -s -o nul -w "Status code: %%{http_code}\n" http://localhost:5000/portfolio/

echo.
echo Testing complete
