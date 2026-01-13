"""Data collector for battery metrics."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from battery_cycles.collector.battery_reader import BatteryReader
from battery_cycles.collector.session_detector import SessionDetector
from battery_cycles.database.models import BatteryReading

logger = logging.getLogger(__name__)


class DataCollector:
    """Orchestrates battery data collection and storage."""

    def __init__(
        self,
        db_session: Session,
        battery_device: str = "BAT0",
        gap_threshold_minutes: int = 5,
    ):
        """Initialize data collector.

        Args:
            db_session: SQLAlchemy database session
            battery_device: Battery device name
            gap_threshold_minutes: Minutes gap for session detection
        """
        self.db = db_session
        self.reader = BatteryReader(battery_device)
        self.detector = SessionDetector(db_session, gap_threshold_minutes)

    def collect(self) -> BatteryReading:
        """Collect a single battery reading and store it.

        Returns:
            The stored BatteryReading object

        Raises:
            RuntimeError: If battery device is not available
        """
        # Read battery data
        reading_data = self.reader.read()

        # Create database record
        reading = BatteryReading(
            timestamp=datetime.now(),
            capacity_percent=reading_data.capacity_percent,
            status=reading_data.status,
            energy_now=reading_data.energy_now,
            energy_full=reading_data.energy_full,
            energy_full_design=reading_data.energy_full_design,
            power_now=reading_data.power_now,
            voltage_now=reading_data.voltage_now,
            voltage_min_design=reading_data.voltage_min_design,
            cycle_count=reading_data.cycle_count,
            health_percentage=reading_data.health_percentage(),
            manufacturer=reading_data.manufacturer,
            model_name=reading_data.model_name,
            serial_number=reading_data.serial_number,
            technology=reading_data.technology,
            capacity_level=reading_data.capacity_level,
        )

        # Store in database
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)

        logger.info(
            f"Collected reading: {reading.capacity_percent}% "
            f"{reading.status} at {reading.timestamp}"
        )

        # Process for session detection
        try:
            self.detector.process_reading(reading)
        except Exception as e:
            logger.error(f"Error in session detection: {e}", exc_info=True)
            # Don't fail collection if session detection fails

        return reading


def collect_reading(
    db_session: Session,
    battery_device: str = "BAT0",
    gap_threshold_minutes: int = 5,
) -> BatteryReading:
    """Convenience function to collect a single reading.

    Args:
        db_session: SQLAlchemy database session
        battery_device: Battery device name
        gap_threshold_minutes: Minutes gap for session detection

    Returns:
        The stored BatteryReading object
    """
    collector = DataCollector(db_session, battery_device, gap_threshold_minutes)
    return collector.collect()
