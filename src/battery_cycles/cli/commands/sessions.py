"""Battery sessions command."""

import logging

import click
from rich.console import Console
from rich.table import Table
from sqlalchemy import desc

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
from battery_cycles.utils.unit_conversions import format_watt_hours, format_watts

logger = logging.getLogger(__name__)
console = Console()


@click.group("sessions", invoke_without_command=True)
@click.pass_context
def sessions_cmd(ctx):
    """View charging and discharging sessions."""
    if ctx.invoked_subcommand is not None:
        return

    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            latest_reading = (
                session.query(BatteryReading)
                .order_by(desc(BatteryReading.id))
                .first()
            )
            if not latest_reading:
                console.print("[yellow]No battery readings recorded yet.[/yellow]")
                return

            status = latest_reading.status
            active_session = None
            if status == "Charging":
                active_session = (
                    session.query(ChargingSession)
                    .filter(ChargingSession.is_complete.is_(False))
                    .order_by(desc(ChargingSession.session_start))
                    .first()
                )
            elif status == "Discharging":
                active_session = (
                    session.query(DischargeSession)
                    .filter(DischargeSession.is_complete.is_(False))
                    .order_by(desc(DischargeSession.session_start))
                    .first()
                )

            if not active_session:
                console.print(
                    f"[yellow]No active session for status '{status}'.[/yellow]"
                )
                return

            duration_minutes = None
            if active_session.session_start:
                duration = latest_reading.timestamp - active_session.session_start
                duration_minutes = int(duration.total_seconds() / 60)

            capacity_delta = None
            if status == "Charging":
                capacity_delta = (
                    latest_reading.capacity_percent - active_session.start_capacity
                )
            elif status == "Discharging":
                capacity_delta = (
                    active_session.start_capacity - latest_reading.capacity_percent
                )

            energy_str = "N/A"
            if (
                active_session.start_reading
                and active_session.start_reading.energy_now
                and latest_reading.energy_now
            ):
                if status == "Charging":
                    energy_delta = (
                        latest_reading.energy_now
                        - active_session.start_reading.energy_now
                    )
                else:
                    energy_delta = (
                        active_session.start_reading.energy_now
                        - latest_reading.energy_now
                    )
                energy_str = format_watt_hours(energy_delta / 1_000_000)

            table = Table(title="Current Session", show_header=False)
            table.add_column("Label", style="bold cyan", width=18)
            table.add_column("Value", style="white")

            table.add_row("Status:", status)
            table.add_row(
                "Started:",
                f"{format_datetime(active_session.session_start)} "
                f"({format_time_ago(active_session.session_start)})",
            )
            table.add_row("Duration:", format_duration(duration_minutes))
            table.add_row("Start:", f"{active_session.start_capacity}%")
            table.add_row("Current:", f"{latest_reading.capacity_percent}%")
            if capacity_delta is not None:
                table.add_row("Change:", f"{capacity_delta}%")
            table.add_row("Energy:", energy_str)
            table.add_row(
                "Last Reading:",
                f"{format_datetime(latest_reading.timestamp)} "
                f"({format_time_ago(latest_reading.timestamp)})",
            )

            console.print()
            console.print(table)
            console.print()

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get current session: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


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


@sessions_cmd.command("repair")
@click.pass_context
def repair_sessions(ctx):
    """Repair overlapping discharge sessions."""
    config = ctx.obj["config"]

    try:
        db = get_database(config.db_path)
        session = db.get_session_direct()

        try:
            repaired = 0
            discharge_sessions = (
                session.query(DischargeSession)
                .order_by(DischargeSession.session_start.asc())
                .all()
            )

            for ds in discharge_sessions:
                charging_start = (
                    session.query(BatteryReading)
                    .filter(
                        BatteryReading.timestamp >= ds.session_start,
                        BatteryReading.status == "Charging",
                    )
                    .order_by(BatteryReading.timestamp.asc())
                    .first()
                )
                if not charging_start:
                    continue

                if ds.session_end and ds.session_end < charging_start.timestamp:
                    continue

                last_discharging = (
                    session.query(BatteryReading)
                    .filter(
                        BatteryReading.timestamp < charging_start.timestamp,
                        BatteryReading.status == "Discharging",
                    )
                    .order_by(BatteryReading.timestamp.desc())
                    .first()
                )
                if not last_discharging:
                    continue

                ds.session_end = last_discharging.timestamp
                ds.end_capacity = last_discharging.capacity_percent
                ds.end_reading_id = last_discharging.id
                ds.is_complete = True

                duration = ds.session_end - ds.session_start
                ds.duration_minutes = int(duration.total_seconds() / 60)

                if (
                    ds.start_reading
                    and ds.start_reading.energy_now
                    and last_discharging.energy_now
                ):
                    energy_consumed = (
                        ds.start_reading.energy_now - last_discharging.energy_now
                    )
                    ds.energy_consumed = energy_consumed
                    if ds.duration_minutes > 0:
                        energy_consumed_wh = energy_consumed / 1_000_000
                        duration_hours = ds.duration_minutes / 60
                        ds.average_power_draw = energy_consumed_wh / duration_hours

                repaired += 1

            session.commit()

            if repaired:
                console.print(
                    f"[green]Repaired {repaired} discharge session(s).[/green]"
                )
            else:
                console.print("[yellow]No discharge sessions needed repair.[/yellow]")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to repair sessions: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
