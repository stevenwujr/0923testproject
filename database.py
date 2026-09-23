"""
database.py
HW10 目標 3：存入 SQLite 資料庫 (data.db)

說明：
- 將整理好的氣溫預報資料存入 SQLite 資料庫 (data.db)
- 建立資料表 TemperatureForecasts
- 實作驗證查詢：
  1. 列出所有地區名稱 (SELECT DISTINCT regionName)
  2. 查詢中部地區資料 (WHERE regionName = '中部地區')
"""

import os
import sys
import sqlite3
import pandas as pd
from typing import Optional

# 確保在 Windows 控制台輸出正常
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DB_FILE = "data.db"
INPUT_CSV = "weather_data.csv"


def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: str = DB_FILE) -> None:
    """建立資料表 TemperatureForecasts"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        mint REAL NOT NULL,
        maxt REAL NOT NULL,
        UNIQUE(regionName, dataDate)
    );
    """
    conn = get_connection(db_path)
    try:
        conn.execute(create_table_sql)
        conn.commit()
    finally:
        conn.close()


def save_to_database(df: Optional[pd.DataFrame] = None, csv_path: str = INPUT_CSV, db_path: str = DB_FILE) -> int:
    """將氣溫預報資料儲存至 SQLite 資料庫，具備冪等性 (防重複插入)"""
    init_database(db_path)

    if df is None:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"找不到 {csv_path}，請先執行 python parse_weather.py。")
        df = pd.read_csv(csv_path)

    insert_sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(regionName, dataDate) DO UPDATE SET
        mint = excluded.mint,
        maxt = excluded.maxt;
    """

    records = [
        (str(row["regionName"]), str(row["dataDate"]), float(row["mint"]), float(row["maxt"]))
        for _, row in df.iterrows()
    ]

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(insert_sql, records)
        conn.commit()
        count = len(records)
    finally:
        conn.close()

    print(f"[OK] 成功將 {count} 筆氣溫預報存入 SQLite 資料庫：{db_path}")
    return count


def verify_database(db_path: str = DB_FILE) -> None:
    """執行作業要求的兩大驗證查詢"""
    print("\n================== SQLite 資料庫驗證查詢 ==================")
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        # 驗證查詢 1: 列出所有地區名稱
        query1 = "SELECT DISTINCT regionName FROM TemperatureForecasts;"
        print(f"\n[驗證查詢 1] {query1}")
        cursor.execute(query1)
        regions = [row[0] for row in cursor.fetchall()]
        print(f"結果：{regions} (共 {len(regions)} 個地區)")

        # 驗證查詢 2: 查詢中部地區資料
        query2 = "SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';"
        print(f"\n[驗證查詢 2] {query2}")
        cursor.execute(query2)
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        
        result_df = pd.DataFrame([dict(r) for r in rows])
        print(result_df.to_string(index=False))
        print("===========================================================\n")
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    save_to_database()
    verify_database()
