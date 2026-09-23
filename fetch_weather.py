"""
fetch_weather.py
HW10 目標 1：使用 CWA API 取得台灣氣象預報資料 (JSON 格式)

說明：
- 使用 CWA API Key 呼叫中央氣象署開放資料 API
- 取得一週天氣預報資料集 (F-D0047-091)
- 將回傳的 JSON 儲存為 weather_data.json
"""

import os
import json
import requests
import urllib3

# 關閉 SSL 不安全連線警告 (確保在各 Windows Python 環境連線順暢)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 使用作業指定之 CWA API Key
API_KEY = "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2"
DATASET_ID = "F-D0047-091"  # 臺灣各區一週天氣預報
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{DATASET_ID}"
OUTPUT_FILE = "weather_data.json"


def fetch_cwa_data(api_key: str = API_KEY, output_path: str = OUTPUT_FILE) -> dict:
    print(f"[1/3] 正在呼叫 CWA API 取得氣象資料 (資料集: {DATASET_ID})...")
    
    headers = {
        "Authorization": api_key,
        "User-Agent": "HW10-Weather-Client/1.0"
    }
    params = {
        "format": "JSON"
    }
    
    response = requests.get(URL, headers=headers, params=params, verify=False, timeout=30)
    
    if response.status_code != 200:
        raise RuntimeError(f"CWA API 回應異常，HTTP 狀態碼: {response.status_code}\n內容: {response.text}")
    
    data = response.json()
    
    if not data.get("success") or data.get("success") == "false":
        raise RuntimeError(f"CWA API 回傳失敗訊息: {data.get('message', '未知錯誤')}")
    
    print("[2/3] 成功取得 JSON 資料，正在儲存至本機檔案...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[3/3] 檔案已儲存: {output_path} (大小約 {os.path.getsize(output_path) / 1024:.1f} KB)")
    return data


if __name__ == "__main__":
    fetch_cwa_data()
