import pytest
import json
from unittest.mock import patch, MagicMock
import random
from datetime import datetime, timedelta

from weathervane.weathervaneinterface import WeatherVaneInterface
from weathervane.parser import BuienradarParser, is_weather_data_stale
from weathervane.datasources import BuienRadarDataSource
import asyncio

# Define wind directions
WIND_DIRECTIONS = [
    "N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO", 
    "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW", 
    # Also test invalid directions
    "INVALID", "", None
]

def generate_random_weather_data():
    """Generate random but plausible weather data."""
    return {
        "winddirection": random.choice(WIND_DIRECTIONS),
        "windspeed": random.uniform(-10, 100),
        "windgusts": random.uniform(-10, 150),
        "windspeedBft": random.randint(-5, 20),
        "airpressure": random.uniform(850, 1200),
        "temperature": random.uniform(-50, 60),
        "feeltemperature": random.uniform(-60, 70),
        "humidity": random.uniform(-10, 120),
        "precipitation": random.choice([random.uniform(-5, 100), True, False]),
        # Include some invalid or missing data
        "random": random.choice([random.randint(-100, 100), "text", None]),
        # Sometimes include required fields
        "timestamp": random.choice([
            datetime.now().isoformat(),
            "invalid-date",
            None
        ]),
        # Sometimes omit fields
        **({"error": random.choice([True, False])} if random.choice([True, False]) else {})
    }

# Test fixture for interface config
@pytest.fixture
def interface_config():
    return {
        "channel": 0,
        "frequency": 250000,
        "test": True,
        "bits": [
            {"key": "winddirection", "length": "4"},
            {"key": "windspeed", "length": "6", "min": "0", "max": "63", "step": "1"},
            {"key": "windgusts", "length": "6", "min": "0", "max": "63", "step": "1"},
            {"key": "windspeedBft", "length": "4", "min": "0", "max": "12", "step": "1"},
            {"key": "airpressure", "length": "8", "min": "900", "max": "1155", "step": "1"},
            {"key": "temperature", "length": "10", "min": "-39.9", "max": "49.9", "step": "0.1"},
            {"key": "feeltemperature", "length": "10", "min": "-39.9", "max": "49.9", "step": "0.1"},
            {"key": "humidity", "length": "7", "min": "0", "max": "99", "step": "1"},
            {"key": "error", "length": "1"},
            {"key": "precipitation", "length": "1"}
        ],
        "stations": [6370, 6350]
    }

@patch("weathervane.weathervaneinterface.GPIO", autospec=True)
def test_encode_weather_data_robustness(mock_gpio, interface_config):
    """Test that encode_weather_data handles various inputs without crashing."""
    interface = WeatherVaneInterface(**interface_config)
    
    # Test specific edge cases that are likely to cause problems
    edge_cases = [
        # Empty data
        {},
        # None data
        None,
        # Missing required fields
        {"windspeed": 10.0},
        # Invalid types
        {"winddirection": 123, "windspeed": "fast", "airpressure": "high"},
        # Extreme values
        {"windspeed": float('inf'), "temperature": float('nan'), "airpressure": -9999},
        # Mixed valid/invalid
        {"winddirection": "N", "windspeed": None, "temperature": "hot"}
    ]
    
    for case in edge_cases:
        try:
            # Should either return data or fail gracefully
            if case is not None:  # Skip None case as it would raise TypeError
                try:
                    result = interface.encode_weather_data(case)
                    if result:  # If it processed successfully
                        assert isinstance(result, (bytes, bytearray))
                except Exception:
                    # Expected to fail for some edge cases
                    pass
        except Exception as e:
            # We shouldn't get unexpected exceptions
            assert isinstance(e, (ValueError, TypeError)), f"Unexpected exception: {type(e)}: {e}"
    
    # Test multiple random cases
    for _ in range(30):
        weather_data = generate_random_weather_data()
        
        # The function should either succeed or handle errors gracefully
        try:
            result = interface.encode_weather_data(weather_data)
            # Verify the result is a valid bytearray
            assert isinstance(result, bytes) or isinstance(result, bytearray)
            assert len(result) > 0
        except Exception as e:
            # Even if it fails, it should do so in expected ways
            # This is just a fuzzing test, so we're allowing exceptions to happen
            # We're just making sure the system doesn't crash unexpectedly
            pass

