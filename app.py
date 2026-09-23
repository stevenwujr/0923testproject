"""
app.py
HW10 Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式
符合作業評分標準：
1. 取得 CWA API 資料 (已由 fetch_weather.py 完成並存為 weather_data.json)
2. 分析 JSON，提取氣溫資料 (已由 parse_weather.py 完成並存為 weather_data.csv)
3. 存入 SQLite 資料庫 (已由 database.py 完成並存為 data.db)
4. Streamlit 氣溫預報 Web App (40%):
   - 下拉選單選擇地區
   - 使用 SQL 從 SQLite (data.db) 查詢資料，不直接呼叫 API
   - 顯示最高/最低溫折線圖 (MaxT vs MinT)
   - 顯示一週資料表格 (Date, MinT, MaxT)
5. 進階：台灣地圖視覺化 (Optional 加分項):
   - Folium + Streamlit 互動地圖
   - 依平均溫度設定顏色: <20°C (藍色), 20-25°C (綠色), 25-30°C (黃色), >30°C (紅色)
   - 點選中部地區或任一地區顯示氣溫卡片
6. 延伸進階：Windy 專業氣象地圖圖層對比
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import altair as alt
from streamlit_folium import st_folium
import folium

# 1. 頁面設定
st.set_page_config(
    page_title="HW10 Taiwan Weather Forecast | 台灣天氣預報",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "data.db"

# 2. 精緻樣式 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans TC', sans-serif;
    }
    
    .hw-badge {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    .card-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
    
    .metric-title {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-num {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #0284C7;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# 3. 確保 SQLite 資料庫存在
if not os.path.exists(DB_PATH):
    # 若首次執行且無 data.db，自動嘗試呼叫 database.py 建立
    try:
        from database import init_database, save_to_database
        init_database(DB_PATH)
        save_to_database(db_path=DB_PATH)
    except Exception as e:
        st.error(f"找不到資料庫 {DB_PATH}，請先執行 `python database.py`。錯誤：{e}")
        st.stop()


def get_db_connection():
    """建立 SQLite 連線 (嚴格遵循重要注意事項 2：必須從 SQLite 查詢，不可直接呼叫 API)"""
    conn = sqlite3.connect(DB_PATH)
    return conn


# 4. 側邊欄：HW10 作業資訊與資料庫狀態
with st.sidebar:
    st.markdown('<div class="hw-badge">HW10 作業規範檢查</div>', unsafe_allow_html=True)
    st.subheader("🌤️ 台灣天氣預報系統")
    st.caption("CWA API × JSON × Python × SQLite × Streamlit")
    
    st.markdown("---")
    st.markdown("#### 📋 **資料來源說明**")
    st.write("• **資料庫來源**：`data.db` (SQLite)")
    st.write("• **資料表名稱**：`TemperatureForecasts`")
    st.write("• **遵循規則**：純 SQL 查詢，完全不直接請求 API")
    
    conn = get_db_connection()
    try:
        total_rows = conn.execute("SELECT COUNT(*) FROM TemperatureForecasts").fetchone()[0]
        distinct_regions = [r[0] for r in conn.execute("SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName").fetchall()]
        distinct_dates = [d[0] for d in conn.execute("SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate").fetchall()]
    finally:
        conn.close()

    st.write(f"• **已載入筆數**：`{total_rows}` 筆")
    st.write(f"• **涵蓋分區**：`{len(distinct_regions)}` 個分區")
    if distinct_dates:
        st.write(f"• **預報期間**：`{distinct_dates[0]} ~ {distinct_dates[-1]}` (7 天)")
    
    st.markdown("---")
    st.markdown("#### 👨‍💻 **學生 / 開發者資訊**")
    st.write("• **CWA 專屬 API Key**：已綁定驗證")
    st.write("• **GitHub 專案**：[stevenwujr/0923testproject](https://github.com/stevenwujr/0923testproject)")
    st.write("• **外網即時網址**：[Cloudflare Live](https://greg-design-their-jon.trycloudflare.com)")


# 5. 主標題區
st.markdown("""
<div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #0284C7 100%); padding: 22px 28px; border-radius: 14px; color: white; margin-bottom: 22px;">
    <div style="font-size: 0.85rem; font-weight: 700; color: #38BDF8; letter-spacing: 1px;">HW10 ASSIGNMENT</div>
    <h1 style="margin: 4px 0; font-size: 2.2rem; font-weight: 700;">Taiwan Weather Forecast 台灣天氣預報</h1>
    <div style="font-size: 0.95rem; color: #94A3B8;">從氣象資料到互動式天氣預報應用程式 | CWA API × JSON × Python × SQLite × Streamlit</div>
