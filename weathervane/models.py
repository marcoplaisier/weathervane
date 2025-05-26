from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """
    Pydantic model for weather data.
    """
    error: bool = Field(default=True)
    airpressure: float = Field(default=900.0)
    humidity: float = Field(default=0.0)
    rain: bool = Field(default=True)
    random: int = Field(default=0)
    temperature: float = Field(default=-39.9)
    groundtemperature: float = Field(default=-39.9)
    feeltemperature: float = Field(default=0.0)
    winddirection: str = Field(default="N")
    winddirectiondegrees: int = Field(default=0)
    windspeed: float = Field(default=0.0)
    windgusts: float = Field(default=0.0)
    windspeedBft: int = Field(default=0)
    
    # Fields added by BuienradarParser
    timestamp: Optional[str] = Field(default=None)
    barometric_trend: Optional[int] = Field(default=None) # Mapped from {'dropping': 2, 'stable': 4, 'rising': 1}
    data_from_fallback: bool = Field(default=False)

    # Potentially other fields from Buienradar that are not in DEFAULT_WEATHER_DATA
    # but might be present in the actual API response and used elsewhere.
    # For now, sticking to the explicitly mentioned ones and DEFAULT_WEATHER_DATA.

    # Example of how other fields from Buienradar's stationmeasurements could be added if needed:
    # stationname: Optional[str] = Field(default=None)
    # stationid: Optional[int] = Field(default=None)
    # lat: Optional[float] = Field(default=None)
    # lon: Optional[float] = Field(default=None)
    # regiocode: Optional[str] = Field(default=None)
    # measured: Optional[str] = Field(default=None) # Timestamp of measurement
    # weatherdescription: Optional[str] = Field(default=None)
    # iconurl: Optional[str] = Field(default=None)
    # sunpower: Optional[float] = Field(default=None) # W/m2
    # rainFallLastHour: Optional[float] = Field(default=None) # mm
    # rainFallLast24Hour: Optional[float] = Field(default=None) # mm
    # visibility: Optional[int] = Field(default=None) # meters
    # windazimuth: Optional[str] = Field(default=None) # e.g., ZZW, should map to winddirection
    # windspeedMS: Optional[float] = Field(default=None) # m/s, likely same as windspeed if that's m/s
    # windgustsMS: Optional[float] = Field(default=None) # m/s, likely same as windgusts if that's m/s
    # precipitation: Optional[float] = Field(default=None) # This might be what 'rain' boolean is derived from

    class Config:
        # This allows the model to be created from a dictionary that has extra fields,
        # which will be ignored. This is useful as the actual API response might have more fields.
        extra = "ignore"


class DisplayConfig(BaseModel):
    """
    Pydantic model for display configuration.
    """
    auto_turn_off: bool
    start_time: str
    end_time: str
    pin: int


class AppConfig(BaseModel):
    """
    Pydantic model for the main application configuration.
    """
    channel: int
    frequency: int
    library: str
    data_collection_interval: int
    source: str
    data_display_interval: float
    test: bool
    barometric_trend: bool
    stations: List[int]
    bits: List[Dict] # Or List[dict] as per original plan, Pydantic handles dict well.
    display: DisplayConfig # Renamed from display_config to match the key in the config dict

    class Config:
        # This allows the model to be created from a dictionary that has extra fields,
        # which will be ignored. This ensures that if WeathervaneConfigParser.parse_config()
        # returns a dict with more keys than defined here, it doesn't cause an error.
        extra = "ignore"
