"""Main CLI entry point for battery-cycles."""

import logging
import sys
from pathlib import Path

import click

from battery_cycles.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@click.group()
@click.option(
    "--db-path",
    type=click.Path(path_type=Path),
    help="Path to database file (overrides default)",
)
@click.option(
    "--battery",
    default="BAT0",
    help="Battery device name (default: BAT0)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.pass_context
def cli(ctx, db_path, battery, verbose):
    """Battery monitoring and analysis tool."""
    # Setup logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get config
    config = get_config()

    # Override with command line args
    if db_path:
        config.db_path = db_path
    config.battery_device = battery

    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


def main():
    """Main entry point."""
    # Import commands here to avoid circular imports
    from battery_cycles.cli.commands import (
        cheatsheet,
        collect,
        completions,
        health,
        history,
        init,
        install_cron,
        sessions,
        status,
    )

    # Register commands
    cli.add_command(init.init_cmd)
    cli.add_command(collect.collect_cmd)
    cli.add_command(status.status_cmd)
    cli.add_command(sessions.sessions_cmd)
    cli.add_command(history.history_cmd)
    cli.add_command(health.health_cmd)
    cli.add_command(install_cron.install_cron_cmd)
    cli.add_command(completions.completions_cmd)
    cli.add_command(cheatsheet.cheatsheet_cmd)

    # Run CLI
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
