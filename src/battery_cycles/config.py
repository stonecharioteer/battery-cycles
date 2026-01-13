"""Configuration management for battery-cycles."""

import logging
from pathlib import Path

from platformdirs import user_config_path, user_data_path

logger = logging.getLogger(__name__)

# Application name for XDG directories
APP_NAME = "battery-cycles"

# Default configuration paths (XDG-compliant)
DEFAULT_DATA_DIR = user_data_path(APP_NAME, ensure_exists=False)
DEFAULT_CONFIG_DIR = user_config_path(APP_NAME, ensure_exists=False)
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "battery.db"
DEFAULT_LOG_PATH = DEFAULT_DATA_DIR / "collector.log"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"


class Config:
    """Application configuration."""

    def __init__(
        self,
        db_path: Path | None = None,
        log_path: Path | None = None,
        config_path: Path | None = None,
        battery_device: str = "BAT0",
        log_level: str = "INFO",
    ):
        """Initialize configuration.

        Args:
            db_path: Path to SQLite database
            log_path: Path to log file
            config_path: Path to config file
            battery_device: Battery device name
            log_level: Logging level
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.log_path = log_path or DEFAULT_LOG_PATH
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.battery_device = battery_device
        self.log_level = log_level

        # Session detection settings
        self.gap_threshold_minutes = 5  # Consider session ended after this gap
        self.min_charge_duration_seconds = (
            30  # Ignore very short charges (likely measurement noise)
        )

        # Logging settings
        self.log_max_bytes = 1_000_000  # 1 MB
        self.log_backup_count = 3  # Keep 3 backup files

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directories exist: {self.db_path.parent}")


def get_config() -> Config:
    """Get default configuration.

    Returns:
        Config instance with default settings
    """
    return Config()
