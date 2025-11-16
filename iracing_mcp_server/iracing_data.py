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

    def get_environmental_conditions(self) -> Optional[Dict[str, Any]]:
        """Return a detailed snapshot of weather and track state."""
        if not self.is_connected():
            return None

        try:
            weekend_info = None
            try:
                weekend_info = self.ir["WeekendInfo"]
            except Exception:
                pass
            if not weekend_info:
                session_info = self.ir["SessionInfo"] or {}
                weekend_info = session_info.get("WeekendInfo", {})

            track_state = self.ir["SessionInfo"] or {}
            track_surface = track_state.get("WeekendInfo", {}).get("TrackSurface")

            conditions = {
                "track_name": (weekend_info or {}).get("TrackDisplayName") or (weekend_info or {}).get("TrackName"),
                "track_config": (weekend_info or {}).get("TrackConfigName"),
                "track_length": (weekend_info or {}).get("TrackLength"),
                "track_surface": track_surface,
                "track_temp": self._get_var("TrackTemp"),
                "track_temp_crew": self._get_var("TrackTempCrew"),
                "track_wetness": self._get_var("TrackWetness"),
                "air_temp": self._get_var("AirTemp"),
                "skies": self._get_var("Skies"),
                "weather_type": self._get_var("WeatherType"),
                "relative_humidity": self._get_var("RelativeHumidity"),
                "wind_speed": self._get_var("WindVel"),
                "wind_direction": self._get_var("WindDir"),
                "wind_speed_max": self._get_var("WindVelMax"),
                "fog_level": self._get_var("FogLevel"),
            }
            return conditions
        except Exception as e:
            logger.error(f"Error getting environmental conditions: {e}")
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

    def get_pit_service_status(self) -> Optional[Dict[str, Any]]:
        """Return pit road, service, and repair information for the player car."""
        if not self.is_connected():
            return None

        try:
            self.ir.freeze_var_buffer_latest()
            status = {
                "on_pit_road": self._get_var("OnPitRoad"),
                "pitstop_active": self._get_var("PitstopActive"),
                "pit_service_flags": self._get_var("PitSvFlags"),
                "pit_service_status": self._get_var("PitSvStatus"),
                "pit_service_fuel": self._get_var("PitSvFuel"),
                "pit_service_left_front_pressure": self._get_var("PitSvLFP"),
                "pit_service_right_front_pressure": self._get_var("PitSvRFP"),
                "pit_service_left_rear_pressure": self._get_var("PitSvLRP"),
                "pit_service_right_rear_pressure": self._get_var("PitSvRRP"),
                "pit_service_tire_compound": self._get_var("PitSvTireCompound"),
                "pit_repair_time_left": self._get_var("PitRepairLeft"),
                "pit_optional_repair_left": self._get_var("PitOptRepairLeft"),
                "fast_repairs_used": self._get_var("FastRepairUsed"),
                "fast_repairs_available": self._get_var("FastRepairAvailable"),
            }
            return status
        except Exception as e:
            logger.error(f"Error getting pit/service status: {e}")
            return None
        finally:
            try:
                self.ir.unfreeze_var_buffer_latest()
            except Exception:
                pass

    def _build_tire_snapshot(self, prefix: str) -> Dict[str, Any]:
        """Helper to collect tire pressure/temp/wear values for a given corner."""
        return {
            "pressure": self._get_var(f"{prefix}pressure"),
            "cold_pressure": self._get_var(f"{prefix}coldPressure"),
            "temp_inner": self._get_var(f"{prefix}tempCL"),
            "temp_middle": self._get_var(f"{prefix}tempCM"),
            "temp_outer": self._get_var(f"{prefix}tempCR"),
            "wear_inner": self._get_var(f"{prefix}wearL"),
            "wear_middle": self._get_var(f"{prefix}wearM"),
            "wear_outer": self._get_var(f"{prefix}wearR"),
        }

    def get_tire_and_brake_status(self) -> Optional[Dict[str, Any]]:
        """Return tire temps/wear and brake temperatures for each corner."""
        if not self.is_connected():
            return None

        try:
            self.ir.freeze_var_buffer_latest()
            status = {
                "left_front": self._build_tire_snapshot("LF"),
                "right_front": self._build_tire_snapshot("RF"),
                "left_rear": self._build_tire_snapshot("LR"),
                "right_rear": self._build_tire_snapshot("RR"),
                "brake_temp_left_front": self._get_var("BrakeTempFL"),
                "brake_temp_right_front": self._get_var("BrakeTempFR"),
                "brake_temp_left_rear": self._get_var("BrakeTempLR"),
                "brake_temp_right_rear": self._get_var("BrakeTempRR"),
            }
            return status
        except Exception as e:
            logger.error(f"Error getting tire/brake status: {e}")
            return None
        finally:
            try:
                self.ir.unfreeze_var_buffer_latest()
            except Exception:
                pass

    def get_driver_roster(self) -> Optional[Dict[str, Any]]:
        """Return the list of drivers, teams, and car metadata in the session."""
        if not self.is_connected():
            return None

        try:
            driver_info = self.ir["DriverInfo"] or {}
            drivers = driver_info.get("Drivers", [])
            roster = []
            for driver in drivers:
                roster.append(
                    {
                        "car_idx": driver.get("CarIdx"),
                        "user_name": driver.get("UserName"),
                        "team_name": driver.get("TeamName"),
                        "car_number": driver.get("CarNumber"),
                        "car_class": driver.get("CarClassShortName") or driver.get("CarPath"),
                        "irating": driver.get("IRating"),
                        "license": driver.get("LicString"),
                        "is_spectator": driver.get("IsSpectator"),
                    }
                )

            return {
                "driver_count": len(roster),
                "player_car_idx": driver_info.get("DriverCarIdx"),
                "drivers": roster,
            }
        except Exception as e:
            logger.error(f"Error getting driver roster: {e}")
            return None

    def get_lap_time_details(self) -> Optional[Dict[str, Any]]:
        """Return lap timing metrics including deltas to best/optimal/session."""
        if not self.is_connected():
            return None

        try:
            self.ir.freeze_var_buffer_latest()
            details = {
                "current_lap_time": self._get_var("LapCurrentLapTime"),
                "last_lap_time": self._get_var("LapLastLapTime"),
                "best_lap_time": self._get_var("LapBestLapTime"),
                "best_lap_number": self._get_var("LapBestLap"),
                "best_n_lap_time": self._get_var("LapBestNLapTime"),
                "best_n_lap_number": self._get_var("LapBestNLapLap"),
                "delta_to_best_lap": self._get_var("LapDeltaToBestLap"),
                "delta_to_best_lap_time": self._get_var("LapDeltaToBestLapTime"),
                "delta_to_optimal_lap": self._get_var("LapDeltaToOptimalLap"),
                "delta_to_session_best_lap": self._get_var("LapDeltaToSessionBestLap"),
                "delta_best_session_time": self._get_var("LapDeltaToSessionBestLapTime"),
                "lap_sector1_time": self._get_var("Sector1Time"),
                "lap_sector2_time": self._get_var("Sector2Time"),
                "lap_sector3_time": self._get_var("Sector3Time"),
            }
            return details
        except Exception as e:
            logger.error(f"Error getting lap time details: {e}")
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
