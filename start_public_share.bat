@echo off
title CWA Temperature Broadcast - Public Share
echo ========================================================
echo  CWA Temperature Broadcast (台灣觀測站氣溫)
echo  正在啟動本機伺服器與全世界公開連線通道...
echo ========================================================
echo.
start /b python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak >nul
echo 正在建立公開網址 (Cloudflare Tunnel)...
echo 請複製終端機下方顯示的 trycloudflare.com 網址分享給他人！
echo.
.\cloudflared.exe tunnel --url http://localhost:8000
pause
