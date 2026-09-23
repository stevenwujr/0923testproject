"""
visualizer.py
視覺化模組：提供 Folium 台灣互動地圖與 Altair 氣溫折線圖
對應微課程步驟：
- 步驟 14: 繪製折線圖 (一週最高與最低氣溫)
- 步驟 17: 進階：台灣地圖視覺化 (Folium 圓點標記、平均溫度顏色階層)
- 步驟 18: 選擇日期顯示地圖 (互動式天氣地圖)
- 步驟 19: 完整成果展示
"""

import folium
from folium import plugins
import pandas as pd
import altair as alt
from typing import Dict, Tuple

# 台灣主要氣象預報分區中心經緯度對照表
REGION_COORDINATES: Dict[str, Tuple[float, float]] = {
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


def get_temperature_color(avg_temp: float) -> str:
    """
    對應步驟 17 之平均溫度顏色階層規範：
    - < 20°C: 藍色 (#2563EB)
    - 20 - 25°C: 綠色 (#10B981)
    - 25 - 30°C: 橙黃色 (#F59E0B)
    - > 30°C: 紅色 (#EF4444)
    """
    if avg_temp < 20.0:
        return "#2563EB"  # 藍色
    elif avg_temp < 25.0:
        return "#10B981"  # 綠色
    elif avg_temp <= 30.0:
        return "#F59E0B"  # 橙黃色
    else:
        return "#EF4444"  # 紅色


def get_temperature_level_label(avg_temp: float) -> str:
    """取得溫度級距文字說明"""
    if avg_temp < 20.0:
        return "涼冷 (< 20°C)"
    elif avg_temp < 25.0:
        return "舒適 (20 ~ 25°C)"
    elif avg_temp <= 30.0:
        return "溫暖 (25 ~ 30°C)"
    else:
        return "炎熱 (> 30°C)"


def create_taiwan_weather_map(date_df: pd.DataFrame, selected_date: str) -> folium.Map:
    """
    建立特定日期的台灣天氣互動地圖。
    
    :param date_df: 包含 ['regionName', 'mint', 'maxt'] 之當日各地氣溫 DataFrame
    :param selected_date: 選擇之日期字串 (YYYY-MM-DD)
    :return: folium.Map 物件
    """
    # 台灣中心視角
    m = folium.Map(
        location=[23.8, 121.0],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True
    )

    for _, row in date_df.iterrows():
        region = str(row["regionName"])
        mint = float(row["mint"])
        maxt = float(row["maxt"])
        avg_temp = round((mint + maxt) / 2.0, 1)

        coords = REGION_COORDINATES.get(region)
        if not coords:
            continue

        color = get_temperature_color(avg_temp)
        level_label = get_temperature_level_label(avg_temp)

        # Popup 卡片設計
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 170px; padding: 6px;">
            <div style="font-size: 15px; font-weight: bold; color: #1E293B; border-bottom: 2px solid {color}; padding-bottom: 4px; margin-bottom: 6px;">
                📍 {region}
            </div>
            <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">📅 日期：{selected_date}</div>
            <div style="font-size: 13px; line-height: 1.6;">
                <div>🔹 <b>最低溫 (MinT)</b>：<span style="color: #2563EB; font-weight: bold;">{mint}°C</span></div>
                <div>🔺 <b>最高溫 (MaxT)</b>：<span style="color: #EF4444; font-weight: bold;">{maxt}°C</span></div>
                <div>🌡️ <b>平均溫</b>：<span style="color: {color}; font-weight: bold;">{avg_temp}°C</span></div>
                <div style="margin-top: 6px; font-size: 11px; padding: 2px 6px; background-color: #F1F5F9; border-radius: 4px; display: inline-block;">
                    狀態：{level_label}
                </div>
            </div>
        </div>
        """

        tooltip_text = f"{region}: {mint}°C ~ {maxt}°C (均溫 {avg_temp}°C)"

        # 繪製外層發光圓圈
        folium.CircleMarker(
            location=coords,
            radius=20,
            color=color,
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.45,
            tooltip=tooltip_text,
            popup=folium.Popup(popup_html, max_width=280)
        ).add_to(m)

        # 繪製中心實心點與地區標籤
        folium.CircleMarker(
            location=coords,
            radius=7,
            color="#FFFFFF",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=1.0,
        ).add_to(m)

    # 建立精緻的圖例 (Legend HTML)
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 25px; 
        right: 25px; 
        width: 175px; 
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 12px;
        font-family: 'Segoe UI', Arial, sans-serif;
        z-index: 9999;
        border: 1px solid #E2E8F0;
    ">
        <div style="font-weight: bold; margin-bottom: 8px; color: #1E293B; font-size: 13px;">🌡️ 平均溫度階層</div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #2563EB; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span>&lt; 20°C (涼冷)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #10B981; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span>20 - 25°C (舒適)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #F59E0B; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span>25 - 30°C (溫暖)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background: #EF4444; width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
            <span>&gt; 30°C (炎熱)</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


def create_temperature_chart(region_df: pd.DataFrame, region_name: str) -> alt.Chart:
    """
    對應步驟 14: 繪製一週最高與最低氣溫折線圖
    
    :param region_df: 包含 ['dataDate', 'mint', 'maxt'] 之特定地區 DataFrame
    :param region_name: 地區名稱 (如 '北部地區')
    :return: Altair Chart 物件
    """
    # 轉換資料格式以利 Altair 雙線繪製 (Melt 成 long format)
    plot_df = region_df.melt(
        id_vars=["dataDate"],
        value_vars=["maxt", "mint"],
        var_name="temp_type",
        value_name="temperature"
    )

    plot_df["指標名稱"] = plot_df["temp_type"].map({
        "maxt": "最高氣溫 (MaxT)",
        "mint": "最低氣溫 (MinT)"
    })

    # 計算 Y 軸合適邊界
    y_min = max(0, int(region_df["mint"].min() - 3))
    y_max = int(region_df["maxt"].max() + 3)

    # 基礎折線
    lines = alt.Chart(plot_df).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("dataDate:N", title="預報日期 (Date)", axis=alt.Axis(labelAngle=0, labelFont="Segoe UI", titleFont="Segoe UI")),
        y=alt.Y("temperature:Q", title="氣溫 (°C)", scale=alt.Scale(domain=[y_min, y_max]), axis=alt.Axis(titleFont="Segoe UI")),
        color=alt.Color(
            "指標名稱:N",
            scale=alt.Scale(
                domain=["最高氣溫 (MaxT)", "最低氣溫 (MinT)"],
                range=["#EF4444", "#2563EB"]
            ),
            legend=alt.Legend(title="氣象指標", orient="top", titleFont="Segoe UI", labelFont="Segoe UI")
        ),
        tooltip=[
            alt.Tooltip("dataDate:N", title="日期"),
            alt.Tooltip("指標名稱:N", title="項目"),
            alt.Tooltip("temperature:Q", title="溫度 (°C)", format=".1f")
        ]
    )

    # 數據點標籤
    text = alt.Chart(plot_df).mark_text(
        align="center",
        baseline="bottom",
        dy=-10,
        fontSize=12,
        fontWeight="bold"
    ).encode(
        x=alt.X("dataDate:N"),
        y=alt.Y("temperature:Q"),
        text=alt.Text("temperature:Q", format=".1f"),
        color=alt.Color(
            "指標名稱:N",
            scale=alt.Scale(
                domain=["最高氣溫 (MaxT)", "最低氣溫 (MinT)"],
                range=["#DC2626", "#1D4ED8"]
            )
        )
    )

    chart = (lines + text).properties(
        title=f"📈 {region_name} 一週最高與最低氣溫走勢預報",
        height=350
    ).configure_view(
        strokeWidth=0
    ).configure_title(
        fontSize=16,
        font="Segoe UI",
        anchor="start",
        color="#1E293B"
    )

    return chart
