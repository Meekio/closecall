"""
get_weather tool — fetches current weather from OpenWeatherMap.
Falls back to a mock response if the API key is not configured.
"""

import requests
from src.config import config


def get_weather(location: str | None = None) -> dict:
    """
    Fetch current weather for a given location.

    Args:
        location: City name or "lat,lon". Defaults to config.DEFAULT_LOCATION.

    Returns:
        dict with keys:
            location       str
            temperature_c  float
            condition      str   (e.g. "Rain", "Clear", "Clouds")
            description    str   (e.g. "moderate rain")
            is_raining     bool
            humidity_pct   int
            wind_kph       float
    """
    location = location or config.DEFAULT_LOCATION

    if not config.OPENWEATHER_API_KEY:
        # Return a plausible mock so the agent can still reason
        return _mock_weather(location)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": config.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return {
            "location": location,
            "error": str(exc),
            "is_raining": False,
            "condition": "Unknown",
            "description": "Could not fetch weather",
            "temperature_c": 25.0,
            "humidity_pct": 60,
            "wind_kph": 10.0,
        }

    weather_main = data["weather"][0]["main"]          # e.g. "Rain"
    weather_desc = data["weather"][0]["description"]   # e.g. "moderate rain"
    temp_c = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    wind_kph = round(data["wind"]["speed"] * 3.6, 1)   # m/s → km/h

    is_raining = weather_main.lower() in {"rain", "drizzle", "thunderstorm"}

    return {
        "location": location,
        "temperature_c": round(temp_c, 1),
        "condition": weather_main,
        "description": weather_desc,
        "is_raining": is_raining,
        "humidity_pct": humidity,
        "wind_kph": wind_kph,
    }


def _mock_weather(location: str) -> dict:
    """Return a mock weather response when no API key is available."""
    return {
        "location": location,
        "temperature_c": 28.0,
        "condition": "Clouds",
        "description": "scattered clouds (mock data — set OPENWEATHER_API_KEY for real weather)",
        "is_raining": False,
        "humidity_pct": 65,
        "wind_kph": 12.0,
    }
