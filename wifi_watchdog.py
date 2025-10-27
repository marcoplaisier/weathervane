#!/usr/bin/env python3
"""
WiFi Watchdog Script for Raspberry Pi
Monitors WiFi connectivity and reboots the system if connection is lost.
"""
import argparse
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Configuration
DEFAULT_CHECK_INTERVAL = 60  # seconds between connectivity checks
DEFAULT_FAILURE_THRESHOLD = 3  # number of consecutive failures before reboot
DEFAULT_PING_TIMEOUT = 10  # seconds to wait for ping response
LOG_FILE = "/var/log/wifi-watchdog.log"

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

# Console handler for systemd journal
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler (if we have permissions)
try:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except (PermissionError, FileNotFoundError):
    pass  # Will only log to console/journal


def check_wifi_interface():
    """
    Check if WiFi interface exists and is up.
    Returns the WiFi interface name if found, None otherwise.
    """
    try:
        # Check for wireless interfaces
        result = subprocess.run(
            ["ip", "link", "show"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Look for common WiFi interface names
        for line in result.stdout.split('\n'):
            if 'wlan' in line or 'wlp' in line:
                # Extract interface name
                interface = line.split(':')[1].strip().split('@')[0]

                # Check if interface is UP
                if 'UP' in line:
                    return interface
                else:
                    logger.warning(f"WiFi interface {interface} is DOWN")
                    return interface

        logger.error("No WiFi interface found")
        return None

    except subprocess.TimeoutExpired:
        logger.error("Timeout checking WiFi interface")
        return None
    except Exception as e:
        logger.error(f"Error checking WiFi interface: {e}")
        return None


def get_gateway_ip():
    """
    Get the default gateway IP address.
    Returns gateway IP or None if not found.
    """
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Parse output: "default via 192.168.1.1 dev wlan0 ..."
        for line in result.stdout.split('\n'):
            if 'default via' in line:
                parts = line.split()
                gateway_ip = parts[2]
                logger.debug(f"Found gateway: {gateway_ip}")
                return gateway_ip

        logger.warning("No default gateway found")
        return None

    except subprocess.TimeoutExpired:
        logger.error("Timeout getting gateway IP")
        return None
    except Exception as e:
        logger.error(f"Error getting gateway IP: {e}")
        return None


def check_connectivity(target=None, timeout=10):
    """
    Check network connectivity by pinging a target.

    Args:
        target: IP address or hostname to ping (default: gateway IP or 8.8.8.8)
        timeout: Timeout in seconds for ping command

    Returns:
        True if ping succeeds, False otherwise
    """
    if target is None:
        # Try to ping the gateway first
        target = get_gateway_ip()
        if target is None:
            # Fallback to Google DNS
            target = "8.8.8.8"
            logger.debug("Using fallback DNS server for connectivity check")

    try:
        # Ping with 1 packet, specified timeout
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), target],
            capture_output=True,
            timeout=timeout + 2
        )

        if result.returncode == 0:
            logger.debug(f"Connectivity check successful (target: {target})")
            return True
        else:
            logger.warning(f"Connectivity check failed (target: {target})")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"Ping timeout (target: {target})")
        return False
    except Exception as e:
        logger.error(f"Error checking connectivity: {e}")
        return False


def trigger_reboot(reason="WiFi connectivity lost"):
    """
    Trigger a system reboot.

    Args:
        reason: Reason for the reboot (for logging)
    """
    logger.critical(f"TRIGGERING REBOOT: {reason}")

    try:
        # Use systemctl to reboot (cleaner than direct reboot command)
        subprocess.run(
            ["systemctl", "reboot"],
            timeout=5
        )
    except subprocess.TimeoutExpired:
        logger.error("Reboot command timeout, trying direct reboot")
        try:
            subprocess.run(["reboot"], timeout=5)
        except Exception as e:
            logger.error(f"Failed to reboot: {e}")
    except Exception as e:
        logger.error(f"Error triggering reboot: {e}")
        # Try direct reboot as fallback
        try:
            subprocess.run(["reboot"], timeout=5)
        except Exception as inner_e:
            logger.error(f"Failed to reboot (fallback): {inner_e}")


def main():
    """Main watchdog loop."""
    parser = argparse.ArgumentParser(
        description="WiFi Watchdog - Monitor WiFi connectivity and reboot if connection is lost"
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=DEFAULT_CHECK_INTERVAL,
        help=f"Check interval in seconds (default: {DEFAULT_CHECK_INTERVAL})"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=DEFAULT_FAILURE_THRESHOLD,
        help=f"Number of consecutive failures before reboot (default: {DEFAULT_FAILURE_THRESHOLD})"
    )
    parser.add_argument(
        "-p", "--ping-timeout",
        type=int,
        default=DEFAULT_PING_TIMEOUT,
        help=f"Ping timeout in seconds (default: {DEFAULT_PING_TIMEOUT})"
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target IP/hostname to ping (default: gateway or 8.8.8.8)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually reboot, just log what would happen"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("WiFi Watchdog starting")
    logger.info(f"Check interval: {args.interval}s")
    logger.info(f"Failure threshold: {args.threshold}")
    logger.info(f"Ping timeout: {args.ping_timeout}s")
    if args.target:
        logger.info(f"Target: {args.target}")
    if args.dry_run:
        logger.info("DRY RUN MODE - Will not actually reboot")
    logger.info("=" * 60)

    # Check if WiFi interface exists
    wifi_interface = check_wifi_interface()
    if wifi_interface:
        logger.info(f"Monitoring WiFi interface: {wifi_interface}")
    else:
        logger.warning("No WiFi interface detected, will monitor general connectivity")

    consecutive_failures = 0
    last_success_time = datetime.now()

    while True:
        try:
            # Check connectivity
            if check_connectivity(target=args.target, timeout=args.ping_timeout):
                if consecutive_failures > 0:
                    logger.info(f"Connectivity restored after {consecutive_failures} failure(s)")
                consecutive_failures = 0
                last_success_time = datetime.now()
            else:
                consecutive_failures += 1
                downtime = (datetime.now() - last_success_time).total_seconds()

                logger.warning(
                    f"Connectivity check failed ({consecutive_failures}/{args.threshold}) - "
                    f"Down for {int(downtime)}s"
                )

                # Check if we've reached the threshold
                if consecutive_failures >= args.threshold:
                    reason = (
                        f"WiFi connectivity lost for {int(downtime)}s "
                        f"({consecutive_failures} consecutive failures)"
                    )

                    if args.dry_run:
                        logger.critical(f"DRY RUN: Would trigger reboot - {reason}")
                        consecutive_failures = 0  # Reset to avoid spamming logs
                    else:
                        trigger_reboot(reason)
                        # If we reach here, reboot failed
                        logger.error("Reboot command did not execute, will retry on next check")

            # Sleep until next check
            time.sleep(args.interval)

        except KeyboardInterrupt:
            logger.info("WiFi Watchdog stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in watchdog loop: {e}")
            # Continue running despite errors
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
