@echo off
echo Starting Cloudflare tunnel (alternative mode)...
echo Press Ctrl+C to stop
echo.
cloudflared.exe tunnel --no-chunked-encoding --no-tls-verify --loglevel debug --url http://localhost:5000 