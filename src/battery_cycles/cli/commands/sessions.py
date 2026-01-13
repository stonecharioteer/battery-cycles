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
@click.option("--all", "-a", is_flag=True, help="Show incomplete sessions too")
@click.pass_context
def charging_sessions(ctx, limit, all):
    """Show recent charging sessions."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Get recent charging sessions
            query = session.query(ChargingSession)

            if not all:
                query = query.filter(ChargingSession.is_complete == True)  # noqa: E712
                order_by = desc(ChargingSession.session_end)
            else:
                order_by = desc(ChargingSession.session_start)

            sessions = query.order_by(order_by).limit(limit).all()

            if not sessions:
                console.print("[yellow]No charging sessions recorded yet.[/yellow]")
                return

            # Create table
            title = "Recent Charging Sessions" + (
                " (Including Incomplete)" if all else ""
            )
            table = Table(title=title, show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("From", justify="right")
            table.add_column("To", justify="right", style="green")
            table.add_column("Duration", justify="right")
            table.add_column("Energy Gained", justify="right")
            if all:
                table.add_column("Status", justify="center")

            for s in sessions:
                energy_str = "N/A"
                if s.energy_gained:
                    energy_wh = s.energy_gained / 1_000_000
                    energy_str = format_watt_hours(energy_wh)

                end_capacity = f"{s.end_capacity}%" if s.end_capacity else "?"
                date_str = (
                    format_datetime(s.session_end)
                    if s.session_end
                    else format_datetime(s.session_start)
                )

                row = [
                    date_str,
                    f"{s.start_capacity}%",
                    end_capacity,
                    format_duration(s.duration_minutes),
                    energy_str,
                ]

                if all:
                    status = (
                        "[green]Complete[/green]"
                        if s.is_complete
                        else "[yellow]In Progress[/yellow]"
                    )
                    row.append(status)

                table.add_row(*row)

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
@click.option("--all", "-a", is_flag=True, help="Show incomplete sessions too")
@click.pass_context
def discharging_sessions(ctx, limit, all):
    """Show recent discharging sessions."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            # Get recent discharge sessions
            query = session.query(DischargeSession)

            if not all:
                query = query.filter(DischargeSession.is_complete == True)  # noqa: E712
                order_by = desc(DischargeSession.session_end)
            else:
                order_by = desc(DischargeSession.session_start)

            sessions = query.order_by(order_by).limit(limit).all()

            if not sessions:
                console.print("[yellow]No discharging sessions recorded yet.[/yellow]")
                return

            # Create table
            title = "Recent Discharging Sessions" + (
                " (Including Incomplete)" if all else ""
            )
            table = Table(title=title, show_header=True)
            table.add_column("Date", style="cyan")
            table.add_column("From", justify="right", style="green")
            table.add_column("To", justify="right")
            table.add_column("Duration", justify="right")
            table.add_column("Avg Power", justify="right")
            table.add_column("Energy Used", justify="right")
            if all:
                table.add_column("Status", justify="center")

            for s in sessions:
                avg_power_str = "N/A"
                if s.average_power_draw:
                    avg_power_str = format_watts(s.average_power_draw)

                energy_str = "N/A"
                if s.energy_consumed:
                    energy_wh = s.energy_consumed / 1_000_000
                    energy_str = format_watt_hours(energy_wh)

                end_capacity = f"{s.end_capacity}%" if s.end_capacity else "?"
                date_str = (
                    format_datetime(s.session_end)
                    if s.session_end
                    else format_datetime(s.session_start)
                )

                row = [
                    date_str,
                    f"{s.start_capacity}%",
                    end_capacity,
                    format_duration(s.duration_minutes),
                    avg_power_str,
                    energy_str,
                ]

                if all:
                    status = (
                        "[green]Complete[/green]"
                        if s.is_complete
                        else "[yellow]In Progress[/yellow]"
                    )
                    row.append(status)

                table.add_row(*row)

            console.print()
            console.print(table)
            console.print()

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get discharging sessions: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