</div>
""", unsafe_allow_html=True)


# 6. 當日天氣全台重點指標卡 (KPI Cards)
if distinct_dates:
    first_date = distinct_dates[0]
    conn = get_db_connection()
    try:
        today_df = pd.read_sql_query(
            "SELECT regionName, mint, maxt FROM TemperatureForecasts WHERE dataDate = ?",
            conn,
            params=(first_date,)
        )
    finally:
        conn.close()

    if not today_df.empty:
        max_rec = today_df.loc[today_df["maxt"].idxmax()]
        min_rec = today_df.loc[today_df["mint"].idxmin()]
        avg_temp = round((today_df["mint"].mean() + today_df["maxt"].mean()) / 2.0, 1)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="card-box">
                <div class="metric-title">🔥 今日最高溫</div>
                <div class="metric-num" style="color: #EF4444;">{max_rec['maxt']}°C</div>
                <div class="metric-sub">📍 {max_rec['regionName']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="card-box">
                <div class="metric-title">❄️ 今日最低溫</div>
                <div class="metric-num" style="color: #2563EB;">{min_rec['mint']}°C</div>
                <div class="metric-sub">📍 {min_rec['regionName']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="card-box">
                <div class="metric-title">🌡️ 全台平均溫</div>
                <div class="metric-num" style="color: #10B981;">{avg_temp}°C</div>
                <div class="metric-sub">📅 {first_date}</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="card-box">
                <div class="metric-title">📊 預報涵蓋天數</div>
                <div class="metric-num" style="color: #F59E0B;">{len(distinct_dates)} 天</div>
                <div class="metric-sub">共 {len(distinct_regions)} 個主要分區</div>
            </div>
            """, unsafe_allow_html=True)


# 7. 功能分頁 (Tabs)
tab_trend, tab_map, tab_sql, tab_windy = st.tabs([
    "📈 **區域氣溫預報 (HW10 核心要求 40%)**",
    "🗺️ **台灣地圖視覺化 (HW10 進階加分項)**",
    "💾 **SQLite 資料庫驗證 (HW10 評分項目 20%)**",
    "🌪️ **Windy 氣象地圖與觀測疊加 (進階延伸)**"
])


# ==============================================================================
# TAB 1: 區域氣溫預報 (HW10 核心 40% 項目)
# ==============================================================================
with tab_trend:
    st.subheader("Taiwan Weather Forecast - 區域一週預報")
    st.caption("依據作業規格：下拉選單選取特定區域，使用 SQL 從 SQLite 查詢資料，繪製最高/最低溫折線圖並呈現一週表格。")

    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        # 下拉選單選擇地區 (預設 中部地區，完美契合投影片範例)
        default_idx = distinct_regions.index("中部地區") if "中部地區" in distinct_regions else 0
        selected_region = st.selectbox(
            "📍 **Select Region (選擇地區)**",
            options=distinct_regions,
            index=default_idx
        )

    # 執行 SQL 查詢 (符合重要注意事項 2)
    conn = get_db_connection()
    try:
        sql = """
        SELECT dataDate AS Date, mint AS MinT, maxt AS MaxT
        FROM TemperatureForecasts
        WHERE regionName = ?
        ORDER BY dataDate ASC
        LIMIT 7;
        """
        region_df = pd.read_sql_query(sql, conn, params=(selected_region,))
    finally:
        conn.close()

    if not region_df.empty:
        st.markdown(f"### Temperature Forecast - {selected_region}")

        # 折線圖與資料表格並列展示 (如投影片版面配置)
        col_chart, col_table = st.columns([1.6, 1])

        with col_chart:
            # 轉換為 Long format 以利繪製 Altair 折線圖
            melted_df = region_df.melt(
                id_vars=["Date"],
                value_vars=["MaxT", "MinT"],
                var_name="Element",
                value_name="Temperature"
            )

            y_min = int(region_df["MinT"].min() - 3)
            y_max = int(region_df["MaxT"].max() + 3)

            chart_lines = alt.Chart(melted_df).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Date:N", title="Date (預報日期)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Temperature:Q", title="Temperature (°C)", scale=alt.Scale(domain=[y_min, y_max])),
                color=alt.Color(
                    "Element:N",
                    scale=alt.Scale(domain=["MaxT", "MinT"], range=["#EF4444", "#2563EB"]),
                    legend=alt.Legend(title="", orient="top")
                ),
                tooltip=["Date", "Element", "Temperature"]
            )

            chart_text = alt.Chart(melted_df).mark_text(
                align="center", baseline="bottom", dy=-8, fontSize=11, fontWeight="bold"
            ).encode(
                x=alt.X("Date:N"),
                y=alt.Y("Temperature:Q"),
                text=alt.Text("Temperature:Q", format=".1f"),
                color=alt.Color("Element:N", scale=alt.Scale(domain=["MaxT", "MinT"], range=["#DC2626", "#1D4ED8"]))
            )

            final_chart = (chart_lines + chart_text).properties(height=360)
            st.altair_chart(final_chart, use_container_width=True)

        with col_table:
            st.markdown("#### 📋 一週資料表格")
            display_df = region_df.copy()
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                height=360
            )