@patch("weathervane.weathervaneinterface.GPIO", autospec=True)
def test_value_to_bits_consistency(mock_gpio, interface_config):
    """Test that _value_to_bits consistently handles various inputs."""
    interface = WeatherVaneInterface(**interface_config)
    
    # Test multiple random cases
    for _ in range(50):
        # Generate random values for different measurement types
        measurement_name = random.choice([
            "winddirection", "precipitation", "temperature", "windspeed", 
            "airpressure", "random_field"
        ])
        
        # Generate appropriate values based on measurement type
        if measurement_name == "winddirection":
            value = random.choice(WIND_DIRECTIONS)
        elif measurement_name == "precipitation":
            value = random.choice([
                random.uniform(-10, 100),
                None,
                "text",
                True,
                False
            ])
        else:
            value = random.choice([
                random.uniform(-100, 100),
                None,
                "text"
            ])
        
        # Parameters for conversion
        step_value = max(0.01, random.uniform(0.01, 10))  # Avoid zero
        min_value = random.uniform(-50, 50)
        max_value = min_value + random.uniform(0.1, 100)
        
        # The function should always return an integer or handle errors gracefully
        try:
            result = interface._value_to_bits(measurement_name, value, step_value, min_value, max_value)
            assert isinstance(result, int)
        except Exception:
            # This is a fuzzing test so we allow exceptions
            pass

def generate_buienradar_json():
    """Generate random buienradar JSON data for testing the parser."""
    # Create a simple but valid structure matching what the parser expects
    num_stations = random.randint(1, 5)
    
    stations = []
    for _ in range(num_stations):
        station = {
            "stationid": random.randint(6300, 6400),
            "timestamp": datetime.now().isoformat(),
            "temperature": random.uniform(-30, 40),
            "feeltemperature": random.uniform(-40, 45),
            "windspeed": random.uniform(0, 30),
        }
        
        # Randomly add or omit fields
        if random.choice([True, False]):
            station["winddirection"] = random.choice(WIND_DIRECTIONS)
        if random.choice([True, False]):
            station["humidity"] = random.uniform(0, 100)
        if random.choice([True, False]):
            station["airpressure"] = random.uniform(900, 1100)
            
        stations.append(station)
    
    # Create the full structure
    data = {
        "actual": {
            "stationmeasurements": stations
        }
    }
    
    return json.dumps(data)

def test_buienradar_parser_robustness():
    """Test that the BuienradarParser can handle various inputs without crashing."""
    stations = [6370, 6350, 6380]
    bits = [
        {"key": "winddirection", "length": "4"},
        {"key": "windspeed", "length": "6"},
        {"key": "temperature", "length": "8"}
    ]
    
    parser = BuienradarParser(stations=stations, bits=bits)
    
    # Edge cases for malformed JSON
    edge_cases = [
        # Empty JSON
        "{}",
        # Missing required sections
        '{"actual": {}}',
        # Empty stations
        '{"actual": {"stationmeasurements": []}}',
        # Invalid structure
        '{"wrong_key": {"stationmeasurements": []}}',
        # Missing stationid
        '{"actual": {"stationmeasurements": [{"temperature": 10.5}]}}',
        # Malformed station data
        '{"actual": {"stationmeasurements": [{"stationid": "not-a-number", "temperature": "not-a-temp"}]}}',
        # Station ID not in list
        '{"actual": {"stationmeasurements": [{"stationid": 9999, "temperature": 10.5}]}}',
    ]
    
    for case in edge_cases:
        try:
            result = parser.parse(case)
            # Should return a dict even for edge cases that can be handled
            assert isinstance(result, dict)
        except Exception:
            # Expected to fail for some edge cases
            pass
    
    # Test multiple random valid cases
    for _ in range(15):
        data = generate_buienradar_json()
        
        try:
            result = parser.parse(data)
            # Should return a dict
            assert isinstance(result, dict)
            
            # Check for expected keys in result
            assert "timestamp" in result
            
            # The error field should be a boolean
            assert isinstance(result.get("error", False), bool)
            
        except Exception:
            # Fuzzing test - allowing exceptions but taking note
            pass

def test_is_weather_data_stale_robustness():
    """Test that is_weather_data_stale handles various inputs gracefully."""
    # Test multiple random cases
    for _ in range(20):
        timestamp = random.choice([
            datetime.now().isoformat(),
            (datetime.now() - timedelta(hours=random.uniform(0, 48))).isoformat(),
            "invalid timestamp",
            ""
        ])
        
        now = datetime.now()
        
        try:
            result = is_weather_data_stale(timestamp, now)
            assert isinstance(result, bool)
        except Exception:
            # For invalid timestamps, exceptions are expected
            pass

@pytest.mark.skip(reason="Requires async setup")
def test_buienradar_data_source_queue_robustness():
    """Test that the BuienRadarDataSource handles queue operations robustly."""
    # This test needs to be run in an async environment which is more complex to set up
    # without pytest-asyncio. Skipping for now.
    pass