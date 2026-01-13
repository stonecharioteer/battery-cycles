"""Top command - comprehensive battery dashboard."""

import logging
import time

import click
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import desc, func

from battery_cycles.collector.battery_reader import BatteryReader
from battery_cycles.database.connection import get_database
from battery_cycles.database.models import (
    BatteryReading,
    ChargingSession,
    DischargeSession,
)
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
    """Get color for battery status."""
    status_colors = {
        "Charging": "green",
        "Discharging": "yellow",
        "Full": "blue",
        "Not charging": "cyan",
        "Unknown": "red",
    }
    return status_colors.get(status, "white")


def get_capacity_color(capacity: int) -> str:
    """Get color for capacity level."""
    if capacity >= 80:
        return "green"
    elif capacity >= 50:
        return "yellow"
    elif capacity >= 20:
        return "orange"
    else:
        return "red"


def generate_dashboard(config, console_width: int) -> Layout:
    """Generate the battery dashboard layout.

    Args:
        config: Application configuration
        console_width: Terminal width for responsive layout

    Returns:
        Rich Layout with dashboard
    """
    try:
        # Read current battery state
        reader = BatteryReader(config.battery_device)
        reading = reader.read()

        # Get database
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=10),
                Layout(name="main"),
                Layout(name="footer", size=8),
            )

            # Split main into left and right (stack vertically on narrow terminals)
            if console_width >= 100:
                layout["main"].split_row(
                    Layout(name="left"),
                    Layout(name="right"),
                )
            else:
                layout["main"].split_column(
                    Layout(name="left"),
                    Layout(name="right"),
                )

            # --- HEADER: Current Status ---
            status_color = get_status_color(reading.status)
            capacity_color = get_capacity_color(reading.capacity_percent)

            header_table = Table(show_header=False, box=None, padding=(0, 2))
            header_table.add_column("Label", style="bold")
            header_table.add_column("Value")

            header_table.add_row(
                "Status:",
                f"[{status_color}]{reading.status}[/{status_color}]",
            )
            header_table.add_row(
                "Capacity:",
                f"[{capacity_color}]{reading.capacity_percent}%[/{capacity_color}]",
            )
            header_table.add_row("Power:", format_watts(reading.power_watts()))
            header_table.add_row("Voltage:", format_volts(reading.voltage_volts()))
            header_table.add_row("Energy:", format_watt_hours(reading.energy_now_wh()))

            health = reading.health_percentage()
            if health:
                health_color = (
                    "green" if health >= 80 else "yellow" if health >= 60 else "red"
                )
                header_table.add_row(
                    "Health:",
                    f"[{health_color}]{health:.1f}%[/{health_color}]",
                )

            # --- LEFT: Last Charging Session ---
            last_charge = (
                session.query(ChargingSession)
                .filter(
                    ChargingSession.is_complete.is_(True),
                    ChargingSession.end_capacity.is_not(None),
                    ChargingSession.end_capacity != ChargingSession.start_capacity,
                )
                .order_by(desc(ChargingSession.session_end))
                .first()
            )

            if last_charge:
                charge_table = Table(show_header=False, box=None, padding=(0, 1))
                charge_table.add_column("Label", style="bold cyan", width=18)
                charge_table.add_column("Value", style="white")

                charge_table.add_row("When:", format_time_ago(last_charge.session_end))
                charge_table.add_row(
                    "Range:",
                    (
                        f"{last_charge.start_capacity}% → "
                        f"[green]{last_charge.end_capacity}%[/green]"
                    ),
                )
                charge_table.add_row(
                    "Duration:", format_duration(last_charge.duration_minutes)
                )

                if last_charge.energy_gained:
                    energy_wh = last_charge.energy_gained / 1_000_000
                    charge_table.add_row("Energy:", format_watt_hours(energy_wh))

                charge_table.add_row("Time:", format_datetime(last_charge.session_end))

                # If discharging, show usage since last charge
                if reading.status == "Discharging":
                    capacity_used = last_charge.end_capacity - reading.capacity_percent
                    if capacity_used > 0:
                        charge_table.add_row(
                            "Used Since:",
                            f"[yellow]{capacity_used}%[/yellow]",
                        )

                left_panel = Panel(
                    charge_table,
                    title="[bold green]Last Charge[/bold green]",
                    border_style="green",
                )
            else:
                left_panel = Panel(
                    "[yellow]No charging sessions recorded yet[/yellow]",
                    title="[bold green]Last Charge[/bold green]",
                    border_style="green",
                )

            # --- RIGHT: Last Discharging Session ---
            last_discharge = (
                session.query(DischargeSession)
                .filter(
                    DischargeSession.is_complete.is_(True),
                    DischargeSession.end_capacity.is_not(None),
                    DischargeSession.end_capacity != DischargeSession.start_capacity,
                )
                .order_by(desc(DischargeSession.session_end))
                .first()
            )

            if last_discharge:
                discharge_table = Table(show_header=False, box=None, padding=(0, 1))
                discharge_table.add_column("Label", style="bold yellow", width=18)
                discharge_table.add_column("Value", style="white")

                discharge_table.add_row(
                    "When:", format_time_ago(last_discharge.session_end)
                )
                discharge_table.add_row(
                    "Range:",
                    (
                        f"[green]{last_discharge.start_capacity}%[/green] → "
                        f"{last_discharge.end_capacity}%"
                    ),
                )
                discharge_table.add_row(
                    "Duration:", format_duration(last_discharge.duration_minutes)
                )

                if last_discharge.average_power_draw:
                    discharge_table.add_row(
                        "Avg Power:", format_watts(last_discharge.average_power_draw)
                    )

                if last_discharge.energy_consumed:
                    energy_wh = last_discharge.energy_consumed / 1_000_000
                    discharge_table.add_row("Energy:", format_watt_hours(energy_wh))

                discharge_table.add_row(
                    "Time:", format_datetime(last_discharge.session_end)
                )

                right_panel = Panel(
                    discharge_table,
                    title="[bold yellow]Last Discharge[/bold yellow]",
                    border_style="yellow",
                )
            else:
                right_panel = Panel(
                    "[yellow]No discharge sessions recorded yet[/yellow]",
                    title="[bold yellow]Last Discharge[/bold yellow]",
                    border_style="yellow",
                )

            layout["left"].update(left_panel)
            layout["right"].update(right_panel)

            # --- FOOTER: Battery Health & Stats ---
            footer_table = Table(show_header=False, box=None, padding=(0, 2))
            footer_table.add_column("Label", style="bold magenta", width=20)
            footer_table.add_column("Value", style="white", width=25)
            footer_table.add_column("Label2", style="bold magenta", width=20)
            footer_table.add_column("Value2", style="white")

            # Row 1: Capacity info
            current_capacity = "N/A"
            design_capacity = "N/A"
            if reading.energy_full:
                current_capacity = format_watt_hours(reading.energy_full_wh())
            if reading.energy_full_design:
                design_capacity = format_watt_hours(reading.energy_full_design_wh())

            total_readings = session.query(func.count(BatteryReading.id)).scalar()
            charge_count = (
                session.query(func.count(ChargingSession.id))
                .filter(ChargingSession.is_complete == True)  # noqa: E712
                .scalar()
            )

            footer_table.add_row(
                "Current Capacity:",
                current_capacity,
                "Total Readings:",
                str(total_readings),
            )

            # Row 2: Design capacity & sessions
            footer_table.add_row(
                "Design Capacity:",
                design_capacity,
                "Charge Sessions:",
                str(charge_count),
            )

            # Row 3: Cycle count & manufacturer
            cycle_count_str = (
                str(reading.cycle_count) if reading.cycle_count is not None else "N/A"
            )
            manufacturer = reading.manufacturer or "Unknown"

            footer_table.add_row(
                "Cycle Count:",
                cycle_count_str,
                "Manufacturer:",
                manufacturer,
            )

            layout["footer"].update(
                Panel(
                    footer_table,
                    title="[bold magenta]Battery Information[/bold magenta]",
                    border_style="magenta",
                )
            )

            # Add timestamp to header
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            header_content = Group(
                header_table,
                "",
                f"[dim]Last updated: {timestamp}[/dim]",
            )

            layout["header"].update(
                Panel(
                    header_content,
                    title="[bold cyan]Current Battery Status[/bold cyan]",
                    border_style="cyan",
                )
            )

            return layout

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to generate dashboard: {e}", exc_info=True)
        # Return error layout
        error_layout = Layout()
        error_layout.update(
            Panel(
                f"[red]Error:[/red] {e}",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        return error_layout


@click.command("top")
@click.option(
    "--refresh",
    "-r",
    default=5,
    help="Refresh interval in seconds (default: 5)",
    type=int,
)
@click.option(
    "--no-live",
    is_flag=True,
    help="Disable auto-refresh (show once and exit)",
)
@click.pass_context
def top_cmd(ctx, refresh, no_live):
    """Show comprehensive battery dashboard with all key metrics.

    By default, the dashboard refreshes every 5 seconds. Press Ctrl+C to exit.
    """
    config = ctx.obj["config"]

    if no_live:
        # Show once and exit
        layout = generate_dashboard(config, console.width)
        console.print()
        console.print(layout)
        console.print()
    else:
        # Live updating mode
        try:
            with Live(
                generate_dashboard(config, console.width),
                console=console,
                refresh_per_second=1 / refresh,
                screen=True,
            ) as live:
                console.print(
                    "\n[dim]Press Ctrl+C to exit. "
                    f"Refreshing every {refresh} seconds...[/dim]\n"
                )
                while True:
                    time.sleep(refresh)
                    live.update(generate_dashboard(config, console.width))
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped.[/yellow]")
        except Exception as e:
            logger.error(f"Failed to run dashboard: {e}", exc_info=True)
            console.print(f"\n[red]Error:[/red] {e}")
            raise click.Abort()