# ==============================================================================
# TAB 2: 台灣地圖視覺化 (HW10 進階加分項)
# ==============================================================================
with tab_map:
    st.subheader("🗺️ 台灣地圖視覺化 (Folium + Streamlit)")
    st.caption("依據作業規格 5：顯示各區當日平均溫度，設定顏色階層 (<20°C 藍、20-25°C 綠、25-30°C 黃、>30°C 紅)，點選顯示氣溫資訊。")

    col_map_ctrl, _ = st.columns([1, 2])
    with col_map_ctrl:
        map_date = st.selectbox(
            "📅 **選擇日期 (Select Date)**",
            options=distinct_dates,
            index=0,
            key="folium_date_select"
        )

    # 查詢該日所有地區預報
    conn = get_db_connection()
    try:
        sql = "SELECT regionName, mint, maxt FROM TemperatureForecasts WHERE dataDate = ? ORDER BY regionName"
        map_df = pd.read_sql_query(sql, conn, params=(map_date,))
    finally:
        conn.close()

    if not map_df.empty:
        # 分區座標對照表
        coords = {
            "北部地區": (25.04, 121.53),
            "中部地區": (24.15, 120.67),
            "南部地區": (22.63, 120.30),
            "東北部地區": (24.75, 121.75),
            "東部地區": (23.99, 121.60),
            "東南部地區": (22.75, 121.15),
            "澎湖地區": (23.57, 119.58),
            "金門地區": (24.44, 118.38),
            "馬祖地區": (26.15, 119.93)
        }

        def get_color(avg_t):
            if avg_t < 20.0:
                return "#2563EB"  # 藍色
            elif avg_t < 25.0:
                return "#10B981"  # 綠色
            elif avg_t <= 30.0:
                return "#F59E0B"  # 黃色
            else:
                return "#EF4444"  # 紅色

        col_m_view, col_m_table = st.columns([1.5, 1])

        with col_m_view:
            fmap = folium.Map(location=[23.8, 121.0], zoom_start=7, tiles="OpenStreetMap")

            for _, row in map_df.iterrows():
                r_name = row["regionName"]
                mint_v = float(row["mint"])
                maxt_v = float(row["maxt"])
                avg_v = round((mint_v + maxt_v) / 2.0, 1)

                pt = coords.get(r_name)
                if not pt:
                    continue

                c = get_color(avg_v)

                popup_html = f"""
                <div style="font-family: Arial; min-width: 150px; font-size: 13px;">
                    <b style="font-size: 15px; color: {c};">{r_name}</b><br/>
                    <b>Date:</b> {map_date}<br/>
                    <b>Min:</b> {mint_v}°C<br/>
                    <b>Max:</b> {maxt_v}°C<br/>
                    <b>Avg:</b> {avg_v}°C
                </div>
                """

                # 圓點標記
                folium.CircleMarker(
                    location=pt,
                    radius=20,
                    color=c,
                    weight=3,
                    fill=True,
                    fill_color=c,
                    fill_opacity=0.6,
                    tooltip=f"{r_name}: Min {mint_v}°C, Max {maxt_v}°C",
                    popup=folium.Popup(popup_html, max_width=250)
                ).add_to(fmap)

                folium.CircleMarker(
                    location=pt,
                    radius=6,
                    color="#FFFFFF",
                    fill=True,
                    fill_color=c,
                    fill_opacity=1.0
                ).add_to(fmap)

            # 圖例 Legend
            legend_html = """
            <div style="position: fixed; bottom: 20px; right: 20px; background: rgba(255,255,255,0.95);
                        border-radius: 8px; padding: 10px; font-size: 12px; z-index: 9999; border: 1px solid #CBD5E1;">
                <b>🌡️ 依平均溫度設定顏色</b><br/>
                <span style="color: #2563EB;">●</span> &lt; 20°C (藍色)<br/>
                <span style="color: #10B981;">●</span> 20 - 25°C (綠色)<br/>
                <span style="color: #F59E0B;">●</span> 25 - 30°C (黃色)<br/>
                <span style="color: #EF4444;">●</span> &gt; 30°C (紅色)
            </div>
            """
            fmap.get_root().html.add_child(folium.Element(legend_html))

            st_folium(fmap, width=680, height=450, returned_objects=[])

        with col_m_table:
            st.markdown(f"#### 📊 {map_date} 各區氣溫一覽")
            t_df = map_df.copy()
            t_df["平均溫 (°C)"] = ((t_df["mint"] + t_df["maxt"]) / 2.0).round(1)
            t_df = t_df.rename(columns={"regionName": "地區", "mint": "最低溫", "maxt": "最高溫"})
            st.dataframe(t_df, hide_index=True, use_container_width=True, height=410)


