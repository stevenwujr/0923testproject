"""
test_pipeline.py
自動化驗證測試腳本，涵蓋 CWA API 解析、SQLite 資料庫冪等性、查詢邏輯與視覺化生成。
"""

import os
import unittest
import pandas as pd
from src.cwa_api import load_sample_data, parse_weather_json, get_weather_dataframe
from src.db import (
    init_db,
    insert_or_update_forecasts,
    get_distinct_regions,
    get_distinct_dates,
    get_forecast_by_region,
    get_forecast_by_date,
    execute_custom_sql,
    get_db_stats
)
from src.visualizer import create_taiwan_weather_map, create_temperature_chart

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_weather.db")


class TestWeatherPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_01_load_and_parse_sample_json(self):
        """測試示範 JSON 資料載入與欄位解析"""
        data = load_sample_data()
        self.assertIn("records", data)
        df = parse_weather_json(data)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        
        expected_cols = ["regionName", "dataDate", "mint", "maxt"]
        for col in expected_cols:
            self.assertIn(col, df.columns)
            
        # 驗證各地區至少有 7 天資料
        regions = df["regionName"].unique()
        self.assertGreaterEqual(len(regions), 6)
        self.assertIn("北部地區", regions)
        self.assertIn("中部地區", regions)
        self.assertIn("南部地區", regions)

    def test_02_sqlite_idempotency(self):
        """測試 SQLite 建立、插入以及重複插入不重複紀錄 (冪等性)"""
        init_db(TEST_DB_PATH)
        df, _, _ = get_weather_dataframe()
        
        # 第一次寫入
        count1 = insert_or_update_forecasts(df, TEST_DB_PATH)
        stats1 = get_db_stats(TEST_DB_PATH)
        self.assertEqual(stats1["total_rows"], len(df))
        
        # 第二次重複寫入 (測試防重複插入機制)
        count2 = insert_or_update_forecasts(df, TEST_DB_PATH)
        stats2 = get_db_stats(TEST_DB_PATH)
        self.assertEqual(stats2["total_rows"], stats1["total_rows"], "重複寫入後總筆數應保持一致，不應膨脹")

    def test_03_db_queries(self):
        """測試 SQL 查詢函數"""
        regions = get_distinct_regions(TEST_DB_PATH)
        self.assertIn("北部地區", regions)
        self.assertIn("中部地區", regions)

        dates = get_distinct_dates(TEST_DB_PATH)
        self.assertGreaterEqual(len(dates), 7)

        # 查詢單一地區
        central_df = get_forecast_by_region("中部地區", TEST_DB_PATH)
        self.assertEqual(len(central_df), len(dates))
        self.assertTrue((central_df["maxt"] >= central_df["mint"]).all(), "最高溫必須大於或等於最低溫")

        # 查詢單一日期
        first_date = dates[0]
        date_df = get_forecast_by_date(first_date, TEST_DB_PATH)
        self.assertEqual(len(date_df), len(regions))

        # 測試自訂 SELECT 查詢
        sql_res = execute_custom_sql("SELECT DISTINCT regionName FROM TemperatureForecasts;", TEST_DB_PATH)
        self.assertEqual(len(sql_res), len(regions))

    def test_04_visualization_generation(self):
        """測試地圖與圖表生成物件"""
        dates = get_distinct_dates(TEST_DB_PATH)
        date_df = get_forecast_by_date(dates[0], TEST_DB_PATH)
        
        # 測試 Folium 地圖產生
        weather_map = create_taiwan_weather_map(date_df, dates[0])
        self.assertIsNotNone(weather_map)
        rendered_map = weather_map.get_root().render()
        self.assertIn("平均溫度階層", rendered_map)

        # 測試 Altair 折線圖產生
        region_df = get_forecast_by_region("北部地區", TEST_DB_PATH)
        chart = create_temperature_chart(region_df, "北部地區")
        self.assertIsNotNone(chart)


if __name__ == "__main__":
    unittest.main()
