@echo off
title Taiwan Weather Forecast - Public Share
echo ========================================================
echo  Taiwan Weather Forecast (台灣天氣預報系統)
echo  正在啟動本機伺服器與全世界公開連線通道...
echo ========================================================
echo.
start /b python -m streamlit run app.py --server.headless true --server.port 8501
timeout /t 3 /nobreak >nul
echo 正在建立公開網址 (Cloudflare Tunnel)...
echo 請複製終端機下方顯示的 trycloudflare.com 網址分享給他人！
echo.
.\cloudflared.exe tunnel --url http://localhost:8501
pause
