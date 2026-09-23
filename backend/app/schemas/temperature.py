from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StationTemperature(BaseModel):
    station_id: str
    station_name: str
    county: Optional[str] = None
    town: Optional[str] = None
    lat: float
    lon: float
    altitude_m: Optional[float] = None
    observed_at: datetime
    temperature_c: float
    humidity_percent: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    precipitation_mm: Optional[float] = None
    weather: Optional[str] = None


class TemperatureLatestResponse(BaseModel):
    source: str = "CWA"
    updated_at: datetime
    count: int
    stations: list[StationTemperature] = Field(default_factory=list)
    status: str = "fresh"
    message: Optional[str] = None
