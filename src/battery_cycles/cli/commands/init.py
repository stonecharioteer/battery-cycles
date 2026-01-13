"""Initialize battery-cycles database and configuration."""

import logging

import click
from rich.console import Console
from rich.panel import Panel

from battery_cycles.database.connection import get_database

logger = logging.getLogger(__name__)
console = Console()


@click.command("init")
@click.pass_context
def init_cmd(ctx):
    """Initialize database and configuration directories."""
    config = ctx.obj["config"]

    try:
        # Ensure directories exist
        config.ensure_directories()

        # Initialize database
        db = get_database(config.db_path)
        db.init_db()

        # Display success message
        console.print(
            Panel.fit(
                f"""[green]Battery Cycles initialized successfully![/green]

Database: [cyan]{config.db_path}[/cyan]
Config: [cyan]{config.config_path.parent}[/cyan]
Logs: [cyan]{config.log_path}[/cyan]

Next steps:
  1. Run [yellow]battery-cycles collect[/yellow] to test data collection
  2. Run [yellow]battery-cycles install-cron[/yellow] to set up automatic collection
""",
                title="Initialization Complete",
                border_style="green",
            )
        )

    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
