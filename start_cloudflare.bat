@echo off
echo Starting Cloudflare tunnel...

set TUNNEL_EDGE_IP_VERSION=4
set TUNNEL_ORIGIN_CERT=certs/cert.pem
set TUNNEL_METRICS=localhost:20241
set TUNNEL_LOGLEVEL=debug
set TUNNEL_TRANSPORT_LOGLEVEL=debug
set TUNNEL_GRACE_PERIOD=30s
set TUNNEL_RETRIES=5

cloudflared.exe tunnel --url http://localhost:5000 ^
    --no-autoupdate ^
    --origin-ca-pool "certs\cloudflare-origin.pem" ^
    --protocol h2mux ^
    --edge-ip-version 4 ^
    --retries 5 ^
    --grace-period 30s ^
    --metrics localhost:20241 ^
    --loglevel debug ^
    --transport-loglevel debug
pause
