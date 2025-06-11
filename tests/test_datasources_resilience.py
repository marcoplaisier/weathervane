import unittest
from unittest.mock import patch, AsyncMock, MagicMock, call, Mock

import httpx  # Required for httpx.RequestError
import pytest

# Assuming BuienRadarDataSource and HTTP_OK are in weathervane.datasources
# Adjust the import path if your project structure is different.
from weathervane.datasources import BuienRadarDataSource, HTTP_OK


# Patch logger at the module level where BuienRadarDataSource is defined
@patch('weathervane.datasources.logger', new_callable=MagicMock)
class TestBuienRadarDataSourceResilience(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # The class-level patch injects mock_logger_class_level. Reset it for each test.
        # This is good practice if you are asserting specific call orders or counts per test.
        # Accessing the mock via the argument passed to each test method by the class decorator.
        # However, the decorator passes it as the last argument, so method signatures need to be updated.
        # Or, we can access it via self.mock_logger_class_level if we assign it in each test.
        # For simplicity, the example has it as an arg. Let's ensure it's reset.
        # The mock object `mock_logger_class_level` passed to each test is specific to that test run due to `new_callable`.
        # If not, we would do: weathervane.datasources.logger.reset_mock()
        pass

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('httpx.AsyncClient')  # Remove new_callable=AsyncMock
    async def test_get_weather_success_first_try(self, mock_async_client_class, mock_sleep, mock_logger_class_level):
        # Set up async context manager
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = HTTP_OK
        mock_response.elapsed = MagicMock()
        mock_response.elapsed.total_seconds.return_value = 0.1  # 100 ms

        # Mock the json() method to return actual dict
        expected_data = {"actual": {"actual": "data"}}
        mock_response.json.return_value = expected_data

        mock_client_instance.get.return_value = mock_response

        data_source = BuienRadarDataSource(queue=None, stations=[], bits=[])

        result = await data_source._BuienRadarDataSource__get_weather()

        # Your code returns r.json(), which is a dict, not a string
        self.assertEqual(result, expected_data)
        mock_client_instance.get.assert_called_once_with("https://data.buienradar.nl/2.0/feed/json", timeout=5)
        mock_sleep.assert_not_called()
        mock_logger_class_level.info.assert_any_call("Weather data retrieved in 100 ms on attempt 1")

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('httpx.AsyncClient')  # Remove new_callable=AsyncMock
    async def test_get_weather_success_after_retries_req_error(self, mock_async_client_class, mock_sleep,
                                                               mock_logger_class_level):
        # Set up async context manager
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_failure_exception = httpx.RequestError("Simulated network error", request=MagicMock())

        # Create successful response mock
        mock_successful_response = Mock()
        mock_successful_response.status_code = HTTP_OK
        mock_successful_response.elapsed = MagicMock()
        mock_successful_response.elapsed.total_seconds.return_value = 0.1
        expected_data = {"success": True}
        mock_successful_response.json.return_value = expected_data

        mock_client_instance.get.side_effect = [
            mock_failure_exception,
            mock_failure_exception,
            mock_successful_response
        ]

        data_source = BuienRadarDataSource(queue=None, stations=[], bits=[])
        result = await data_source._BuienRadarDataSource__get_weather()

        self.assertEqual(expected_data, result)
        self.assertEqual(mock_client_instance.get.call_count, 3)
        mock_sleep.assert_has_calls([call(10), call(10)])
        self.assertEqual(mock_sleep.call_count, 2)

        # Check log calls
        mock_logger_class_level.warning.assert_any_call(
            "Attempt 1/4: RequestError connecting to Buienradar: Simulated network error")
        mock_logger_class_level.warning.assert_any_call(
            "Attempt 2/4: RequestError connecting to Buienradar: Simulated network error")
        mock_logger_class_level.info.assert_any_call("Weather data retrieved in 100 ms on attempt 3")

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('httpx.AsyncClient')  # Remove new_callable=AsyncMock
    async def test_get_weather_success_after_retries_status_code(self, mock_async_client_class, mock_sleep,
                                                                 mock_logger_class_level):
        # Set up async context manager
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_failure_response = Mock()
        mock_failure_response.status_code = 500
        mock_failure_response.elapsed = MagicMock()
        mock_failure_response.elapsed.total_seconds.return_value = 0.05  # 50ms

        mock_successful_response = Mock()
        mock_successful_response.status_code = HTTP_OK
        mock_successful_response.elapsed = MagicMock()
        mock_successful_response.elapsed.total_seconds.return_value = 0.1  # 100ms
        # Mock the json() method to return actual dict
        expected_data = {"success": True}
        mock_successful_response.json.return_value = expected_data

        mock_client_instance.get.side_effect = [
            mock_failure_response,
            mock_failure_response,
            mock_successful_response
        ]

        data_source = BuienRadarDataSource(queue=None, stations=[], bits=[])
        result = await data_source._BuienRadarDataSource__get_weather()

        # Your code returns r.json(), which is a dict, not a string
        self.assertEqual(result, expected_data)
        self.assertEqual(mock_client_instance.get.call_count, 3)
        mock_sleep.assert_has_calls([call(10), call(10)])
        self.assertEqual(mock_sleep.call_count, 2)

        mock_logger_class_level.warning.assert_any_call(
            "Attempt 1/4: Got response in 50 ms, but unexpected status code 500")
        mock_logger_class_level.warning.assert_any_call(
            "Attempt 2/4: Got response in 50 ms, but unexpected status code 500")
        mock_logger_class_level.info.assert_any_call("Weather data retrieved in 100 ms on attempt 3")

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('httpx.AsyncClient')  # Remove new_callable=AsyncMock
    async def test_get_weather_failure_all_retries_request_error(self, mock_async_client_class, mock_sleep,
                                                                 mock_logger_class_level):
        # Create a proper async context manager mock
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_failure_exception = httpx.RequestError("Simulated persistent network error", request=MagicMock())
        # max_retries = 3, so 4 attempts total
        mock_client_instance.get.side_effect = [mock_failure_exception] * 4

        data_source = BuienRadarDataSource(queue=None, stations=[], bits=[])

        with pytest.raises(httpx.RequestError):
            await data_source._BuienRadarDataSource__get_weather()

        self.assertEqual(mock_client_instance.get.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)  # Sleeps between 4 attempts
        mock_sleep.assert_has_calls([call(10)] * 3)
        mock_logger_class_level.error.assert_any_call("All 4 attempts to connect to Buienradar failed.")
        # Check that specific warnings for each attempt were logged
        for i in range(1, 5):  # Attempts 1 through 4
            mock_logger_class_level.warning.assert_any_call(
                f"Attempt {i}/4: RequestError connecting to Buienradar: Simulated persistent network error")

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @patch('httpx.AsyncClient')  # Remove new_callable=AsyncMock
    async def test_get_weather_failure_all_retries_status_code(self, mock_async_client_class, mock_sleep,
                                                               mock_logger_class_level):
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_failure_response = AsyncMock()
        mock_failure_response.status_code = 503
        mock_failure_response.text = '{"error":"unavailable"}'
        mock_failure_response.elapsed = MagicMock()
        mock_failure_response.elapsed.total_seconds.return_value = 0.05

        mock_client_instance.get.return_value = mock_failure_response  # Use return_value, not side_effect

        data_source = BuienRadarDataSource(queue=None, stations=[], bits=[])

        with pytest.raises(ConnectionError) as cm:
            await data_source._BuienRadarDataSource__get_weather()

        self.assertEqual(str(cm.value), "Buienradar: 503")  # Use cm.value, not cm.exception
        self.assertEqual(mock_client_instance.get.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)
        mock_sleep.assert_has_calls([call(10)] * 3)
        mock_logger_class_level.error.assert_any_call("All 4 attempts to connect to Buienradar failed.")
        for i in range(1, 5):
            mock_logger_class_level.warning.assert_any_call(
                f"Attempt {i}/4: Got response in 50 ms, but unexpected status code 503")