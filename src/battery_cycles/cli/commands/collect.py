"""Collect battery data command."""

import logging
import sys
from logging.handlers import RotatingFileHandler

import click

from battery_cycles.collector.data_collector import collect_reading
from battery_cycles.database.connection import get_database

logger = logging.getLogger(__name__)


def setup_rotating_log(config):
    """Set up rotating file handler for collection logs.

    Args:
        config: Application configuration
    """
    # Ensure log directory exists
    config.log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create rotating file handler
    handler = RotatingFileHandler(
        config.log_path,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
    )

    # Set format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


@click.command("collect")
@click.pass_context
def collect_cmd(ctx):
    """Collect a single battery reading (used by cron)."""
    config = ctx.obj["config"]

    # Set up rotating log file for cron mode
    setup_rotating_log(config)

    try:
        # Get database connection
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Collect reading
            reading = collect_reading(
                session,
                battery_device=config.battery_device,
                gap_threshold_minutes=config.gap_threshold_minutes,
            )

            # Log success (goes to cron log)
            logger.info(
                f"Collected: {reading.capacity_percent}% {reading.status} "
                f"(ID: {reading.id})"
            )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        # Don't print to stdout in cron mode - it goes to cron email
        sys.exit(1)
