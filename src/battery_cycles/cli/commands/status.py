"""Battery status command."""

import logging

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from sqlalchemy import desc

from battery_cycles.collector.battery_reader import BatteryReader
from battery_cycles.database.connection import get_database
from battery_cycles.database.models import ChargingSession
from battery_cycles.utils.time_utils import (
    format_datetime,
    format_duration,
    format_time_ago,
)
from battery_cycles.utils.unit_conversions import (
    format_volts,
    format_watt_hours,
    format_watts,
)

logger = logging.getLogger(__name__)
console = Console()


def get_status_color(status: str) -> str:
    """Get color for battery status.

    Args:
        status: Battery status string

    Returns:
        Rich color name
    """
    status_colors = {
        "Charging": "green",
        "Discharging": "yellow",
        "Full": "blue",
        "Not charging": "cyan",
        "Unknown": "red",
    }
    return status_colors.get(status, "white")


def get_capacity_color(capacity: int) -> str:
    """Get color for capacity level.

    Args:
        capacity: Capacity percentage

    Returns:
        Rich color name
    """
    if capacity >= 80:
        return "green"
    elif capacity >= 50:
        return "yellow"
    elif capacity >= 20:
        return "orange"
    else:
        return "red"


@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show current battery status and last charge info."""
    config = ctx.obj["config"]

    try:
        # Read current battery state
        reader = BatteryReader(config.battery_device)
        reading = reader.read()

        # Get database for last charge info
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Get last charging session
            last_charge = (
                session.query(ChargingSession)
                .filter(ChargingSession.is_complete == True)  # noqa: E712
                .order_by(desc(ChargingSession.session_end))
                .first()
            )

            # Build status display
            status_color = get_status_color(reading.status)
            capacity_color = get_capacity_color(reading.capacity_percent)

            # Create main status table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Label", style="bold")
            table.add_column("Value")

            table.add_row(
                "Status:",
                f"[{status_color}]{reading.status}[/{status_color}]",
            )

            # Capacity with progress bar
            table.add_row(
                "Capacity:",
                f"[{capacity_color}]{reading.capacity_percent}%[/{capacity_color}]",
            )

            # Power draw
            if reading.power_now:
                table.add_row("Power Draw:", format_watts(reading.power_watts()))

            # Voltage
            if reading.voltage_now:
                table.add_row("Voltage:", format_volts(reading.voltage_volts()))

            # Energy remaining
            if reading.energy_now:
                table.add_row("Energy Now:", format_watt_hours(reading.energy_now_wh()))

            # Battery health
            health = reading.health_percentage()
            if health:
                health_color = (
                    "green" if health >= 80 else "yellow" if health >= 60 else "red"
                )
                table.add_row(
                    "Battery Health:",
                    f"[{health_color}]{health:.1f}%[/{health_color}]",
                )

            # Cycle count
            if reading.cycle_count is not None:
                table.add_row("Cycle Count:", str(reading.cycle_count))

            # Manufacturer and model
            if reading.manufacturer and reading.model_name:
                table.add_row(
                    "Battery:",
                    f"{reading.manufacturer} {reading.model_name}",
                )

            console.print()
            console.print(
                Panel(
                    table,
                    title="[bold]Battery Status[/bold]",
                    border_style="blue",
                )
            )

            # Show capacity as progress bar
            progress = Progress(
                TextColumn("[bold]{task.description}"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                expand=False,
            )

            with progress:
                progress.add_task(
                    "Capacity",
                    total=100,
                    completed=reading.capacity_percent,
                )

            # Last charge info and discharging status
            if last_charge:
                charge_table = Table(show_header=False, box=None, padding=(0, 2))
                charge_table.add_column("Label", style="bold")
                charge_table.add_column("Value")

                charge_table.add_row(
                    "Last Charged:",
                    format_time_ago(last_charge.session_end),
                )
                charge_table.add_row(
                    "Charged To:",
                    f"[green]{last_charge.end_capacity}%[/green]",
                )

                if last_charge.duration_minutes:
                    charge_table.add_row(
                        "Duration:",
                        format_duration(last_charge.duration_minutes),
                    )

                if last_charge.energy_gained:
                    energy_gained_wh = last_charge.energy_gained / 1_000_000
                    charge_table.add_row(
                        "Energy Gained:",
                        format_watt_hours(energy_gained_wh),
                    )

                charge_table.add_row(
                    "Started At:",
                    format_datetime(last_charge.session_start),
                )

                # If currently discharging, show how long since last charge
                if reading.status == "Discharging":
                    charge_table.add_row(
                        "Discharging Since:",
                        format_time_ago(last_charge.session_end),
                    )

                    # Show capacity drop
                    capacity_drop = last_charge.end_capacity - reading.capacity_percent
                    if capacity_drop > 0:
                        charge_table.add_row(
                            "Capacity Used:",
                            f"[yellow]{capacity_drop}%[/yellow]",
                        )

                console.print()
                console.print(
                    Panel(
                        charge_table,
                        title="[bold]Last Charging Session[/bold]",
                        border_style="green",
                    )
                )
            else:
                console.print()
                console.print("[yellow]No charging sessions recorded yet.[/yellow]")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get status: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
