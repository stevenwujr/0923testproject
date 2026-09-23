from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.cwa_api import load_sample_data, parse_weather_json
from backend.app.config import settings
import requests
import urllib3

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STATION_TEMPLATE = [
    {"station_id": "466920", "station_name": "臺北", "county": "臺北市", "town": "中正區", "lat": 25.0377, "lon": 121.5149, "region": "北部地區"},
    {"station_id": "466900", "station_name": "板橋", "county": "新北市", "town": "板橋區", "lat": 25.0143, "lon": 121.4637, "region": "北部地區"},
    {"station_id": "466880", "station_name": "桃園", "county": "桃園市", "town": "桃園區", "lat": 24.9941, "lon": 121.3010, "region": "北部地區"},
    {"station_id": "466883", "station_name": "新竹", "county": "新竹縣", "town": "竹北市", "lat": 24.8294, "lon": 121.0055, "region": "北部地區"},
    {"station_id": "C01", "station_name": "新竹市", "county": "新竹市", "town": "東區", "lat": 24.8138, "lon": 120.9675, "region": "北部地區"},
    {"station_id": "466940", "station_name": "苗栗", "county": "苗栗縣", "town": "苗栗市", "lat": 24.5602, "lon": 120.8214, "region": "中部地區"},
    {"station_id": "467050", "station_name": "臺中", "county": "臺中市", "town": "西區", "lat": 24.1477, "lon": 120.6736, "region": "中部地區"},
    {"station_id": "467270", "station_name": "彰化", "county": "彰化縣", "town": "彰化市", "lat": 24.0756, "lon": 120.5440, "region": "中部地區"},
    {"station_id": "467210", "station_name": "南投", "county": "南投縣", "town": "南投市", "lat": 23.9157, "lon": 120.6639, "region": "中部地區"},
    {"station_id": "467770", "station_name": "雲林", "county": "雲林縣", "town": "斗六市", "lat": 23.7092, "lon": 120.4313, "region": "中部地區"},
    {"station_id": "467490", "station_name": "嘉義", "county": "嘉義市", "town": "東區", "lat": 23.4800, "lon": 120.4495, "region": "南部地區"},
    {"station_id": "467530", "station_name": "嘉義縣", "county": "嘉義縣", "town": "太保市", "lat": 23.4592, "lon": 120.3329, "region": "南部地區"},
    {"station_id": "467410", "station_name": "臺南", "county": "臺南市", "town": "中西區", "lat": 22.9937, "lon": 120.2017, "region": "南部地區"},
    {"station_id": "467440", "station_name": "高雄", "county": "高雄市", "town": "前金區", "lat": 22.6273, "lon": 120.3013, "region": "南部地區"},
    {"station_id": "467550", "station_name": "屏東", "county": "屏東縣", "town": "屏東市", "lat": 22.6710, "lon": 120.4880, "region": "南部地區"},
    {"station_id": "466990", "station_name": "花蓮", "county": "花蓮縣", "town": "花蓮市", "lat": 23.9769, "lon": 121.6064, "region": "東部地區"},
    {"station_id": "467080", "station_name": "宜蘭", "county": "宜蘭縣", "town": "宜蘭市", "lat": 24.7576, "lon": 121.7535, "region": "東部地區"},
    {"station_id": "467540", "station_name": "臺東", "county": "臺東縣", "town": "臺東市", "lat": 22.7554, "lon": 121.1500, "region": "東部地區"},
    {"station_id": "467350", "station_name": "澎湖", "county": "澎湖縣", "town": "馬公市", "lat": 23.5657, "lon": 119.5898, "region": "澎湖地區"},
    {"station_id": "467110", "station_name": "金門", "county": "金門縣", "town": "金城鎮", "lat": 24.4340, "lon": 118.3180, "region": "金門地區"},
    {"station_id": "467990", "station_name": "馬祖", "county": "連江縣", "town": "南竿鄉", "lat": 26.1605, "lon": 119.9499, "region": "馬祖地區"},
]

