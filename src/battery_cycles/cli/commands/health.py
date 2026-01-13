"""Battery health command."""

import logging

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import desc, func

from battery_cycles.database.connection import get_database
from battery_cycles.database.models import BatteryReading
from battery_cycles.utils.unit_conversions import format_watt_hours

logger = logging.getLogger(__name__)
console = Console()


@click.command("health")
@click.pass_context
def health_cmd(ctx):
    """Show battery health information."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Get latest reading with health info
            latest = (
                session.query(BatteryReading)
                .order_by(desc(BatteryReading.timestamp))
                .first()
            )

            if not latest:
                console.print("[yellow]No battery readings recorded yet.[/yellow]")
                return

            # Calculate health metrics
            health_table = Table(show_header=False, box=None, padding=(0, 2))
            health_table.add_column("Label", style="bold")
            health_table.add_column("Value")

            # Current health
            if latest.health_percentage:
                health = latest.health_percentage
                health_color = (
                    "green" if health >= 80 else "yellow" if health >= 60 else "red"
                )
                health_table.add_row(
                    "Current Health:",
                    f"[{health_color}]{health:.1f}%[/{health_color}]",
                )

            # Capacity info
            if latest.energy_full and latest.energy_full_design:
                current_wh = latest.energy_full / 1_000_000
                design_wh = latest.energy_full_design / 1_000_000

                health_table.add_row(
                    "Current Capacity:",
                    format_watt_hours(current_wh),
                )
                health_table.add_row(
                    "Design Capacity:",
                    format_watt_hours(design_wh),
                )

                degradation_wh = design_wh - current_wh
                degradation_pct = (degradation_wh / design_wh) * 100
                health_table.add_row(
                    "Capacity Loss:",
                    f"{format_watt_hours(degradation_wh)} ({degradation_pct:.1f}%)",
                )

            # Cycle count
            if latest.cycle_count is not None:
                health_table.add_row("Cycle Count:", str(latest.cycle_count))

            # Battery info
            if latest.technology:
                health_table.add_row("Technology:", latest.technology)

            if latest.manufacturer:
                health_table.add_row("Manufacturer:", latest.manufacturer)

            if latest.model_name:
                health_table.add_row("Model:", latest.model_name)

            console.print()
            console.print(
                Panel(
                    health_table,
                    title="[bold]Battery Health[/bold]",
                    border_style="blue",
                )
            )

            # Statistics from all readings
            total_readings = session.query(func.count(BatteryReading.id)).scalar()

            if total_readings > 1:
                # Get earliest reading with health data
                earliest = (
                    session.query(BatteryReading)
                    .filter(BatteryReading.health_percentage.isnot(None))
                    .order_by(BatteryReading.timestamp)
                    .first()
                )

                if earliest and latest and earliest.health_percentage:
                    stats_table = Table(show_header=False, box=None, padding=(0, 2))
                    stats_table.add_column("Label", style="bold")
                    stats_table.add_column("Value")

                    stats_table.add_row("Total Readings:", str(total_readings))

                    # Health change
                    health_change = (
                        latest.health_percentage - earliest.health_percentage
                    )
                    health_change_str = (
                        f"{health_change:+.2f}%" if health_change != 0 else "No change"
                    )
                    stats_table.add_row("Health Change:", health_change_str)

                    console.print()
                    console.print(
                        Panel(
                            stats_table,
                            title="[bold]Statistics[/bold]",
                            border_style="cyan",
                        )
                    )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get health info: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
