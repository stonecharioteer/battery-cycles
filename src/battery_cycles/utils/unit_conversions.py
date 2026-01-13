"""Unit conversion utilities."""


def microwatts_to_watts(microwatts: int | None) -> float | None:
    """Convert microWatts to Watts.

    Args:
        microwatts: Value in microWatts

    Returns:
        Value in Watts, or None if input is None
    """
    if microwatts is None:
        return None
    return microwatts / 1_000_000


def microwatt_hours_to_watt_hours(microwatt_hours: int | None) -> float | None:
    """Convert microWatt-hours to Watt-hours.

    Args:
        microwatt_hours: Value in microWatt-hours

    Returns:
        Value in Watt-hours, or None if input is None
    """
    if microwatt_hours is None:
        return None
    return microwatt_hours / 1_000_000


def microvolts_to_volts(microvolts: int | None) -> float | None:
    """Convert microVolts to Volts.

    Args:
        microvolts: Value in microVolts

    Returns:
        Value in Volts, or None if input is None
    """
    if microvolts is None:
        return None
    return microvolts / 1_000_000


def format_watts(watts: float | None, decimals: int = 1) -> str:
    """Format Watts value for display.

    Args:
        watts: Value in Watts
        decimals: Number of decimal places

    Returns:
        Formatted string like "33.9 W"
    """
    if watts is None:
        return "N/A"
    return f"{watts:.{decimals}f} W"


def format_watt_hours(watt_hours: float | None, decimals: int = 1) -> str:
    """Format Watt-hours value for display.

    Args:
        watt_hours: Value in Watt-hours
        decimals: Number of decimal places

    Returns:
        Formatted string like "36.6 Wh"
    """
    if watt_hours is None:
        return "N/A"
    return f"{watt_hours:.{decimals}f} Wh"


def format_volts(volts: float | None, decimals: int = 2) -> str:
    """Format Volts value for display.

    Args:
        volts: Value in Volts
        decimals: Number of decimal places

    Returns:
        Formatted string like "15.94 V"
    """
    if volts is None:
        return "N/A"
    return f"{volts:.{decimals}f} V"
