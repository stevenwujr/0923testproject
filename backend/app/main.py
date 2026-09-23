from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.schemas.temperature import TemperatureLatestResponse
from backend.app.services.cwa_service import get_geojson, get_latest_station_observations, get_station_detail

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/temperature/latest", response_model=TemperatureLatestResponse)
def get_latest_temperature():
    data = get_latest_station_observations()
    return TemperatureLatestResponse(**data)


@app.get("/api/temperature/geojson")
def get_temperature_geojson():
    return get_geojson()


@app.get("/api/temperature/stations/{station_id}")
def get_temperature_station(station_id: str):
    station = get_station_detail(station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@app.get("/api/health")
def health_check():
    latest = get_latest_station_observations()
    return {
        "status": "ok",
        "cwa_cache_status": "fresh",
        "latest_cwa_time": latest["updated_at"],
    }


@app.get("/api/config")
def public_config():
    """Return browser-safe configuration; the CWA key is never included."""
    return {"windy_api_key": settings.windy_api_key}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=True)
