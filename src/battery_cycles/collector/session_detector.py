"""Session detection for charging and discharging events."""

import logging
from datetime import timedelta
from enum import Enum

from sqlalchemy import desc
from sqlalchemy.orm import Session

from battery_cycles.database.models import (
    BatteryReading,
    ChargingSession,
    DischargeSession,
)

logger = logging.getLogger(__name__)


class StateTransition(Enum):
    """Types of state transitions."""

    NONE = "none"
    START_CHARGING = "start_charging"
    STOP_CHARGING = "stop_charging"
    START_DISCHARGING = "start_discharging"
    STOP_DISCHARGING = "stop_discharging"


class SessionDetector:
    """Detect and manage battery charging/discharging sessions."""

    def __init__(self, db_session: Session, gap_threshold_minutes: int = 5):
        """Initialize session detector.

        Args:
            db_session: SQLAlchemy database session
            gap_threshold_minutes: Minutes gap to consider session ended
        """
        self.db = db_session
        self.gap_threshold = timedelta(minutes=gap_threshold_minutes)

    def detect_transition(self, current_reading: BatteryReading) -> StateTransition:
        """Detect state transition from previous to current reading.

        Args:
            current_reading: Current battery reading

        Returns:
            Type of transition detected
        """
        # Get the previous reading
        previous_reading = (
            self.db.query(BatteryReading)
            .filter(BatteryReading.id < current_reading.id)
            .order_by(desc(BatteryReading.id))
            .first()
        )

        if not previous_reading:
            # First reading - check if currently charging or discharging
            if current_reading.status == "Charging":
                return StateTransition.START_CHARGING
            elif current_reading.status == "Discharging":
                return StateTransition.START_DISCHARGING
            return StateTransition.NONE

        # Check for gap (system sleep/hibernate)
        time_gap = current_reading.timestamp - previous_reading.timestamp
        if time_gap > self.gap_threshold:
            logger.info(f"Gap detected: {time_gap} > {self.gap_threshold}")
            # Close any open sessions due to gap
            self._close_open_sessions_due_to_gap(previous_reading)

            # Start new session based on current state
            if current_reading.status == "Charging":
                return StateTransition.START_CHARGING
            elif current_reading.status == "Discharging":
                return StateTransition.START_DISCHARGING
            return StateTransition.NONE

        # Detect transitions
        prev_status = previous_reading.status
        curr_status = current_reading.status

        # Charging transitions
        if prev_status != "Charging" and curr_status == "Charging":
            return StateTransition.START_CHARGING
        if prev_status == "Charging" and curr_status != "Charging":
            return StateTransition.STOP_CHARGING

        # Discharging transitions
        if prev_status != "Discharging" and curr_status == "Discharging":
            return StateTransition.START_DISCHARGING
        if prev_status == "Discharging" and curr_status != "Discharging":
            return StateTransition.STOP_DISCHARGING

        return StateTransition.NONE

    def process_reading(self, reading: BatteryReading) -> None:
        """Process a battery reading and handle session detection.

        Args:
            reading: Battery reading to process
        """
        transition = self.detect_transition(reading)

        if transition == StateTransition.START_CHARGING:
            self._start_charging_session(reading)
        elif transition == StateTransition.STOP_CHARGING:
            self._end_charging_session(reading)
        elif transition == StateTransition.START_DISCHARGING:
            self._start_discharge_session(reading)
        elif transition == StateTransition.STOP_DISCHARGING:
            self._end_discharge_session(reading)

        # Always update ongoing sessions even without transitions
        self._update_active_sessions(reading)

    def _start_charging_session(self, reading: BatteryReading) -> None:
        """Start a new charging session.

        Args:
            reading: Battery reading that triggered the start
        """
        logger.info(
            f"Starting charging session at {reading.capacity_percent}% "
            f"({reading.timestamp})"
        )

        session = ChargingSession(
            session_start=reading.timestamp,
            start_capacity=reading.capacity_percent,
            start_reading_id=reading.id,
            is_complete=False,
        )
        self.db.add(session)
        self.db.commit()

    def _end_charging_session(self, reading: BatteryReading) -> None:
        """End the active charging session.

        Args:
            reading: Battery reading that triggered the end
        """
        # Find the most recent incomplete charging session
        session = (
            self.db.query(ChargingSession)
            .filter(ChargingSession.is_complete == False)  # noqa: E712
            .order_by(desc(ChargingSession.session_start))
            .first()
        )

        if not session:
            logger.warning("No active charging session to end")
            return

        # Update session
        session.session_end = reading.timestamp
        session.end_capacity = reading.capacity_percent
        session.end_reading_id = reading.id
        session.is_complete = True

        # Calculate duration
        duration = reading.timestamp - session.session_start
        session.duration_minutes = int(duration.total_seconds() / 60)

        # Calculate energy gained if available
        if (
            session.start_reading
            and reading.energy_now
            and session.start_reading.energy_now
        ):
            energy_gained = reading.energy_now - session.start_reading.energy_now
            session.energy_gained = energy_gained

        self.db.commit()

        logger.info(
            f"Ended charging session: {session.start_capacity}% -> "
            f"{session.end_capacity}% in {session.duration_minutes}m"
        )

    def _start_discharge_session(self, reading: BatteryReading) -> None:
        """Start a new discharge session.

        Args:
            reading: Battery reading that triggered the start
        """
        logger.info(
            f"Starting discharge session at {reading.capacity_percent}% "
            f"({reading.timestamp})"
        )

        session = DischargeSession(
            session_start=reading.timestamp,
            start_capacity=reading.capacity_percent,
            start_reading_id=reading.id,
            is_complete=False,
        )
        self.db.add(session)
        self.db.commit()

    def _end_discharge_session(self, reading: BatteryReading) -> None:
        """End the active discharge session.

        Args:
            reading: Battery reading that triggered the end
        """
        # Find the most recent incomplete discharge session
        session = (
            self.db.query(DischargeSession)
            .filter(DischargeSession.is_complete == False)  # noqa: E712
            .order_by(desc(DischargeSession.session_start))
            .first()
        )

        if not session:
            logger.warning("No active discharge session to end")
            return

        # Update session
        session.session_end = reading.timestamp
        session.end_capacity = reading.capacity_percent
        session.end_reading_id = reading.id
        session.is_complete = True

        # Calculate duration
        duration = reading.timestamp - session.session_start
        session.duration_minutes = int(duration.total_seconds() / 60)

        # Calculate energy consumed and average power if available
        if (
            session.start_reading
            and reading.energy_now
            and session.start_reading.energy_now
        ):
            energy_consumed = session.start_reading.energy_now - reading.energy_now
            session.energy_consumed = energy_consumed

            # Calculate average power draw in Watts
            if session.duration_minutes > 0:
                energy_consumed_wh = energy_consumed / 1_000_000  # Convert to Wh
                duration_hours = session.duration_minutes / 60
                session.average_power_draw = energy_consumed_wh / duration_hours

        self.db.commit()

        logger.info(
            f"Ended discharge session: {session.start_capacity}% -> "
            f"{session.end_capacity}% in {session.duration_minutes}m"
        )

    def _update_active_sessions(self, reading: BatteryReading) -> None:
        """Update any active sessions with latest reading.

        This allows tracking sessions even when status doesn't change.

        Args:
            reading: Current battery reading
        """
        # This could be extended to update intermediate metrics
        # For now, we only create/end sessions on transitions
        pass

    def _close_open_sessions_due_to_gap(self, last_reading: BatteryReading) -> None:
        """Close any open sessions due to a gap in readings.

        Args:
            last_reading: Last reading before the gap
        """
        # Close any incomplete charging sessions
        charging_sessions = (
            self.db.query(ChargingSession)
            .filter(ChargingSession.is_complete == False)  # noqa: E712
            .all()
        )

        for session in charging_sessions:
            session.session_end = last_reading.timestamp
            session.end_capacity = last_reading.capacity_percent
            session.end_reading_id = last_reading.id
            session.is_complete = True

            duration = last_reading.timestamp - session.session_start
            session.duration_minutes = int(duration.total_seconds() / 60)

            logger.info(f"Closed charging session due to gap: {session}")

        # Close any incomplete discharge sessions
        discharge_sessions = (
            self.db.query(DischargeSession)
            .filter(DischargeSession.is_complete == False)  # noqa: E712
            .all()
        )

        for session in discharge_sessions:
            session.session_end = last_reading.timestamp
            session.end_capacity = last_reading.capacity_percent
            session.end_reading_id = last_reading.id
            session.is_complete = True

            duration = last_reading.timestamp - session.session_start
            session.duration_minutes = int(duration.total_seconds() / 60)

            logger.info(f"Closed discharge session due to gap: {session}")

        self.db.commit()
