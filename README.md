# 🌤️ Taiwan Weather Forecast (台灣天氣預報互動式應用)

> 🌐 **永久線上網址 (Live Demo)**：Render 部署完成後，請將平台提供的網址填入此處。  
> 📦 **GitHub 專案倉庫**：**[https://github.com/stevenwujr/0923testproject](https://github.com/stevenwujr/0923testproject)**  
> 
> 🎓 **AI 創新微課程：從氣象資料到互動式天氣預報應用**  
> 🛠️ **核心技術棧**：CWA API × JSON × Python × SQLite × Streamlit × Folium  
> 🤖 **開發實作思維**：Vibe Coding (自然語言對話 → AI 規劃架構 → 逐步實作與測試)

---

## 📖 專案簡介

本專案依據「**AI 創新微課程**」24 步驟完整學習地圖與「**打造你的 AI Coding Agent**」流程打造。整合**交通部中央氣象署 (CWA) Open Data API**、**SQLite 輕量關聯資料庫**、**Pandas 資料清洗處理**、**Altair 走勢圖**、**Folium 台灣互動地理資訊圖資**與 **Streamlit 儀表板框架**，提供直觀、即時且富美感的全台天氣預報體驗。

---

## 🗺️ 微課程 24 步驟全要素實踐對照表

| 步驟 | 課綱主題 | 本專案對應實作與模組位置 |
| :---: | :--- | :--- |
| **01** | 課程介紹 | 完整學習地圖與 Vibe Coding 架構設計 (`README.md`, `app.py` Tab 4) |
| **02** | 台灣的天氣與生活 | 智慧氣象生活決策應用（穿搭建議、農事溫差、戶外活動指標） |
| **03** | 中央氣象署 CWA Open Data 平台 | 支援 CWA API Key 授權設定與資料集對接 (`F-D0047-091`) |
| **04** | API 資料取得 | 使用 `requests` 模組透過 HTTP Header 傳遞授權碼取得 JSON (`src/cwa_api.py`) |
| **05** | JSON 資料結構解析 | 定位 `locations`、`weatherElement` (MinT/MaxT) 與日期時間結構 |
| **06** | 提取最高與最低氣溫 | 自動萃取日最低溫 (MinT) 與日最高溫 (MaxT) 浮點數值 |
| **07** | 資料整理與預覽 | 使用 Pandas 結構化為 `regionName`, `dataDate`, `mint`, `maxt` 表格 |
| **08** | 建立 SQLite 資料庫 | 自動初始化本機 `data/weather.db` 資料庫 (`src/db.py`) |
| **09** | 資料庫設計 | 建立 `TemperatureForecasts` 表，具備主鍵、分區、日期與時間戳欄位 |
| **10** | 查詢資料驗證 | 提供 `SELECT DISTINCT regionName` 與 `WHERE regionName='...'` 等 SQL 驗證器 |
| **11** | Streamlit 入門 | 基於 Streamlit 現代化響應式介面建構 (`app.py`) |
| **12** | 從資料庫讀取資料 | 透過 `sqlite3` 與 `pd.read_sql_query` 安全讀取資料 |
| **13** | 下拉選單選擇地區 | 支援 `北部地區`、`中部地區`、`南部地區`、`東部地區`、離島等切換 |
| **14** | 繪製折線圖 | 使用 Altair 繪製一週最高/最低氣溫雙色對比折線走勢圖 (`src/visualizer.py`) |
| **15** | 顯示資料表格 | 精美格式化展示預報數值（日期、MinT、MaxT、日溫差、均溫） |
| **16** | 整合 Web App 介面 | 現代化 Hero Banner、KPI 指標卡與分頁切換元件 |
| **17** | 進階：台灣地圖視覺化 | 使用 Folium 依據 4 段溫度色階繪製圓點標記與圖例 (`<20°C`, `20-25°C`, `25-30°C`, `>30°C`) |
| **18** | 選擇日期顯示地圖 | 下拉選單選取日期，即時連動地圖各區圓圈標記、氣溫與 Popup 資訊卡 |
| **19** | 完整成果展示 | Taiwan Weather Dashboard 整合地圖、趨勢、統計與資料庫監控 |
| **20** | 程式碼品質與優化 | 模組化分層、全面 try-except 錯誤捕捉、**防重複插入冪等性 (`ON CONFLICT DO UPDATE`)** |
| **21** | 專案上傳至 GitHub | 配置 `.gitignore`、`requirements.txt`，提供 Git 初始化與推送流程 |
| **22** | 延伸應用與想法 | 天氣提醒 LINE Bot、AI 穿搭解說員、農業防寒預警應用指引 |
| **23** | 回顧與重點整理 | 梳理 API → JSON → DB → Dashboard 的端到端數據流 |
| **24** | 下一步：繼續探索 | 連接氣象雷達圖、即時空品 AQI、Gemini 智慧對話助理 |

---

## 📂 專案目錄結構

```text
Taiwan-Weather-Project/
├── .gitignore                     # Git 排除清單 (.venv, __pycache__, 等)
├── README.md                      # 專案說明文件
├── requirements.txt               # 相依套件清單
├── app.py                         # Streamlit 視覺化主應用程式
├── data/
│   ├── sample_cwa_weather.json    # 預置之台灣全區氣溫示範資料 (免 Key 即可完整體驗)
│   └── weather.db                 # SQLite 資料庫 (存放 TemperatureForecasts)
├── src/
│   ├── __init__.py
│   ├── cwa_api.py                 # CWA API 請求與 JSON 結構解析
│   ├── db.py                      # SQLite 資料庫 CRUD、SQL 驗證與防重複機制
│   └── visualizer.py              # Folium 台灣互動地圖與 Altair 折線圖
└── tests/
    └── test_pipeline.py           # 自動化測試腳本 (涵蓋解析、冪等性、查詢與渲染)
```

---

## 🚀 快速開始

### 1. 安裝相依套件
確保使用 Python 3.10+ 環境，執行：
```bash
pip install -r requirements.txt
```

### 2. 啟動 Streamlit 應用程式
在專案根目錄下執行：
```bash
python -m streamlit run app.py
```
啟動後，瀏覽器將自動開啟 `http://localhost:8501`。

### FastAPI + Windy 觀測站 MVP

本專案另包含符合設計文件的 FastAPI 版本，入口為 `backend/app/main.py`，首頁為 `backend/static/index.html`。

在專案根目錄執行：

```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

### GitHub push 後自動部署（永久網址）

專案已附上 `render.yaml`，可使用 Render 從 GitHub 自動部署新版 FastAPI 觀測站：

1. 開啟 [Render](https://render.com/)，使用 GitHub 登入。
2. 選擇 **New + → Blueprint**，連結 `stevenwujr/0923testproject`。
3. Render 會讀取 `render.yaml`，建立 Web Service。
4. 在 Render 的 Environment 設定 `CWA_API_KEY`；`WINDY_API_KEY` 沒有使用需求時可留空。
5. 部署完成後取得 Render 網址，例如 `https://taiwan-weather-dashboard.onrender.com`。

之後只要執行 `git push`，Render 就會自動重新部署。免費方案可能在一段時間沒有流量後休眠，第一次開啟時需要等待幾秒；若需要真正不休眠的服務，請改用付費方案。CWA API 金鑰只應設定在 Render Environment，不要寫進程式碼或提交 `.env`。

開啟 `http://localhost:8000` 後，可使用台灣地圖、CWA 站點溫度標記、popup、溫度圖例、手動刷新、縣市篩選與站點標籤。設定有效的 `CWA_API_KEY` 後，後端會從 `CWA_DATA_URL` 取得觀測資料；未設定或上游失敗時會顯示內建示範資料並標示 `stale`，因此展示不會因外部服務中斷而崩潰。

### Cloudflare 公開分享

先確認 `.env` 已放在專案根目錄，再雙擊 `start_public_share.bat`。腳本會啟動 FastAPI `8000`，並將 Cloudflare tunnel 指向同一個服務；終端機顯示的 `trycloudflare.com` 網址就是新版觀測站頁面。Quick Tunnel 網址是臨時網址，每次重新啟動可能不同。

PowerShell 環境變數範例：

```powershell
$env:CWA_API_KEY = "your_cwa_api_key"
$env:WINDY_API_KEY = "your_windy_api_key"
python -m uvicorn backend.app.main:app --reload --port 8000
```

後端 API：

- `GET /api/temperature/latest`：最新正規化站點資料
- `GET /api/temperature/geojson`：Leaflet/GeoJSON 資料
- `GET /api/temperature/stations/{station_id}`：單站詳細資料
- `GET /api/health`：服務健康狀態

有 `WINDY_API_KEY` 且目前網域已在 Windy 後台授權時，前端會初始化 Windy Map Forecast API；本機 `localhost` / `127.0.0.1` 預設使用 OpenStreetMap，避免未授權網域造成頁面錯誤。部署時請將正式網域加入 Windy API key 的 allowed domains。CWA 金鑰只在後端環境變數中使用，不會回傳給瀏覽器。

### 3. 執行自動化測試
驗證整個氣象資料處理管線與 SQLite 冪等性：
```bash
python -m unittest tests/test_pipeline.py
```

---

## 💡 功能特色解說

### 1. 雙模式運作（即時 API / 本地示範資料）
- **即時模式**：於側邊欄輸入 CWA API Key，點擊「🔄 同步資料」即可由氣象署即時載入全台最新一週預報。
- **示範模式**：若未填寫 API Key 或處於離線環境，系統自動載入 `data/sample_cwa_weather.json`，保證所有地圖、圖表與 SQL 查詢功能均可順暢展示。

### 2. SQLite 資料庫設計與防重複機制
資料表結構如下：
```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    mint REAL NOT NULL,
    maxt REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regionName, dataDate)
);
```
寫入邏輯使用 `ON CONFLICT(regionName, dataDate) DO UPDATE`，確保重複更新時不會新增冗餘資料，保持資料庫乾淨嚴謹。

### 3. Folium 互動地圖溫度色階
地圖根據各地當日平均氣溫動態著色：
- 🔵 **涼冷**：`< 20°C`
- 🟢 **舒適**：`20 ~ 25°C`
- 🟡 **溫暖**：`25 ~ 30°C`
- 🔴 **炎熱**：`> 30°C`

---

## 🤝 版本管理與 Git / GitHub 整合 (步驟 21)

若需將專案備份或提交至 GitHub：
```bash
# 1. 初始化 Git 倉庫
git init

# 2. 加入所有檔案
git add .

# 3. 提交第一個版本
git commit -m "feat: Taiwan Weather Forecast initial release (CWA x SQLite x Streamlit x Folium)"

# 4. 關聯至您的遠端 GitHub 儲存庫
git branch -M main
git remote add origin https://github.com/<your-username>/HW10-Taiwan-Weather.git
git push -u origin main
```

---

## 🌟 致謝
- 課程講師：**煥哥 (Huan-Ge)**
- 開發實踐：**Antigravity × Gemini × Vibe Coding**
- 氣象資料來源：**交通部中央氣象署 (CWA) 開放資料平台**
