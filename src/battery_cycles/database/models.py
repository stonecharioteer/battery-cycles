"""Database models for battery monitoring."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class BatteryReading(Base):
    """Battery reading time-series data."""

    __tablename__ = "battery_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, index=True
    )

    # Core metrics
    capacity_percent: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Charging, Discharging, Full, etc.

    # Energy metrics (in microWatt-hours)
    energy_now: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_full: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_full_design: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Power metrics (in microWatts)
    power_now: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Voltage metrics (in microVolts)
    voltage_now: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voltage_min_design: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Battery health
    cycle_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    health_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Device info
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    technology: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capacity_level: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Normal, High, Low, Critical

    def __repr__(self) -> str:
        return (
            f"<BatteryReading(id={self.id}, timestamp={self.timestamp}, "
            f"capacity={self.capacity_percent}%, status={self.status})>"
        )


class ChargingSession(Base):
    """Detected charging session."""

    __tablename__ = "charging_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Session timing
    session_start: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    session_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Capacity metrics
    start_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    end_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # References to readings
    start_reading_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("battery_readings.id"), nullable=True
    )
    end_reading_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("battery_readings.id"), nullable=True
    )

    # Calculated metrics
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_gained: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # microWatt-hours

    # Session status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    start_reading: Mapped["BatteryReading"] = relationship(
        foreign_keys=[start_reading_id]
    )
    end_reading: Mapped["BatteryReading"] = relationship(foreign_keys=[end_reading_id])

    def __repr__(self) -> str:
        return (
            f"<ChargingSession(id={self.id}, start={self.session_start}, "
            f"{self.start_capacity}% -> {self.end_capacity}%, "
            f"complete={self.is_complete})>"
        )


class DischargeSession(Base):
    """Detected discharge session."""

    __tablename__ = "discharge_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Session timing
    session_start: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    session_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Capacity metrics
    start_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    end_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # References to readings
    start_reading_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("battery_readings.id"), nullable=True
    )
    end_reading_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("battery_readings.id"), nullable=True
    )

    # Calculated metrics
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_power_draw: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Watts
    energy_consumed: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # microWatt-hours

    # Session status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    start_reading: Mapped["BatteryReading"] = relationship(
        foreign_keys=[start_reading_id]
    )
    end_reading: Mapped["BatteryReading"] = relationship(foreign_keys=[end_reading_id])

    def __repr__(self) -> str:
        return (
            f"<DischargeSession(id={self.id}, start={self.session_start}, "
            f"{self.start_capacity}% -> {self.end_capacity}%, "
            f"complete={self.is_complete})>"
        )


class BatteryHealthSnapshot(Base):
    """Periodic snapshot of battery health metrics."""

    __tablename__ = "battery_health_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, index=True
    )

    # Health metrics
    cycle_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_full: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # microWatt-hours
    energy_full_design: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # microWatt-hours
    health_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cycles_from_data: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<BatteryHealthSnapshot(id={self.id}, timestamp={self.timestamp}, "
            f"health={self.health_percentage}%)>"
        )
