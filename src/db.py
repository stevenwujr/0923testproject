"""
db.py
SQLite 資料庫管理模組
對應微課程步驟：
- 步驟 8: 建立 SQLite 資料庫 (儲存氣溫資料)
- 步驟 9: 資料庫設計 (TemperatureForecasts: id, regionName, dataDate, mint, maxt)
- 步驟 10: 查詢資料驗證 (SELECT DISTINCT regionName, SELECT * WHERE regionName=...)
- 步驟 12: 從資料庫讀取資料 (pd.read_sql_query)
- 步驟 20: 程式碼品質與優化 (防重複插入機制 Idempotency)
"""

import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "weather.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """取得 SQLite 連線物件，確保目標目錄存在"""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    初始化資料表 TemperatureForecasts。
    建立 UNIQUE(regionName, dataDate) 約束以避免重複插入。
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        mint REAL NOT NULL,
        maxt REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(regionName, dataDate)
    );
    CREATE INDEX IF NOT EXISTS idx_region_date ON TemperatureForecasts(regionName, dataDate);
    CREATE INDEX IF NOT EXISTS idx_dataDate ON TemperatureForecasts(dataDate);
    """
    conn = get_connection(db_path)
    try:
        conn.executescript(create_table_sql)
        conn.commit()
    finally:
        conn.close()
    logger.info(f"SQLite 資料庫初始化完成: {db_path}")


def insert_or_update_forecasts(df: pd.DataFrame, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    將 DataFrame 寫入資料庫。
    使用 ON CONFLICT DO UPDATE 機制，落實步驟 20「重複執行不重複插入」的冪等性 (Idempotency)。
    
    :param df: 包含 ['regionName', 'dataDate', 'mint', 'maxt'] 的 DataFrame
    :param db_path: 資料庫路徑
    :return: 處理的筆數
    """
    init_db(db_path)
    
    if df.empty:
        return 0

    upsert_sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(regionName, dataDate) DO UPDATE SET
        mint = excluded.mint,
        maxt = excluded.maxt,
        updated_at = CURRENT_TIMESTAMP;
    """

    records = [
        (str(row["regionName"]), str(row["dataDate"]), float(row["mint"]), float(row["maxt"]))
        for _, row in df.iterrows()
    ]

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(upsert_sql, records)
        conn.commit()
    finally:
        conn.close()

    logger.info(f"成功將 {len(records)} 筆預報寫入 SQLite 資料庫: {db_path}")
    return len(records)


def get_distinct_regions(db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """
    對應步驟 10: 查詢所有不重複地區清單
    SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName;
    """
    init_db(db_path)
    sql = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName ASC;"
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [r["regionName"] for r in rows]
    finally:
        conn.close()


def get_distinct_dates(db_path: str = DEFAULT_DB_PATH) -> List[str]:
    """
    查詢所有不重複的預報日期清單
    SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate;
    """
    init_db(db_path)
    sql = "SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate ASC;"
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [r["dataDate"] for r in rows]
    finally:
        conn.close()


def get_forecast_by_region(region_name: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    對應步驟 10、12: 查詢特定地區的一週預報氣溫資料
    SELECT * FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate;
    """
    init_db(db_path)
    sql = """
    SELECT id, regionName, dataDate, mint, maxt, updated_at
    FROM TemperatureForecasts
    WHERE regionName = ?
    ORDER BY dataDate ASC;
    """
    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(sql, conn, params=(region_name,))
        return df
    finally:
        conn.close()


def get_forecast_by_date(date_str: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    對應步驟 18: 查詢特定日期全台各地區預報氣溫資料
    """
    init_db(db_path)
    sql = """
    SELECT id, regionName, dataDate, mint, maxt, updated_at
    FROM TemperatureForecasts
    WHERE dataDate = ?
    ORDER BY regionName ASC;
    """
    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(sql, conn, params=(date_str,))
        return df
    finally:
        conn.close()


def get_all_forecasts(db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    查詢全表所有資料
    """
    init_db(db_path)
    sql = "SELECT * FROM TemperatureForecasts ORDER BY regionName, dataDate ASC;"
    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


def execute_custom_sql(query: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    安全執行只讀 SELECT 查詢，供 UI 驗證與教學演示
    """
    clean_query = query.strip()
    if not clean_query.upper().startswith("SELECT"):
        raise ValueError("基於安全考量，僅支援執行 SELECT 查詢語法。")
    
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(clean_query, conn)
    finally:
        conn.close()


def get_db_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    取得資料庫當前狀態摘要（總筆數、地區數、日期範圍、最新更新時間）
    """
    init_db(db_path)
    stats = {
        "total_rows": 0,
        "region_count": 0,
        "date_count": 0,
        "date_range": "無資料",
        "last_updated": "尚未更新"
    }
    
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT regionName), COUNT(DISTINCT dataDate), MIN(dataDate), MAX(dataDate), MAX(updated_at) FROM TemperatureForecasts;")
        row = cursor.fetchone()
        if row and row[0] > 0:
            stats["total_rows"] = row[0]
            stats["region_count"] = row[1]
            stats["date_count"] = row[2]
            stats["date_range"] = f"{row[3]} ~ {row[4]}"
            stats["last_updated"] = str(row[5])
        return stats
    finally:
        conn.close()
