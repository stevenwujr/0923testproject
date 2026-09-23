"""
cwa_api.py
處理中央氣象署 (CWA) Open Data API 請求與 JSON 結構解析
對應微課程步驟：
- 步驟 3: 中央氣象署 CWA Open Data 平台
- 步驟 4: API 資料取得 (使用 Requests 取得 JSON)
- 步驟 5: JSON 資料結構解析 (定位 locations, weatherElement, MinT, MaxT)
- 步驟 6: 提取最高與最低氣溫
- 步驟 7: 資料整理與預覽 (Pandas DataFrame)
- 步驟 20: 程式碼品質與錯誤處理
"""

import os
import json
import logging
import requests
import pandas as pd
from typing import Tuple, Optional, Dict, Any

# 設定日誌記錄
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# CWA 預設 API 網址與資料集代碼 (臺灣各區一週天氣預報)
CWA_API_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
DEFAULT_DATASET_ID = "F-D0047-091"
DEFAULT_SAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_cwa_weather.json")


def fetch_from_api(api_key: str, dataset_id: str = DEFAULT_DATASET_ID, timeout: int = 10) -> Dict[str, Any]:
    """
    使用 requests 呼叫 CWA API 取得氣象預報 JSON 資料。
    
    :param api_key: CWA API 授權碼
    :param dataset_id: 資料集識別代碼 (預設為 F-D0047-091 臺灣各區一週預報)
    :param timeout: 網路請求超時秒數
    :return: 解析後的 JSON dict
    :raises requests.RequestException: 網路連線或 API 回應異常
    """
    if not api_key or not api_key.strip():
        raise ValueError("未提供有效的 CWA API Key。")

    url = f"{CWA_API_BASE_URL}/{dataset_id}"
    params = {
        "Authorization": api_key.strip(),
        "format": "JSON"
    }
    headers = {
        "User-Agent": "Taiwan-Weather-Forecast-App/1.0",
        "Accept": "application/json"
    }

    logger.info(f"正在呼叫 CWA API: {url} (資料集: {dataset_id})")
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    if not data.get("success") or data.get("success") == "false":
        error_msg = data.get("message", "API 回應失敗，請檢查 API Key 是否正確或權限是否足夠。")
        raise RuntimeError(f"CWA API 錯誤: {error_msg}")

    return data


def load_sample_data(sample_path: str = DEFAULT_SAMPLE_PATH) -> Dict[str, Any]:
    """
    從本地讀取預置的氣象示範 JSON 資料，提供無 API Key 或離線模式下之完整體驗。
    
    :param sample_path: 示範 JSON 檔案路徑
    :return: JSON dict
    """
    if not os.path.exists(sample_path):
        raise FileNotFoundError(f"找不到示範資料檔: {sample_path}")
    
    with open(sample_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_weather_json(data: Dict[str, Any]) -> pd.DataFrame:
    """
    解析 CWA 天氣預報 JSON 結構，提取各地區最高溫 (MaxT) 與最低溫 (MinT)。
    
    處理層級：
    records -> locations -> location 或 records -> location
    -> weatherElement (MinT / MaxT) -> time -> elementValue -> value
    
    :param data: CWA JSON 資料
    :return: 包含欄位 ['regionName', 'dataDate', 'mint', 'maxt'] 的 Pandas DataFrame
    """
    records = data.get("records", {})
    locations_list = []

    # 兼容不同 CWA 資料集的結構層級
    if "locations" in records:
        for loc_container in records["locations"]:
            if "location" in loc_container:
                locations_list.extend(loc_container["location"])
    elif "location" in records:
        locations_list = records["location"]

    if not locations_list:
        raise ValueError("JSON 格式中未找到任何 location 地區資料。")

    records_extracted = []

    for loc in locations_list:
        region_name = loc.get("locationName", "").strip()
        if not region_name:
            continue

        weather_elements = loc.get("weatherElement", [])
        mint_dict = {}  # date -> list of values
        maxt_dict = {}  # date -> list of values

        for elem in weather_elements:
            elem_name = elem.get("elementName", "")
            time_list = elem.get("time", [])

            if elem_name == "MinT":
                for t in time_list:
                    start_time = t.get("startTime", "")
                    date_str = start_time.split(" ")[0] if " " in start_time else start_time[:10]
                    # 抓取 elementValue
                    val = None
                    if "elementValue" in t and len(t["elementValue"]) > 0:
                        val = t["elementValue"][0].get("value")
                    elif "parameter" in t:
                        val = t["parameter"].get("parameterName")

                    if val is not None and date_str:
                        try:
                            mint_dict.setdefault(date_str, []).append(float(val))
                        except (ValueError, TypeError):
                            pass

            elif elem_name == "MaxT":
                for t in time_list:
                    start_time = t.get("startTime", "")
                    date_str = start_time.split(" ")[0] if " " in start_time else start_time[:10]
                    val = None
                    if "elementValue" in t and len(t["elementValue"]) > 0:
                        val = t["elementValue"][0].get("value")
                    elif "parameter" in t:
                        val = t["parameter"].get("parameterName")

                    if val is not None and date_str:
                        try:
                            maxt_dict.setdefault(date_str, []).append(float(val))
                        except (ValueError, TypeError):
                            pass

        # 合併該地區所有日期的最高溫與最低溫
        all_dates = sorted(set(mint_dict.keys()) | set(maxt_dict.keys()))
        for d in all_dates:
            min_vals = mint_dict.get(d, [])
            max_vals = maxt_dict.get(d, [])

            if min_vals and max_vals:
                day_mint = round(min(min_vals), 1)
                day_maxt = round(max(max_vals), 1)
                records_extracted.append({
                    "regionName": region_name,
                    "dataDate": d,
                    "mint": day_mint,
                    "maxt": day_maxt
                })

    df = pd.DataFrame(records_extracted)
    if df.empty:
        raise ValueError("未能從 JSON 中成功提取出任何氣溫預報紀錄。")

    # 確保資料格式與型別正確
    df["mint"] = pd.to_numeric(df["mint"])
    df["maxt"] = pd.to_numeric(df["maxt"])
    df = df.sort_values(by=["regionName", "dataDate"]).reset_index(drop=True)

    return df


def get_weather_dataframe(api_key: Optional[str] = None) -> Tuple[pd.DataFrame, bool, str]:
    """
    整合式獲取氣象預報 DataFrame：
    若提供有效 api_key，優先請求 CWA 即時 API；
    若無提供或連線失敗，自動優雅降級為讀取本地示範資料。
    
    :param api_key: CWA API Key (可為 None)
    :return: (df, is_sample, status_message)
    """
    if api_key and api_key.strip():
        try:
            api_data = fetch_from_api(api_key.strip())
            df = parse_weather_json(api_data)
            return df, False, "成功自中央氣象署 (CWA) API 取得即時一週天氣預報！"
        except Exception as e:
            logger.warning(f"CWA API 請求失敗 ({e})，自動切換至離線示範資料。")
            df = parse_weather_json(load_sample_data())
            return df, True, f"API 請求未成功（原因：{str(e)}），已自動載入離線示範氣象資料庫。"
    else:
        df = parse_weather_json(load_sample_data())
        return df, True, "未設定 API Key，目前顯示內建之台灣各區示範氣溫預報資料。"
