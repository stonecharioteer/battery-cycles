"""Battery data reader for Linux sysfs."""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BatteryReading:
    """Structured battery reading data."""

    capacity_percent: int
    status: str
    energy_now: int | None  # microWatt-hours
    energy_full: int | None  # microWatt-hours
    energy_full_design: int | None  # microWatt-hours
    power_now: int | None  # microWatts
    voltage_now: int | None  # microVolts
    voltage_min_design: int | None  # microVolts
    cycle_count: int | None
    manufacturer: str | None
    model_name: str | None
    serial_number: str | None
    technology: str | None
    capacity_level: str | None

    def power_watts(self) -> float | None:
        """Get power draw in Watts."""
        if self.power_now is None:
            return None
        return self.power_now / 1_000_000

    def energy_now_wh(self) -> float | None:
        """Get current energy in Watt-hours."""
        if self.energy_now is None:
            return None
        return self.energy_now / 1_000_000

    def energy_full_wh(self) -> float | None:
        """Get full capacity in Watt-hours."""
        if self.energy_full is None:
            return None
        return self.energy_full / 1_000_000

    def energy_full_design_wh(self) -> float | None:
        """Get design capacity in Watt-hours."""
        if self.energy_full_design is None:
            return None
        return self.energy_full_design / 1_000_000

    def health_percentage(self) -> float | None:
        """Calculate battery health percentage."""
        if self.energy_full is None or self.energy_full_design is None:
            return None
        if self.energy_full_design == 0:
            return 100.0
        return round((self.energy_full / self.energy_full_design) * 100, 2)

    def voltage_volts(self) -> float | None:
        """Get voltage in Volts."""
        if self.voltage_now is None:
            return None
        return self.voltage_now / 1_000_000


class BatteryReader:
    """Read battery metrics from Linux sysfs."""

    def __init__(self, battery_device: str = "BAT0"):
        """Initialize battery reader.

        Args:
            battery_device: Battery device name (default: BAT0)
        """
        self.battery_device = battery_device
        self.battery_path = Path(f"/sys/class/power_supply/{battery_device}")

    def is_available(self) -> bool:
        """Check if battery device is available."""
        return self.battery_path.exists()

    def _read_file(self, filename: str) -> str | None:
        """Read a sysfs file and return its contents.

        Args:
            filename: Name of the file to read

        Returns:
            File contents stripped of whitespace, or None if read fails
        """
        file_path = self.battery_path / filename
        try:
            return file_path.read_text().strip()
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.debug(f"Could not read {filename}: {e}")
            return None

    def _read_int(self, filename: str) -> int | None:
        """Read an integer value from a sysfs file.

        Args:
            filename: Name of the file to read

        Returns:
            Integer value, or None if read/parse fails
        """
        value = self._read_file(filename)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError as e:
            logger.warning(f"Could not parse {filename} as int: {e}")
            return None

    def _parse_uevent(self) -> dict[str, str]:
        """Parse the uevent file into a dictionary.

        Returns:
            Dictionary of KEY=VALUE pairs from uevent file
        """
        uevent_content = self._read_file("uevent")
        if not uevent_content:
            return {}

        result = {}
        for line in uevent_content.split("\n"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            # Remove POWER_SUPPLY_ prefix for cleaner keys
            if key.startswith("POWER_SUPPLY_"):
                key = key[13:]  # len("POWER_SUPPLY_")
            result[key] = value

        return result

    def read(self) -> BatteryReading:
        """Read current battery state.

        Returns:
            BatteryReading with current battery metrics

        Raises:
            RuntimeError: If battery device is not available
        """
        if not self.is_available():
            raise RuntimeError(
                f"Battery device {self.battery_device} not found at {self.battery_path}"
            )

        # Parse uevent file for most metrics
        uevent = self._parse_uevent()

        # Helper to get int from uevent
        def get_int(key: str) -> int | None:
            value = uevent.get(key)
            if value is None:
                return None
            try:
                return int(value)
            except ValueError:
                return None

        # Build battery reading
        reading = BatteryReading(
            capacity_percent=get_int("CAPACITY") or 0,
            status=uevent.get("STATUS", "Unknown"),
            energy_now=get_int("ENERGY_NOW"),
            energy_full=get_int("ENERGY_FULL"),
            energy_full_design=get_int("ENERGY_FULL_DESIGN"),
            power_now=get_int("POWER_NOW"),
            voltage_now=get_int("VOLTAGE_NOW"),
            voltage_min_design=get_int("VOLTAGE_MIN_DESIGN"),
            cycle_count=get_int("CYCLE_COUNT"),
            manufacturer=uevent.get("MANUFACTURER"),
            model_name=uevent.get("MODEL_NAME"),
            serial_number=uevent.get("SERIAL_NUMBER"),
            technology=uevent.get("TECHNOLOGY"),
            capacity_level=uevent.get("CAPACITY_LEVEL"),
        )

        logger.debug(
            f"Battery reading: {reading.capacity_percent}% {reading.status} "
            f"{reading.power_watts():.1f}W"
        )

        return reading


def get_available_batteries() -> list[str]:
    """Get list of available battery devices.

    Returns:
        List of battery device names (e.g., ["BAT0", "BAT1"])
    """
    power_supply_path = Path("/sys/class/power_supply")
    if not power_supply_path.exists():
        return []

    batteries = []
    for device in power_supply_path.iterdir():
        if device.is_symlink() or device.is_dir():
            # Check if it's a battery by reading the type file
            type_file = device / "type"
            try:
                device_type = type_file.read_text().strip()
                if device_type == "Battery":
                    batteries.append(device.name)
            except (FileNotFoundError, PermissionError, OSError):
                pass

    return batteries
