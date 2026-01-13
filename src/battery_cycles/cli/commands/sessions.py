"""Battery sessions command."""

import logging

import click
from rich.console import Console
from rich.table import Table
from sqlalchemy import desc

from battery_cycles.database.connection import get_database
from battery_cycles.database.models import ChargingSession, DischargeSession
from battery_cycles.utils.time_utils import format_datetime, format_duration
from battery_cycles.utils.unit_conversions import format_watt_hours, format_watts

logger = logging.getLogger(__name__)
console = Console()


@click.group("sessions")
def sessions_cmd():
    """View charging and discharging sessions."""
    pass


@sessions_cmd.command("charging")
@click.option("--limit", "-n", default=10, help="Number of sessions to show")
@click.pass_context
def charging_sessions(ctx, limit):
    """Show recent charging sessions."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Get recent charging sessions
            sessions = (
                session.query(ChargingSession)
                .filter(ChargingSession.is_complete == True)  # noqa: E712
                .order_by(desc(ChargingSession.session_end))
                .limit(limit)
                .all()
            )

            if not sessions:
                console.print("[yellow]No charging sessions recorded yet.[/yellow]")
                return

            # Create table
            table = Table(title="Recent Charging Sessions", show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("From", justify="right")
            table.add_column("To", justify="right", style="green")
            table.add_column("Duration", justify="right")
            table.add_column("Energy Gained", justify="right")

            for s in sessions:
                energy_str = "N/A"
                if s.energy_gained:
                    energy_wh = s.energy_gained / 1_000_000
                    energy_str = format_watt_hours(energy_wh)

                table.add_row(
                    format_datetime(s.session_end),
                    f"{s.start_capacity}%",
                    f"{s.end_capacity}%",
                    format_duration(s.duration_minutes),
                    energy_str,
                )

            console.print()
            console.print(table)
            console.print()

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get charging sessions: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@sessions_cmd.command("discharging")
@click.option("--limit", "-n", default=10, help="Number of sessions to show")
@click.pass_context
def discharging_sessions(ctx, limit):
    """Show recent discharging sessions."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Get recent discharge sessions
            sessions = (
                session.query(DischargeSession)
                .filter(DischargeSession.is_complete == True)  # noqa: E712
                .order_by(desc(DischargeSession.session_end))
                .limit(limit)
                .all()
            )

            if not sessions:
                console.print("[yellow]No discharging sessions recorded yet.[/yellow]")
                return

            # Create table
            table = Table(title="Recent Discharging Sessions", show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("From", justify="right", style="green")
            table.add_column("To", justify="right")
            table.add_column("Duration", justify="right")
            table.add_column("Avg Power", justify="right")
            table.add_column("Energy Used", justify="right")

            for s in sessions:
                avg_power_str = "N/A"
                if s.average_power_draw:
                    avg_power_str = format_watts(s.average_power_draw)

                energy_str = "N/A"
                if s.energy_consumed:
                    energy_wh = s.energy_consumed / 1_000_000
                    energy_str = format_watt_hours(energy_wh)

                table.add_row(
                    format_datetime(s.session_end),
                    f"{s.start_capacity}%",
                    f"{s.end_capacity}%",
                    format_duration(s.duration_minutes),
                    avg_power_str,
                    energy_str,
                )

            console.print()
            console.print(table)
            console.print()

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get discharging sessions: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
