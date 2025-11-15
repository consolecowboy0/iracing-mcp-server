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

    def _get_var(self, name: str) -> Any:
        """Safely fetch an iRacing variable."""
        try:
            return self.ir[name]
        except KeyError:
            logger.debug("Telemetry field %s is not available in this session.", name)
            return None

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
            self.ir.freeze_var_buffer_latest()
            telemetry = {
                "speed": self._get_var("Speed"),
                "rpm": self._get_var("RPM"),
                "gear": self._get_var("Gear"),
                "throttle": self._get_var("Throttle"),
                "brake": self._get_var("Brake"),
                "steering_wheel_angle": self._get_var("SteeringWheelAngle"),
                "lap": self._get_var("Lap"),
                "lap_dist_pct": self._get_var("LapDistPct"),
                "fuel_level": self._get_var("FuelLevel"),
                "fuel_level_pct": self._get_var("FuelLevelPct"),
                "engine_warnings": self._get_var("EngineWarnings"),
            }

            return telemetry
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            return None
        finally:
            try:
                self.ir.unfreeze_var_buffer_latest()
            except Exception:
                pass

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get session information from iRacing.
        
        Returns:
            Dict with session info or None if not available
        """
        if not self.is_connected():
            return None

        try:
            session_info = self.ir["SessionInfo"] or {}
            weekend_info = self.ir["WeekendInfo"] or session_info.get("WeekendInfo", {})
            session_details = session_info.get("Sessions", [])
            session_num = self._get_var("SessionNum") or 0

            session_type = "Unknown"
            if isinstance(session_num, int) and 0 <= session_num < len(session_details):
                session_type = session_details[session_num].get("SessionType", "Unknown")

            track_name = (
                weekend_info.get("TrackDisplayName")
                or weekend_info.get("TrackDisplayShortName")
                or weekend_info.get("TrackName")
                or "Unknown"
            )

            info = {
                "track_name": track_name,
                "track_config": weekend_info.get("TrackConfigName", ""),
                "session_type": session_type,
                "session_time": self._get_var("SessionTime"),
                "session_time_remain": self._get_var("SessionTimeRemain"),
                "air_temp": self._get_var("AirTemp"),
                "track_temp": self._get_var("TrackTemp"),
                "sky_condition": self._get_var("Skies"),
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
            self.ir.freeze_var_buffer_latest()
            car_info = {
                "car_id": self._get_var("CarIdxClassPosition"),
                "player_car_idx": self._get_var("PlayerCarIdx"),
                "car_class_short_name": self._get_var("PlayerCarClassShortName"),
                "is_on_track": self._get_var("IsOnTrack"),
                "is_in_garage": self._get_var("IsInGarage"),
            }

            return car_info
        except Exception as e:
            logger.error(f"Error getting car info: {e}")
            return None
        finally:
            try:
                self.ir.unfreeze_var_buffer_latest()
            except Exception:
                pass

    def get_position_info(self) -> Optional[Dict[str, Any]]:
        """
        Get position and standings information.
        
        Returns:
            Dict with position info or None if not available
        """
        if not self.is_connected():
            return None

        try:
            self.ir.freeze_var_buffer_latest()
            player_idx = self._get_var("PlayerCarIdx")
            car_idx_position = self._get_var("CarIdxPosition") or []
            car_idx_class_position = self._get_var("CarIdxClassPosition") or []

            position_info = {
                "position": car_idx_position[player_idx] if isinstance(car_idx_position, list) and isinstance(player_idx, int) and player_idx < len(car_idx_position) else 0,
                "class_position": car_idx_class_position[player_idx] if isinstance(car_idx_class_position, list) and isinstance(player_idx, int) and player_idx < len(car_idx_class_position) else 0,
                "lap_completed": self._get_var("LapCompleted"),
                "laps_completed": self._get_var("LapsComplete"),
                "lap_best_time": self._get_var("LapBestLapTime"),
                "lap_last_time": self._get_var("LapLastLapTime"),
            }

            return position_info
        except Exception as e:
            logger.error(f"Error getting position info: {e}")
            return None
        finally:
            try:
                self.ir.unfreeze_var_buffer_latest()
            except Exception:
                pass