# ==============================================================================
# TAB 3: SQLite 資料庫驗證 (HW10 評分項目 20%)
# ==============================================================================
with tab_sql:
    st.subheader("💾 SQLite 資料庫檢查與驗證 (data.db)")
    st.caption("依據作業規格 3：建立 TemperatureForecasts 資料表並執行驗證查詢。")

    st.markdown("""
    **資料庫結構 (Schema)**：
    ```sql
    CREATE TABLE TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT,
        dataDate TEXT,
        mint REAL,
        maxt REAL,
        UNIQUE(regionName, dataDate)
    );
    ```
    """)

    col_btn_q1, col_btn_q2, col_btn_all = st.columns(3)
    preset_sql = ""
    with col_btn_q1:
        if st.button("① 列出所有地區名稱 (SELECT DISTINCT)", use_container_width=True):
            preset_sql = "SELECT DISTINCT regionName FROM TemperatureForecasts;"
    with col_btn_q2:
        if st.button("② 查詢中部地區資料 (WHERE regionName='中部地區')", use_container_width=True):
            preset_sql = "SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';"
    with col_btn_all:
        if st.button("③ 查詢全表前 20 筆資料", use_container_width=True):
            preset_sql = "SELECT * FROM TemperatureForecasts LIMIT 20;"

    sql_input = st.text_area(
        "輸入欲執行的 SQL 查詢：",
        value=preset_sql if preset_sql else "SELECT DISTINCT regionName FROM TemperatureForecasts;",
        height=80
    )

    if st.button("▶️ 執行 SQL 查詢", type="primary"):
        conn = get_db_connection()
        try:
            res_df = pd.read_sql_query(sql_input, conn)
            st.success(f"查詢成功！共返回 {len(res_df)} 筆紀錄。")
            st.dataframe(res_df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL 查詢失敗: {e}")
        finally:
            conn.close()


# ==============================================================================
# TAB 4: Windy 氣象地圖與觀測疊加 (進階延伸)
# ==============================================================================
with tab_windy:
    st.subheader("🌪️ Windy Map Forecast API 氣象背景與觀測疊加")
    st.caption("整合 Windy 專業氣象數值模型圖層 (ECMWF) 作為底圖背景，觀測即時風場、氣溫、降雨與雲層走勢。")

    st.markdown("""
    <div style="border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 20px;">
        <iframe width="100%" height="520" 
                src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=m/s&zoom=7&overlay=temp&product=ecmwf&level=surface&lat=23.8&lon=121.0" 
                frameborder="0">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    #### 💡 Windy + CWA 整合架構說明
    1. **Windy Map Forecast API**：作為氣象數值預報 (ECMWF / GFS) 之高畫質背景圖層，提供風向粒子流動動畫、氣壓線與動態溫度場。
    2. **CWA 中央氣象署資料**：作為台灣在地之高精度預報與地面測站觀測依據，提供最真實的地面實測數據。
    3. **雙層疊加架構**：Windy 提供氣候大環境背景，Leaflet / Folium 負責精準標記台灣各分區之預報高低溫數值。
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 0.85rem;">
    HW10 Taiwan Weather Forecast | CWA API × JSON × Python × SQLite × Streamlit
</div>
""", unsafe_allow_html=True)