REGION_NAME_MAP = {
    "北部地區": "北部",
    "中部地區": "中部",
    "南部地區": "南部",
    "東部地區": "東部",
    "東北部地區": "東北",
    "東南部地區": "東南",
    "澎湖地區": "澎湖",
    "金門地區": "金門",
    "馬祖地區": "馬祖",
}

_cache: dict[str, Any] = {"payload": None, "fetched_at": None}
INVALID_VALUES = {None, "", "X", "NA", "N/A", "null", "-99", "-999"}


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(hour=12, minute=0, second=0)


def _as_float(value: Any, minimum: float | None = None, maximum: float | None = None) -> float | None:
    if value in INVALID_VALUES:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if minimum is not None and number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return number


def _first_value(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    if isinstance(value, dict):
        return value.get("value", value.get("Value", value.get("parameterName")))
    return value


def _field(record: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in record:
            return record[name]
    return None


def _observation_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = data.get("records", {})
    candidates = records.get("Station", records.get("station", records.get("location", [])))
    if isinstance(candidates, dict):
        candidates = candidates.get("Station", candidates.get("station", candidates.get("location", [])))
    return [item for item in candidates if isinstance(item, dict)]


def _coordinate(record: dict[str, Any], name: str) -> Any:
    geo = record.get("GeoInfo", record.get("geoInfo", {}))
    if isinstance(geo, dict):
        value = _field(geo, name, name[0].lower() + name[1:])
        if value is not None:
            return value
        points = geo.get("Coordinates", geo.get("coordinates", []))
        preferred = [point for point in points if isinstance(point, dict) and point.get("CoordinateName") == "WGS84"]
        for point in preferred + [point for point in points if point not in preferred]:
            value = _field(point, name, name[0].lower() + name[1:])
            if value is not None:
                return value
    return _field(record, name, name[0].lower() + name[1:])


def _element(record: dict[str, Any], *names: str) -> Any:
    weather = record.get("WeatherElement", record.get("weatherElement", {}))
    if isinstance(weather, dict):
        for name in names:
            value = _field(weather, name, name[0].lower() + name[1:])
            if value is not None:
                return _first_value(value)
    elements = record.get("weatherElement")
    if isinstance(elements, list):
        for item in elements:
            if item.get("elementName") in names or item.get("ElementName") in names:
                return _first_value(item.get("elementValue", item.get("ElementValue")))
    return None


def _parse_observations(data: dict[str, Any]) -> list[dict[str, Any]]:
    stations = []
    for record in _observation_records(data):
        station_id = _field(record, "StationId", "stationId", "station_id")
        name = _field(record, "StationName", "stationName", "station_name")
        lat = _as_float(_coordinate(record, "StationLatitude"), 20, 27)
        lon = _as_float(_coordinate(record, "StationLongitude"), 118, 123)
        temperature = _as_float(_element(record, "AirTemperature", "airTemperature", "temperature"), -20, 50)
        observed = _field(record, "ObsTime", "obsTime", "DateTime", "datetime")
        if isinstance(observed, dict):
            observed = _field(observed, "DateTime", "dateTime", "value")
        if not station_id or not name or lat is None or lon is None or temperature is None or not observed:
            continue
        observed_at = str(observed).replace("Z", "+00:00")
        geo = record.get("GeoInfo", record.get("geoInfo", {}))
        stations.append({
            "station_id": str(station_id), "station_name": str(name),
            "county": _field(record, "CountyName", "countyName") or _field(geo, "CountyName", "countyName"),
            "town": _field(record, "TownName", "townName") or _field(geo, "TownName", "townName"), "lat": lat, "lon": lon,
            "altitude_m": _as_float(_coordinate(record, "StationAltitude")),
            "observed_at": observed_at,
            "temperature_c": round(temperature, 1),
            "humidity_percent": _as_float(_element(record, "RelativeHumidity", "relativeHumidity"), 0, 100),
            "pressure_hpa": _as_float(_element(record, "AirPressure", "airPressure"), 800, 1100),
            "wind_speed_mps": _as_float(_element(record, "WindSpeed", "windSpeed"), 0, 150),
            "wind_direction_deg": _as_float(_element(record, "WindDirection", "windDirection"), 0, 360),
            "precipitation_mm": _as_float(_element(record, "Precipitation", "precipitation"), 0),
            "weather": _element(record, "Weather", "weather"),
        })
    return stations


def _sample_station_payloads() -> list[dict[str, Any]]:
    source = load_sample_data()
    df = parse_weather_json(source)
    latest_date = df["dataDate"].max()
    region_rows = df[df["dataDate"] == latest_date].copy()
    region_temps = {
        row["regionName"]: round((row["mint"] + row["maxt"]) / 2.0, 1)
        for _, row in region_rows.iterrows()
    }

    stations: list[dict[str, Any]] = []
    for idx, station in enumerate(STATION_TEMPLATE):
        region_name = station["region"]
        base_temp = float(region_temps.get(region_name, 27.5))
        temp_delta = ((idx % 5) - 2) * 1.8
        temp = round(max(-10.0, min(45.0, base_temp + temp_delta)), 1)
        humidity = 50 + (idx * 7) % 35
        wind = 1.3 + (idx % 4) * 0.8
        observed_at = _parse_date(latest_date)

        stations.append(
            {
                "station_id": station["station_id"],
                "station_name": station["station_name"],
                "county": station["county"],
                "town": station["town"],
                "lat": station["lat"],
                "lon": station["lon"],
                "altitude_m": 12.0 + idx * 5.0,
                "observed_at": observed_at.isoformat(timespec="seconds"),
                "temperature_c": temp,
                "humidity_percent": humidity,
                "pressure_hpa": 1008.0 + (idx % 4),
                "wind_speed_mps": round(wind, 1),
                "wind_direction_deg": 90.0 + idx * 18,
                "precipitation_mm": 0.0,
                "weather": "晴" if temp > 25 else "多雲",
            }
        )
    return stations


def get_latest_station_observations() -> dict[str, Any]:
    now = datetime.now().astimezone().replace(microsecond=0)
    cached_at = _cache.get("fetched_at")
    if _cache.get("payload") and cached_at and (now - cached_at) < timedelta(seconds=settings.cache_ttl_seconds):
        return _cache["payload"]

    try:
        stations = []
        if settings.cwa_api_key and settings.cwa_data_url:
            response = requests.get(
                settings.cwa_data_url,
                params={"Authorization": settings.cwa_api_key, "format": "JSON"},
                headers={"Accept": "application/json", "User-Agent": "CWA-Temperature-Broadcast/1.0"},
                timeout=10,
                verify=False,
            )
            response.raise_for_status()
            stations = _parse_observations(response.json())
        if not stations:
            raise ValueError("CWA 回應中沒有可用觀測站資料")
        payload = {"source": "CWA", "updated_at": now.isoformat(), "count": len(stations), "stations": stations, "status": "fresh"}
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        stations = _sample_station_payloads()
        payload = {
            "source": "CWA", "updated_at": now.isoformat(), "count": len(stations), "stations": stations,
            "status": "stale", "message": f"CWA 資料暫時無法取得，已顯示本地示範資料：{error}",
        }
    _cache.update({"payload": payload, "fetched_at": now})
    return payload


def get_geojson() -> dict[str, Any]:
    payload = get_latest_station_observations()
    features = []
    for station in payload["stations"]:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [station["lon"], station["lat"]]},
                "properties": {
                    "station_id": station["station_id"],
                    "station_name": station["station_name"],
                    "temperature_c": station["temperature_c"],
                    "county": station["county"],
                    "town": station["town"],
                    "observed_at": station["observed_at"],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def get_station_detail(station_id: str) -> dict[str, Any] | None:
    for station in get_latest_station_observations()["stations"]:
        if station["station_id"] == station_id:
            return station
    return None
