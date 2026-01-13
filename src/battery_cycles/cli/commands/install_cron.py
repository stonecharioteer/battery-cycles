"""Install cron job command."""

import logging
import shutil
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()


@click.command("install-cron")
@click.pass_context
def install_cron_cmd(ctx):
    """Install cron job for automatic data collection."""
    config = ctx.obj["config"]

    try:
        # Find the battery-cycles command path
        battery_cycles_path = shutil.which("battery-cycles")
        if not battery_cycles_path:
            # Try to use current python + module
            python_path = sys.executable
            cron_command = (
                f"* * * * * {python_path} -m battery_cycles collect "
                f">> {config.log_path} 2>&1"
            )
        else:
            cron_command = (
                f"* * * * * {battery_cycles_path} collect >> {config.log_path} 2>&1"
            )

        # Get current crontab
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False,
            )
            current_crontab = result.stdout if result.returncode == 0 else ""
        except FileNotFoundError:
            console.print("[red]Error:[/red] crontab command not found")
            raise click.Abort()

        # Check if already installed
        if "battery_cycles" in current_crontab or "battery-cycles" in current_crontab:
            console.print(
                "[yellow]Warning:[/yellow] battery-cycles cron job already exists"
            )
            if not click.confirm("Do you want to reinstall it?"):
                raise click.Abort()

            # Remove existing entries
            lines = current_crontab.split("\n")
            lines = [
                line
                for line in lines
                if "battery_cycles" not in line and "battery-cycles" not in line
            ]
            current_crontab = "\n".join(lines)

        # Add new cron job
        new_crontab = current_crontab.strip()
        if new_crontab:
            new_crontab += "\n"
        new_crontab += f"\n# Battery Cycles Data Collector\n{cron_command}\n"

        # Install crontab
        try:
            subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error:[/red] Failed to install crontab: {e}")
            raise click.Abort()

        # Success message
        console.print()
        console.print(
            Panel.fit(
                f"""[green]Cron job installed successfully![/green]

Collection will run every minute.

Cron entry:
[cyan]{cron_command}[/cyan]

Logs will be written to:
[cyan]{config.log_path}[/cyan]

Log rotation:
  Max size: 1 MB
  Backups: 3 files

To view logs:
  [yellow]tail -f {config.log_path}[/yellow]

To verify cron job:
  [yellow]crontab -l | grep battery[/yellow]

To uninstall:
  [yellow]crontab -e[/yellow]
  (remove the battery-cycles line)
""",
                title="Installation Complete",
                border_style="green",
            )
        )

    except Exception as e:
        logger.error(f"Failed to install cron job: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
