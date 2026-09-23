"""
Taiwan Weather Forecast Web App
從氣象資料到互動式天氣預報應用 (CWA API x JSON x Python x SQLite x Streamlit)

微課程步驟全整合：
- 步驟 1-7: CWA API 資料取得、JSON 解析、Pandas 資料整理
- 步驟 8-10, 12, 20: SQLite 資料庫儲存、查詢驗證、防重複插入機制
- 步驟 11, 13-16: Streamlit 互動操作、地區選擇、MinT/MaxT 折線圖、一週資料表
- 步驟 17-19: Folium 台灣互動地圖視覺化、日期切換、溫度分級顏色
- 步驟 21-24: 成果展示、SQL 驗證器、延伸應用與學習地圖
"""

import os
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from src.cwa_api import get_weather_dataframe
from src.db import (
    init_db,
    insert_or_update_forecasts,
    get_distinct_regions,
    get_distinct_dates,
    get_forecast_by_region,
    get_forecast_by_date,
    get_all_forecasts,
    execute_custom_sql,
    get_db_stats,
    DEFAULT_DB_PATH
)
from src.visualizer import (
    create_taiwan_weather_map,
    create_temperature_chart,
    get_temperature_color,
    get_temperature_level_label
)

# 1. 頁面設定
st.set_page_config(
    page_title="Taiwan Weather Forecast | 台灣天氣預報儀表板",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 精緻客製化 CSS 樣式 (符合微課程與現代 Web 設計美學)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 頂部 Hero 區塊 */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0369A1 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
        color: #F8FAFC;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-top: 6px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
    }
    .tech-badge {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #38BDF8;
    }

    /* 指標卡 Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #0284C7;
        margin-top: 2px;
        font-weight: 500;
    }

    /* 狀態標籤 */
    .status-badge-api {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-sample {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    /* 說明區塊 */
    .info-box {
        background: #F8FAFC;
        border-left: 4px solid #0284C7;
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 18px;
        font-size: 0.9rem;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)


# 3. 初始化資料庫與工作狀態
init_db(DEFAULT_DB_PATH)

if "db_initialized" not in st.session_state:
    # 首次啟動：自動載入預設示範資料以確保開箱即可瀏覽
    stats = get_db_stats(DEFAULT_DB_PATH)
    if stats["total_rows"] == 0:
        df, is_sample, msg = get_weather_dataframe()
        insert_or_update_forecasts(df, DEFAULT_DB_PATH)
        st.session_state["is_sample"] = is_sample
        st.session_state["status_message"] = msg
    else:
        st.session_state["is_sample"] = True
        st.session_state["status_message"] = "已成功連接現有 SQLite 資料庫。"
    st.session_state["db_initialized"] = True


# 4. 側邊欄控制與設定 (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/partly-cloudy-day.png", width=64)
    st.markdown("### 🌤️ **氣象資料同步中心**")
    st.caption("CWA API × SQLite 資料庫整合控制台")
    
    st.markdown("---")
    
    # 步驟 3: 中央氣象署 API Key 設定
    api_key_input = st.text_input(
        "🔑 **CWA API 授權金鑰 (API Key)**",
        value="",
        type="password",
        help="輸入中央氣象署氣象資料開放平台之授權碼 (若未提供則預設使用內建示範資料)"
    )
    
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        sync_button = st.button("🔄 同步資料", use_container_width=True, type="primary")
    with col_btn2:
        reset_demo = st.button("📦 示範資料", use_container_width=True)

    if sync_button:
        with st.spinner("正在向資料源請求天氣資料並寫入 SQLite 資料庫..."):
            try:
                new_df, is_sample, msg = get_weather_dataframe(api_key=api_key_input)
                rows_updated = insert_or_update_forecasts(new_df, DEFAULT_DB_PATH)
                st.session_state["is_sample"] = is_sample
                st.session_state["status_message"] = msg
                st.toast(f"✅ 成功更新 {rows_updated} 筆氣象資料至 SQLite！", icon="🎉")
            except Exception as e:
                st.error(f"同步失敗: {str(e)}")

    if reset_demo:
        with st.spinner("正在重置為本地示範資料..."):
            new_df, is_sample, msg = get_weather_dataframe(api_key=None)
            insert_or_update_forecasts(new_df, DEFAULT_DB_PATH)
            st.session_state["is_sample"] = is_sample
            st.session_state["status_message"] = msg
            st.toast("✅ 已載入本地示範氣象預報資料！", icon="📦")

    st.markdown("---")
    
    # 資料狀態資訊
    db_stats = get_db_stats(DEFAULT_DB_PATH)
    is_sample_mode = st.session_state.get("is_sample", True)
    
    if not is_sample_mode:
        st.markdown('<span class="status-badge-api">🟢 連接即時 CWA API</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-sample">🟡 使用示範氣象資料庫</span>', unsafe_allow_html=True)

    st.write(f"**資料庫位置**：`data/weather.db`")
    st.write(f"**總記錄筆數**：`{db_stats['total_rows']}` 筆")
    st.write(f"**涵蓋地區數**：`{db_stats['region_count']}` 個分區")
    st.write(f"**預報日期區間**：`{db_stats['date_range']}`")
    st.write(f"**最後更新時間**：`{db_stats['last_updated']}`")
    
    st.markdown("---")
    st.markdown("#### 💡 **微課程小提示**")
    st.caption("本系統遵循步驟 20「重複執行不重複插入」，即使頻繁點擊同步按鈕，SQLite 亦會透過 `ON CONFLICT DO UPDATE` 保障資料一致性與防重複。")


# 5. 主頁面 Hero Header
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">🌤️ Taiwan Weather Forecast 台灣天氣預報系統</h1>
    <div class="hero-subtitle">
        <span>從氣象資料到互動式天氣預報應用</span>
        <span class="tech-badge">CWA API</span>
        <span class="tech-badge">JSON</span>
        <span class="tech-badge">Python</span>
        <span class="tech-badge">SQLite</span>
        <span class="tech-badge">Streamlit</span>
        <span class="tech-badge">Folium</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 顯示當前狀態訊息通知
if "status_message" in st.session_state:
    st.info(f"ℹ️ **資料庫運作狀態**：{st.session_state['status_message']}")


# 6. 讀取現有資料並計算全台當日天氣焦點 (KPI Metrics)
distinct_dates = get_distinct_dates(DEFAULT_DB_PATH)
distinct_regions = get_distinct_regions(DEFAULT_DB_PATH)

if not distinct_dates or not distinct_regions:
    st.warning("目前資料庫尚無氣象資料，請於側邊欄點選「🔄 同步資料」或「📦 示範資料」。")
    st.stop()

# 預設以第一天作為重點指標基準日
default_date = distinct_dates[0]
today_df = get_forecast_by_date(default_date, DEFAULT_DB_PATH)

if not today_df.empty:
    max_row = today_df.loc[today_df["maxt"].idxmax()]
    min_row = today_df.loc[today_df["mint"].idxmin()]
    today_df["temp_diff"] = today_df["maxt"] - today_df["mint"]
    max_diff_row = today_df.loc[today_df["temp_diff"].idxmax()]
    avg_national = round((today_df["mint"].mean() + today_df["maxt"].mean()) / 2.0, 1)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🔥 全台今日最高溫</div>
            <div class="metric-value" style="color: #EF4444;">{max_row['maxt']}°C</div>
            <div class="metric-sub">📍 {max_row['regionName']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">❄️ 全台今日最低溫</div>
            <div class="metric-value" style="color: #2563EB;">{min_row['mint']}°C</div>
            <div class="metric-sub">📍 {min_row['regionName']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🌡️ 全台今日平均溫</div>
            <div class="metric-value" style="color: #10B981;">{avg_national}°C</div>
            <div class="metric-sub">涵蓋 {len(today_df)} 個主要分區</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 最大日夜溫差</div>
            <div class="metric-value" style="color: #F59E0B;">{round(max_diff_row['temp_diff'], 1)}°C</div>
            <div class="metric-sub">📍 {max_diff_row['regionName']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)


# 7. 主要功能分頁 (Tabs)
tab_map, tab_trend, tab_sql, tab_guide = st.tabs([
    "🗺️ **台灣地圖視覺化 (Folium)**",
    "📈 **地區一週趨勢 (圖表與表格)**",
    "💾 **SQLite 資料庫查詢驗證**",
    "🎓 **微課程 24 步驟與學習地圖**"
])


# ==============================================================================
# TAB 1: 台灣地圖視覺化 (對應步驟 17, 18, 19)
# ==============================================================================
with tab_map:
    st.subheader("🗺️ 全台氣象互動地圖 (Folium + Streamlit)")
    st.caption("依據步驟 17-18：選擇預報日期，地圖動態呈現各區氣溫標記，並以顏色階層標示溫度分級。")

    col_select_date, col_map_info = st.columns([1, 2])
    with col_select_date:
        selected_date = st.selectbox(
            "📅 **選擇預報日期 (Select Date)**",
            options=distinct_dates,
            index=0,
            key="map_date_select"
        )
    with col_map_info:
        st.markdown("""
        <div style="font-size: 0.88rem; color: #475569; padding-top: 18px;">
            💡 <b>操作說明</b>：點擊地圖圓圈標記可展開氣溫卡；右下方附有 4 段平均溫度顏色階層圖例 (<20°C 藍、20-25°C 綠、25-30°C 橙、>30°C 紅)。
        </div>
        """, unsafe_allow_html=True)

    date_df = get_forecast_by_date(selected_date, DEFAULT_DB_PATH)

    col_map_view, col_table_view = st.columns([1.5, 1])

    with col_map_view:
        if not date_df.empty:
            weather_map = create_taiwan_weather_map(date_df, selected_date)
            st_folium(weather_map, width=700, height=480, returned_objects=[])
        else:
            st.warning("查無該日期之氣象資料。")

    with col_table_view:
        st.markdown(f"#### 📋 {selected_date} 各區氣溫總覽")
        if not date_df.empty:
            display_date_df = date_df.copy()
            display_date_df["平均溫 (°C)"] = ((display_date_df["mint"] + display_date_df["maxt"]) / 2.0).round(1)
            display_date_df["溫階狀態"] = display_date_df["平均溫 (°C)"].apply(get_temperature_level_label)
            
            # 格式化呈現
            display_table = display_date_df.rename(columns={
                "regionName": "地區名稱",
                "mint": "最低溫 (°C)",
                "maxt": "最高溫 (°C)"
            })[["地區名稱", "最低溫 (°C)", "最高溫 (°C)", "平均溫 (°C)", "溫階狀態"]]

            st.dataframe(
                display_table,
                hide_index=True,
                use_container_width=True,
                height=440
            )


# ==============================================================================
# TAB 2: 地區一週趨勢 (對應步驟 13, 14, 15, 16)
# ==============================================================================
with tab_trend:
    st.subheader("📈 區域氣溫趨勢分析 (Taiwan Weather Forecast)")
    st.caption("依據步驟 13-16：下拉選單選取特定區域，繪製一週最高溫與最低溫走勢折線圖並列出數據清單。")

    col_reg_select, col_reg_summary = st.columns([1, 2])
    with col_reg_select:
        selected_region = st.selectbox(
            "📍 **下拉選單選擇地區 (Select Region)**",
            options=distinct_regions,
            index=0 if "北部地區" not in distinct_regions else distinct_regions.index("北部地區"),
            key="region_select_trend"
        )

    region_df = get_forecast_by_region(selected_region, DEFAULT_DB_PATH)

    if not region_df.empty:
        with col_reg_summary:
            r_max = region_df["maxt"].max()
            r_min = region_df["mint"].min()
            r_avg = round((region_df["mint"].mean() + region_df["maxt"].mean()) / 2.0, 1)
            st.markdown(f"""
            <div style="padding-top: 14px; font-size: 0.95rem; color: #1E293B;">
                📌 <b>{selected_region}</b> 一週預報極值：最高溫 <b style="color: #EF4444;">{r_max}°C</b>，最低溫 <b style="color: #2563EB;">{r_min}°C</b>，整週平均溫 <b>{r_avg}°C</b>。
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        # 步驟 14: 繪製折線圖
        st.markdown(f"#### 📈 走勢折線圖 (MinT vs MaxT)")
        chart = create_temperature_chart(region_df, selected_region)
        st.altair_chart(chart, use_container_width=True)

        # 步驟 15: 顯示資料表格
        st.markdown("#### 📊 一週詳細資料表格")
        view_df = region_df.copy()
        view_df["日溫差 (°C)"] = (view_df["maxt"] - view_df["mint"]).round(1)
        view_df["平均溫 (°C)"] = ((view_df["maxt"] + view_df["mint"]) / 2.0).round(1)
        
        formatted_df = view_df.rename(columns={
            "dataDate": "日期 (Date)",
            "mint": "最低溫 MinT (°C)",
            "maxt": "最高溫 MaxT (°C)"
        })[["日期 (Date)", "最低溫 MinT (°C)", "最高溫 MaxT (°C)", "日溫差 (°C)", "平均溫 (°C)"]]

        st.dataframe(
            formatted_df,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning(f"目前無 {selected_region} 的氣溫預報資料。")


# ==============================================================================
# TAB 3: SQLite 資料庫查詢驗證 (對應步驟 8, 9, 10, 12, 20)
# ==============================================================================
with tab_sql:
    st.subheader("💾 SQLite 資料庫檢查與 SQL 查詢驗證")
    st.caption("依據步驟 8-10：驗證資料庫設計 `TemperatureForecasts` 表結構與 SQL 查詢語法。")

    st.markdown("""
    <div class="info-box">
        <b>資料表設計 (Schema)</b>：<br/>
        <code>TemperatureForecasts (id INTEGER PRIMARY KEY, regionName TEXT, dataDate TEXT, mint REAL, maxt REAL, updated_at TIMESTAMP, UNIQUE(regionName, dataDate))</code><br/>
        已落實<b>防重複插入機制 (Idempotency)</b>，重複呼叫寫入不會產生冗餘資料。
    </div>
    """, unsafe_allow_html=True)

    # 快捷示範 SQL (對應投影片步驟 10 範例)
    st.markdown("##### 🔍 常用驗證 SQL 快捷查詢")
    col_q1, col_q2, col_q3 = st.columns(3)
    
    preset_query = None
    with col_q1:
        if st.button("查詢所有地區 (SELECT DISTINCT)", use_container_width=True):
            preset_query = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName;"
    with col_q2:
        if st.button("查詢中部地區預報 (WHERE regionName='中部地區')", use_container_width=True):
            preset_query = "SELECT dataDate, mint, maxt FROM TemperatureForecasts WHERE regionName = '中部地區' ORDER BY dataDate;"
    with col_q3:
        if st.button("查詢資料庫最新前 15 筆", use_container_width=True):
            preset_query = "SELECT id, regionName, dataDate, mint, maxt, updated_at FROM TemperatureForecasts LIMIT 15;"

    sql_input = st.text_area(
        "輸入自訂 SQL 查詢 (僅限 SELECT 讀取語法)：",
        value=preset_query if preset_query else "SELECT id, regionName, dataDate, mint, maxt, updated_at FROM TemperatureForecasts LIMIT 10;",
        height=90
    )

    if st.button("▶️ 執行 SQL 查詢", type="primary"):
        try:
            query_result = execute_custom_sql(sql_input, DEFAULT_DB_PATH)
            st.success(f"查詢成功！共返回 {len(query_result)} 筆紀錄。")
            st.dataframe(query_result, use_container_width=True)
        except Exception as e:
            st.error(f"SQL 執行出錯: {str(e)}")


# ==============================================================================
# TAB 4: 微課程 24 步驟與學習地圖 (對應步驟 1, 2, 21, 22, 23, 24)
# ==============================================================================
with tab_guide:
    st.subheader("🎓 AI 創新微課程：Taiwan Weather Forecast 學習地圖")
    st.caption("從氣象資料到互動式天氣預報應用 | 用程式探索天氣，用資料看見台灣，用 AI 實現更多可能！")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("""
        #### 🗺️ **24 步驟學習歷程檢視**
        1. **課程介紹**：AI × 資料 × 天氣 × 實作導向
        2. **台灣的天氣與生活**：氣象對生活與商業決策的重要性
        3. **中央氣象署 CWA Open Data 平台**：註冊帳號、取得 API Key
        4. **API 資料取得**：使用 Python Requests 取得 JSON 回應
        5. **JSON 資料結構解析**：定位 locations 與 weatherElement (MinT / MaxT)
        6. **提取最高與最低氣溫**：整理為結構化數據
        7. **資料整理與預覽**：使用 Pandas 觀察 DataFrame
        8. **建立 SQLite 資料庫**：建立 data.db 與連線
        9. **資料庫設計**：TemperatureForecasts 表結構定義
        10. **查詢資料驗證**：使用 SQL 檢查與過濾資料
        11. **Streamlit 入門**：快速建立 Web App
        12. **從資料庫讀取資料**：使用 SQL 與 Pandas 整合
        13. **下拉選單選擇地區**：Selectbox 互動操作
        14. **繪製折線圖**：一週最高與最低溫趨勢視覺化
        15. **顯示資料表格**：清楚呈現數據表格
        16. **整合 Web App 介面**：模組整合與使用者體驗
        17. **進階：台灣地圖視覺化**：Folium 圓點標記與溫度色階
        18. **選擇日期顯示地圖**：日期切換與動態地圖刷新
        19. **完整成果展示**：Taiwan Weather Dashboard 儀表板
        20. **程式碼品質與優化**：模組化、防重複插入 (Idempotency)、錯誤處理
        21. **專案上傳至 GitHub**：版本管理、Git Remote 與備份
        22. **延伸應用與想法**：Line Bot、行程建議、農業防災、AI 結合
        23. **回顧與重點整理**：技術串聯總複習
        24. **下一步：繼續探索**：更多 Open Data 與商業級專案
        """)

    with col_g2:
        st.markdown("""
        #### 🚀 **延伸應用與 AI Vibe Coding 實踐**
        - 🤖 **結合 AI 氣象解說員**：利用 Gemini 2.0 依據資料庫氣溫，自動生成當日穿搭、帶傘提醒與行車叮嚀。
        - 📲 **LINE 官方帳號推播**：整合 Line Messaging API，每日早晨自動推播用戶所在地的最高最低溫。
        - 🌾 **智慧農業與防災預警**：當預報溫差過大或連續低溫時，觸發農作物防寒警報通知。
        - ✈️ **旅遊行程智慧規劃**：配合週末天氣走勢，推薦最合適出遊的縣市與景點。
        
        ---
        #### 📦 **版本管理 (Git & GitHub Ready)**
        本專案已備齊：
        - `.gitignore` (自動排除快取與環境檔)
        - `requirements.txt` (相依套件清單)
        - `README.md` (完整教學與執行說明)
        - 模組化目錄架構：`src/`、`data/`、`app.py`
        """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 0.85rem; padding: 12px 0;">
    🌟 <b>Code Smarter, Build a Better Tomorrow!</b> | 煥哥 × AI Coding Agent (Antigravity × Gemini × GitHub)
</div>
""", unsafe_allow_html=True)
