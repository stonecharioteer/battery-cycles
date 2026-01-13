"""Battery history command."""

import logging
from datetime import datetime, timedelta

import click
from rich.console import Console
from rich.table import Table
from sqlalchemy import desc

from battery_cycles.database.connection import get_database
from battery_cycles.database.models import BatteryReading
from battery_cycles.utils.time_utils import format_datetime

logger = logging.getLogger(__name__)
console = Console()


@click.command("history")
@click.option("--today", is_flag=True, help="Show today's readings")
@click.option("--week", is_flag=True, help="Show this week's readings")
@click.option("--limit", "-n", default=50, help="Number of readings to show")
@click.pass_context
def history_cmd(ctx, today, week, limit):
    """View battery history."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Build query
            query = session.query(BatteryReading).order_by(
                desc(BatteryReading.timestamp)
            )

            # Apply filters
            if today:
                start_of_day = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                query = query.filter(BatteryReading.timestamp >= start_of_day)
            elif week:
                start_of_week = datetime.now() - timedelta(days=7)
                query = query.filter(BatteryReading.timestamp >= start_of_week)

            # Get readings
            readings = query.limit(limit).all()

            if not readings:
                console.print("[yellow]No battery readings recorded yet.[/yellow]")
                return

            # Create table
            table = Table(title="Battery History", show_header=True)
            table.add_column("Timestamp", style="cyan")
            table.add_column("Capacity", justify="right")
            table.add_column("Status", justify="center")
            table.add_column("Power", justify="right")
            table.add_column("Health", justify="right")

            for reading in reversed(readings):  # Show oldest first
                # Capacity color
                if reading.capacity_percent >= 80:
                    capacity_style = "green"
                elif reading.capacity_percent >= 50:
                    capacity_style = "yellow"
                elif reading.capacity_percent >= 20:
                    capacity_style = "orange"
                else:
                    capacity_style = "red"

                # Status color
                if reading.status == "Charging":
                    status_style = "green"
                elif reading.status == "Discharging":
                    status_style = "yellow"
                else:
                    status_style = "blue"

                # Power
                power_str = "N/A"
                if reading.power_now:
                    power_w = reading.power_now / 1_000_000
                    power_str = f"{power_w:.1f} W"

                # Health
                health_str = "N/A"
                if reading.health_percentage:
                    health_str = f"{reading.health_percentage:.1f}%"

                table.add_row(
                    format_datetime(reading.timestamp),
                    f"[{capacity_style}]{reading.capacity_percent}%[/{capacity_style}]",
                    f"[{status_style}]{reading.status}[/{status_style}]",
                    power_str,
                    health_str,
                )

            console.print()
            console.print(table)
            console.print()
            console.print(f"Showing {len(readings)} readings")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get history: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
