import logging
import asyncio
import httpx # Ensure this is imported for RequestError
import subprocess
import time

from weathervane.parser import BuienradarParser

HTTP_OK = 200

DEFAULT_WEATHER_DATA = {
    "error": True,
    "airpressure": 900,
    "humidity": 0,
    "rain": True,
    "random": 0,
    "temperature": -39.9,
    "groundtemperature": -39.9,
    "feeltemperature": 0,
    "winddirection": "N",
    "winddirectiondegrees": 0,
    "windspeed": 0,
    "windgusts": 0,
    "windspeedBft": 0,
}

logger = logging.getLogger()


class BuienRadarDataSource:

    def __init__(self, queue, stations, bits):
        self.queue = queue
        self.bp = BuienradarParser(stations=stations, bits=bits)

    @staticmethod
    async def __get_weather():
        max_retries = 3
        retry_delay_seconds = 10
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get("https://data.buienradar.nl/2.0/feed/json", timeout=5)
                
                if r.status_code == HTTP_OK:
                    logger.info(f"Weather data retrieved in {r.elapsed.total_seconds() * 1000:.0f} ms on attempt {attempt + 1}") # Adjusted logging for timedelta
                    return r.text
                else:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries + 1}: Got response in {r.elapsed.total_seconds() * 1000:.0f} ms, but unexpected status code {r.status_code}") # Adjusted logging for timedelta
                    last_exception = ConnectionError(f"Buienradar: {r.status_code}")
                    # This ConnectionError will be caught by the broader except block below if it's the last attempt or just be part of the loop
                    # To ensure it's caught and processed by the retry logic, we raise it here.
                    raise last_exception

            except httpx.RequestError as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries + 1}: RequestError connecting to Buienradar: {e}")
                last_exception = e
            except ConnectionError as e: # Catching the specific ConnectionError from status_code check
                # The warning for non-OK status is already logged above.
                # If we want to avoid re-logging or make it less verbose:
                # logger.debug(f"Attempt {attempt + 1}/{max_retries + 1}: ConnectionError captured: {e}")
                last_exception = e # Ensure last_exception is updated

            if attempt < max_retries:
                logger.info(f"Waiting {retry_delay_seconds} seconds before retrying...")
                await asyncio.sleep(retry_delay_seconds)
            elif last_exception: # If it's the last attempt and an exception occurred
                logger.error(f"All {max_retries + 1} attempts to connect to Buienradar failed.")
                raise last_exception
        
        # Fallback if loop finishes unexpectedly (should ideally be covered by raise last_exception)
        # This part might be unreachable if last_exception is always raised on failure,
        # but it's a safeguard as per the provided example.
        logger.error("Exited retry loop for Buienradar without success or explicit error (should not happen).")
        raise ConnectionError("Failed to retrieve data from Buienradar after multiple attempts.")

    @staticmethod
    def _reboot_system():
        logger.info("Attempting system reboot using 'sudo reboot'...")
        command = ["sudo", "reboot"]
        try:
            # Using Popen for reboot as it's a non-returning command usually.
            subprocess.Popen(command)
            logger.info("Reboot command issued. The system should now restart.")
            # If Popen succeeds, script may end before this is reached or continue briefly.
            # Return True to indicate the command was dispatched without Popen throwing an error.
            return True
        except FileNotFoundError:
            logger.error("Reboot command failed: `sudo` or `reboot` not found. Ensure these utilities are installed and in PATH.")
            return False # Return False indicating command couldn't be dispatched
        except Exception as e:
            logger.error(f"An unexpected error occurred while trying to issue reboot command: {e}")
            return False # Return False indicating command couldn't be dispatched

    @staticmethod
    def _reset_wifi_connection():
        logger.info("Attempting WiFi reset using 'sudo ifdown wlan0 && sudo ifup wlan0'...")
        cmd_string = "sudo ifdown wlan0 && sudo ifup wlan0"

        try:
            # Using shell=True for the compound command.
            result = subprocess.run(cmd_string, shell=True, capture_output=True, text=True, check=False, timeout=60) 
            if result.returncode == 0:
                logger.info("WiFi reset command executed successfully.")
                logger.info("Waiting 10 seconds for network to re-establish...")
                time.sleep(10) 
                return True
            else:
                logger.error(f"WiFi reset command failed with return code {result.returncode}.")
                if result.stdout:
                    logger.error(f"STDOUT: {result.stdout.strip()}")
                if result.stderr:
                    logger.error(f"STDERR: {result.stderr.strip()}")
                return False
        except FileNotFoundError:
            logger.error("WiFi reset command failed: `sudo`, `ifdown`, or `ifup` not found. Ensure these utilities are installed and in PATH.")
            return False
        except subprocess.TimeoutExpired:
            logger.error("WiFi reset command timed out after 60 seconds.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during WiFi reset: {e}")
            return False

    async def fetch_weather_data(self):
        data = None
        try:
            data = await self.__get_weather()
        except (httpx.RequestError, ConnectionError) as e:
            logger.warning(f"Initial attempts to fetch weather data failed: {e}. Attempting WiFi reset.")
            
            # Use asyncio.to_thread for the blocking subprocess call
            wifi_reset_success = await asyncio.to_thread(self._reset_wifi_connection)

            if wifi_reset_success:
                logger.info("WiFi reset seemed successful. Attempting to fetch weather data one more time.")
                try:
                    data = await self.__get_weather() # One more try
                except (httpx.RequestError, ConnectionError) as e_after_reset:
                    logger.error(f"Fetching weather data failed even after WiFi reset: {e_after_reset}")
                    logger.info("Proceeding to system reboot due to persistent connection issues after WiFi reset.")
                    reboot_issued = await asyncio.to_thread(self._reboot_system)
                    if reboot_issued:
                        logger.info("Reboot command dispatched. No further data will be queued in this cycle.")
                        return # Exit fetch_weather_data early
                    else:
                        logger.error("System reboot command failed to dispatch. Proceeding with default weather data.")
                        data = None # Fallback to default data
                except Exception as e_generic_after_reset: # Catch any other unexpected error
                    logger.error(f"An unexpected error occurred fetching weather data after WiFi reset: {e_generic_after_reset}")
                    logger.info("Proceeding to system reboot due to unexpected error after WiFi reset.")
                    reboot_issued = await asyncio.to_thread(self._reboot_system)
                    if reboot_issued:
                        logger.info("Reboot command dispatched. No further data will be queued in this cycle.")
                        return # Exit fetch_weather_data early
                    else:
                        logger.error("System reboot command failed to dispatch. Proceeding with default weather data.")
                        data = None # Fallback to default data
            else: # wifi_reset_success is False
                logger.error("WiFi reset failed.")
                logger.info("Proceeding to system reboot due to WiFi reset failure.")
                reboot_issued = await asyncio.to_thread(self._reboot_system)
                if reboot_issued:
                    logger.info("Reboot command dispatched. No further data will be queued in this cycle.")
                    return # Exit fetch_weather_data early
                else:
                    logger.error("System reboot command failed to dispatch. Proceeding with default weather data.")
                    data = None # Fallback to default data
        except Exception as e_initial_unexpected: # Catch any other unexpected error from initial __get_weather
            logger.error(f"An unexpected error occurred during initial weather data fetch: {e_initial_unexpected}")
            data = None # Should already be None, but ensure it

        # This part is reached if:
        # 1. Initial __get_weather() succeeded.
        # 2. Reboot command failed to dispatch, and data was set to None.
        if data:
            try:
                wd = self.bp.parse(data)
            except Exception as e_parse: # Broader exception catch for parsing issues
                logger.error(f"Data parsing failed: {e_parse}. Setting error.")
                wd = DEFAULT_WEATHER_DATA
        else:
            # This 'else' is hit if data is None. This can happen if:
            # - Initial __get_weather() failed, and all subsequent recovery (WiFi reset, reboot dispatch) also failed.
            # - An unexpected error occurred in the initial fetch.
            logger.error("Setting default weather data as a last resort after other recovery attempts (including reboot dispatch failure).")
            wd = DEFAULT_WEATHER_DATA

        await self.queue.put(wd)
