"""iRacing data collection module using pyirsdk."""

import logging
from typing import Dict, Any, Optional
import irsdk

logger = logging.getLogger(__name__)


class IRacingDataCollector:
    """Handles connection and data collection from iRacing."""

    def __init__(self):
        """Initialize the iRacing data collector."""
        self.ir = irsdk.IRSDK()
        self._connected = False

    def connect(self) -> bool:
        """
        Connect to iRacing.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            if self.ir.startup():
                self._connected = True
                logger.info("Successfully connected to iRacing")
                return True
            logger.warning("Failed to connect to iRacing - is the sim running?")
            return False
        except Exception as e:
            logger.error(f"Error connecting to iRacing: {e}")
            return False

    def disconnect(self):
        """Disconnect from iRacing."""
        if self._connected:
            self.ir.shutdown()
            self._connected = False
            logger.info("Disconnected from iRacing")

    def is_connected(self) -> bool:
        """
        Check if connected to iRacing.
        
        Returns:
            bool: Connection status
        """
        if not self._connected:
            return False
        
        # Check if iRacing is still running
        if self.ir.is_initialized and self.ir.is_connected:
            return True
        
        self._connected = False
        return False

    def get_telemetry(self) -> Optional[Dict[str, Any]]:
        """
        Get current telemetry data from iRacing.
        
        Returns:
            Dict with telemetry data or None if not available
        """
        if not self.is_connected():
            return None

        try:
            # Freeze data to ensure consistency
            if not self.ir.freeze_var_buffer_latest():
                return None

            telemetry = {
                "speed": self.ir["Speed"],
                "rpm": self.ir["RPM"],
                "gear": self.ir["Gear"],
                "throttle": self.ir["Throttle"],
                "brake": self.ir["Brake"],
                "steering_wheel_angle": self.ir["SteeringWheelAngle"],
                "lap": self.ir["Lap"],
                "lap_dist_pct": self.ir["LapDistPct"],
                "fuel_level": self.ir["FuelLevel"],
                "fuel_level_pct": self.ir["FuelLevelPct"],
                "engine_warnings": self.ir["EngineWarnings"],
            }

            return telemetry
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            return None

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get session information from iRacing.
        
        Returns:
            Dict with session info or None if not available
        """
        if not self.is_connected():
            return None

        try:
            session_info = self.ir["SessionInfo"]
            
            if not session_info:
                return None

            # Extract key session data
            info = {
                "track_name": self.ir["WeekendInfo"]["TrackDisplayName"] if "WeekendInfo" in session_info else "Unknown",
                "track_config": self.ir["WeekendInfo"]["TrackConfigName"] if "WeekendInfo" in session_info else "",
                "session_type": self.ir["SessionInfo"]["Sessions"][self.ir["SessionNum"]]["SessionType"] if "SessionInfo" in session_info else "Unknown",
                "session_time": self.ir["SessionTime"],
                "session_time_remain": self.ir["SessionTimeRemain"],
                "air_temp": self.ir["AirTemp"],
                "track_temp": self.ir["TrackTemp"],
                "sky_condition": self.ir["Skies"],
            }

            return info
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None

    def get_car_info(self) -> Optional[Dict[str, Any]]:
        """
        Get car information from iRacing.
        
        Returns:
            Dict with car info or None if not available
        """
        if not self.is_connected():
            return None

        try:
            car_info = {
                "car_id": self.ir["CarIdxClassPosition"],
                "player_car_idx": self.ir["PlayerCarIdx"],
                "car_class_short_name": self.ir["PlayerCarClassShortName"],
                "is_on_track": self.ir["IsOnTrack"],
                "is_in_garage": self.ir["IsInGarage"],
            }

            return car_info
        except Exception as e:
            logger.error(f"Error getting car info: {e}")
            return None

    def get_position_info(self) -> Optional[Dict[str, Any]]:
        """
        Get position and standings information.
        
        Returns:
            Dict with position info or None if not available
        """
        if not self.is_connected():
            return None

        try:
            position_info = {
                "position": self.ir["CarIdxPosition"][self.ir["PlayerCarIdx"]] if self.ir["PlayerCarIdx"] is not None else 0,
                "class_position": self.ir["CarIdxClassPosition"][self.ir["PlayerCarIdx"]] if self.ir["PlayerCarIdx"] is not None else 0,
                "lap_completed": self.ir["LapCompleted"],
                "laps_completed": self.ir["LapsComplete"],
                "lap_best_time": self.ir["LapBestLapTime"],
                "lap_last_time": self.ir["LapLastLapTime"],
            }

            return position_info
        except Exception as e:
            logger.error(f"Error getting position info: {e}")
            return None
