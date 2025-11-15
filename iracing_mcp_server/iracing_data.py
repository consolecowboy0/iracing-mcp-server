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

    def _get_driver_metadata(self, car_idx: int, field: str) -> Any:
        """Return metadata for the given driver index (if available)."""
        try:
            driver_info = self.ir["DriverInfo"] or {}
            drivers = driver_info.get("Drivers", [])
            if isinstance(car_idx, int) and 0 <= car_idx < len(drivers):
                return drivers[car_idx].get(field)
        except Exception:
            logger.debug("Driver metadata %s unavailable for car_idx %s", field, car_idx)
        return None

    def _get_track_length_meters(self) -> Optional[float]:
        """Return track length in meters if available."""
        weekend_info = None
        try:
            weekend_info = self.ir["WeekendInfo"]
        except Exception:
            pass
        if not weekend_info:
            try:
                weekend_info = (self.ir["SessionInfo"] or {}).get("WeekendInfo", {})
            except Exception:
                weekend_info = {}
        length_str = (weekend_info or {}).get("TrackLength")
        if not length_str:
            return None
        parts = length_str.replace(",", "").split()
        if not parts:
            return None
        try:
            value = float(parts[0])
        except ValueError:
            return None
        unit = parts[1].lower() if len(parts) > 1 else "m"
        if unit.startswith("km"):
            return value * 1000.0
        if unit.startswith("mi"):
            return value * 1609.34
        if unit.startswith("m"):
            return value
        if unit.startswith("ft"):
            return value * 0.3048
        return None

    def get_surroundings(self, count: int = 3) -> Optional[Dict[str, Any]]:
        """
        Return nearby cars ahead/behind the player.

        Args:
            count: Number of cars to include ahead/behind (default 3, max 10).
        """
        if not self.is_connected():
            return None

        count = max(1, min(10, count or 3))

        try:
            self.ir.freeze_var_buffer_latest()
            player_idx = self._get_var("PlayerCarIdx")
            player_dist = self._get_var("LapDistPct")
            if player_idx is None or player_dist is None:
                return None

            car_dists = self._get_var("CarIdxLapDistPct") or []
            car_speeds = self._get_var("CarIdxSpeed") or []
            car_positions = self._get_var("CarIdxPosition") or []
            car_class_positions = self._get_var("CarIdxClassPosition") or []
            car_surfaces = self._get_var("CarIdxTrackSurface") or []

            track_length_m = self._get_track_length_meters()
            player_driver = {
                "name": self._get_driver_metadata(player_idx, "UserName") or self._get_driver_metadata(player_idx, "CarNumber") or f"Car {player_idx}",
                "car_number": self._get_driver_metadata(player_idx, "CarNumber") or str(player_idx),
                "team": self._get_driver_metadata(player_idx, "TeamName"),
            }

            entries: list[Dict[str, Any]] = []
            for idx, dist in enumerate(car_dists):
                if idx == player_idx:
                    continue
                if dist is None or dist < 0 or not isinstance(dist, (int, float)):
                    continue
                relative = float(dist) - float(player_dist)
                if relative > 0.5:
                    relative -= 1.0
                elif relative < -0.5:
                    relative += 1.0
                if relative == 0:
                    continue
                relative_pct = relative * 100.0
                gap_meters = track_length_m * relative if track_length_m is not None else None

                entry = {
                    "car_idx": idx,
                    "name": self._get_driver_metadata(idx, "UserName") or self._get_driver_metadata(idx, "CarNumber") or f"Car {idx}",
                    "car_number": self._get_driver_metadata(idx, "CarNumber") or str(idx),
                    "position": car_positions[idx] if isinstance(car_positions, (list, tuple)) and 0 <= idx < len(car_positions) else None,
                    "class_position": car_class_positions[idx] if isinstance(car_class_positions, (list, tuple)) and 0 <= idx < len(car_class_positions) else None,
                    "speed": car_speeds[idx] if isinstance(car_speeds, (list, tuple)) and 0 <= idx < len(car_speeds) else None,
                    "track_surface": car_surfaces[idx] if isinstance(car_surfaces, (list, tuple)) and 0 <= idx < len(car_surfaces) else None,
                    "relative_lap_dist_pct": round(relative_pct, 4),
                    "gap_meters": round(gap_meters, 2) if gap_meters is not None else None,
                }
                entries.append(entry)

            ahead = sorted(
                [car for car in entries if car["relative_lap_dist_pct"] > 0],
                key=lambda car: car["relative_lap_dist_pct"],
            )[:count]
            behind = sorted(
                [car for car in entries if car["relative_lap_dist_pct"] < 0],
                key=lambda car: abs(car["relative_lap_dist_pct"]),
            )[:count]

            player_summary = {
                "car_idx": player_idx,
                "name": player_driver["name"],
                "car_number": player_driver["car_number"],
                "position": car_positions[player_idx] if isinstance(car_positions, (list, tuple)) and isinstance(player_idx, int) and 0 <= player_idx < len(car_positions) else None,
                "class_position": car_class_positions[player_idx] if isinstance(car_class_positions, (list, tuple)) and isinstance(player_idx, int) and 0 <= player_idx < len(car_class_positions) else None,
            }

            return {
                "player": player_summary,
                "cars_ahead": ahead,
                "cars_behind": behind,
                "track_length_m": track_length_m,
            }
        except Exception as e:
            logger.error(f"Error getting surroundings info: {e}")
            return None
        finally:
            try:
                self.ir.unfreeze_var_buffer_latest()
            except Exception:
                pass
