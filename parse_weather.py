"""
parse_weather.py
HW10 目標 2：分析 JSON 結構，提取氣溫資料

說明：
- 讀取 weather_data.json
- 解析 locations -> location -> weatherElement (MinT / MaxT)
- 整理為六大區域（北部、中部、南部、東北部、東部、東南部）一週預報
- 輸出至 weather_data.csv 並顯示預覽
"""

import os
import json
import pandas as pd
from typing import Optional

INPUT_JSON = "weather_data.json"
OUTPUT_CSV = "weather_data.csv"

# 台灣縣市對應微課程之主要分區對照表
COUNTY_TO_REGION = {
    "基隆市": "北部地區", "臺北市": "北部地區", "新北市": "北部地區",
    "桃園市": "北部地區", "新竹市": "北部地區", "新竹縣": "北部地區", "苗栗縣": "北部地區",
    "臺中市": "中部地區", "彰化縣": "中部地區", "南投縣": "中部地區",
    "雲林縣": "中部地區", "嘉義市": "中部地區", "嘉義縣": "中部地區",
    "臺南市": "南部地區", "高雄市": "南部地區", "屏東縣": "南部地區",
    "宜蘭縣": "東北部地區",
    "花蓮縣": "東部地區",
    "臺東縣": "東南部地區",
    "澎湖縣": "澎湖地區", "金門縣": "金門地區", "連江縣": "馬祖地區"
}

# 作業規定的六大核心區域
CORE_REGIONS = ["北部地區", "中部地區", "南部地區", "東北部地區", "東部地區", "東南部地區"]


def parse_weather_data(json_path: str = INPUT_JSON, output_csv: Optional[str] = OUTPUT_CSV) -> pd.DataFrame:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到 JSON 檔案：{json_path}，請先執行 python fetch_weather.py。")
    
    print(f"[1/3] 正在讀取並解析 {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    records = data.get("records", {})
    # 支援新舊版 Locations / locations
    locations = records.get("Locations") or records.get("locations") or []
    loc_list = []
    if isinstance(locations, list) and len(locations) > 0:
        loc_list = locations[0].get("Location") or locations[0].get("location") or []
    elif isinstance(records.get("location"), list):
        loc_list = records.get("location")

    if not loc_list:
        raise ValueError("JSON 格式中未找到任何 location 地區資料。")

    # 彙總各分區每天的氣溫觀察值: (region, date) -> {'min': [...], 'max': [...]}
    region_date_map = {}

    for loc in loc_list:
        loc_name = loc.get("LocationName") or loc.get("locationName", "")
        # 若已有 regionName 則直接使用，否則透過縣市名稱映射分區
        region = loc_name if "地區" in loc_name else COUNTY_TO_REGION.get(loc_name)
        if not region:
            continue

        weather_elements = loc.get("WeatherElement") or loc.get("weatherElement") or []

        for elem in weather_elements:
            el_name = elem.get("ElementName") or elem.get("elementName", "")
            time_list = elem.get("Time") or elem.get("time") or []

            is_min = (el_name in ["最低溫度", "MinT", "MinTemperature"])
            is_max = (el_name in ["最高溫度", "MaxT", "MaxTemperature"])

            if not (is_min or is_max):
                continue

            for t in time_list:
                start_time = t.get("StartTime") or t.get("startTime", "")
                date_str = start_time[:10]
                if not date_str:
                    continue

                val_containers = t.get("ElementValue") or t.get("elementValue") or []
                val = None
                if val_containers and isinstance(val_containers, list):
                    first_val = val_containers[0]
                    val = first_val.get("MinTemperature") or first_val.get("MaxTemperature") or first_val.get("value")
                elif "parameter" in t:
                    val = t["parameter"].get("parameterName")

                if val is not None and str(val).strip() != "":
                    try:
                        f_val = float(val)
                        key = (region, date_str)
                        if key not in region_date_map:
                            region_date_map[key] = {"min": [], "max": []}
                        if is_min:
                            region_date_map[key]["min"].append(f_val)
                        if is_max:
                            region_date_map[key]["max"].append(f_val)
                    except (ValueError, TypeError):
                        pass

    # 轉換為標準 DataFrame: [regionName, dataDate, mint, maxt]
    rows = []
    for (region, date_str), temps in region_date_map.items():
        if temps["min"] and temps["max"]:
            day_mint = round(min(temps["min"]), 1)
            day_maxt = round(max(temps["max"]), 1)
            rows.append({
                "regionName": region,
                "dataDate": date_str,
                "mint": day_mint,
                "maxt": day_maxt
            })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("未能提取出任何氣溫預報紀錄。")

    # 排序並格式化
    df = df.sort_values(by=["regionName", "dataDate"]).reset_index(drop=True)

    print(f"[2/3] 成功提取氣溫資料！共 {len(df)} 筆紀錄，涵蓋地區：{sorted(df['regionName'].unique())}")
    
    # 按照 HW10 投影片要求，印出提取結果範例
    print("\n--- 提取結果範例 (前 10 筆) ---")
    print(df.head(10).to_string(index=False))
    print("--------------------------------\n")

    if output_csv:
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"[3/3] 中間產物已儲存至：{output_csv}")

    return df


if __name__ == "__main__":
    parse_weather_data()
