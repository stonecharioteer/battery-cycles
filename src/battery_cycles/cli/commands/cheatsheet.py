"""Cheatsheet command."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command("cheatsheet")
def cheatsheet_cmd():
    """Show a cheatsheet of all available commands."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Battery Cycles Command Cheatsheet[/bold cyan]",
            border_style="cyan",
        )
    )

    # Setup Commands
    setup_table = Table(show_header=True, header_style="bold magenta", box=None)
    setup_table.add_column("Command", style="cyan", width=30)
    setup_table.add_column("Description", style="white")

    setup_table.add_row(
        "battery-cycles init",
        "Initialize database and directories",
    )
    setup_table.add_row(
        "battery-cycles install-cron",
        "Install cron job for automatic data collection",
    )
    setup_table.add_row(
        "battery-cycles completions [shell]",
        "Install shell completions (bash, zsh, fish)",
    )

    console.print()
    console.print("[bold yellow]Setup & Installation[/bold yellow]")
    console.print(setup_table)

    # Monitoring Commands
    monitor_table = Table(show_header=True, header_style="bold magenta", box=None)
    monitor_table.add_column("Command", style="cyan", width=30)
    monitor_table.add_column("Description", style="white")

    monitor_table.add_row(
        "battery-cycles top",
        "Live dashboard (refreshes every 5s, Ctrl+C to exit)",
    )
    monitor_table.add_row(
        "battery-cycles top --refresh 10",
        "Dashboard with custom refresh interval (10s)",
    )
    monitor_table.add_row(
        "battery-cycles top --no-live",
        "Show dashboard once without auto-refresh",
    )
    monitor_table.add_row(
        "battery-cycles status",
        "Show current battery status and last charge info",
    )
    monitor_table.add_row(
        "battery-cycles collect",
        "Manually collect a single battery reading",
    )
    monitor_table.add_row(
        "battery-cycles health",
        "Show battery health and degradation stats",
    )

    console.print()
    console.print("[bold yellow]Monitoring[/bold yellow]")
    console.print(monitor_table)

    # History & Sessions Commands
    history_table = Table(show_header=True, header_style="bold magenta", box=None)
    history_table.add_column("Command", style="cyan", width=35)
    history_table.add_column("Description", style="white")

    history_table.add_row(
        "battery-cycles history",
        "Show recent battery readings",
    )
    history_table.add_row(
        "battery-cycles history --today",
        "Show today's readings only",
    )
    history_table.add_row(
        "battery-cycles history --week",
        "Show this week's readings",
    )
    history_table.add_row(
        "battery-cycles history --limit N",
        "Show last N readings",
    )

    console.print()
    console.print("[bold yellow]History[/bold yellow]")
    console.print(history_table)

    # Sessions Commands
    sessions_table = Table(show_header=True, header_style="bold magenta", box=None)
    sessions_table.add_column("Command", style="cyan", width=40)
    sessions_table.add_column("Description", style="white")

    sessions_table.add_row(
        "battery-cycles sessions charging",
        "Show recent charging sessions",
    )
    sessions_table.add_row(
        "battery-cycles sessions charging -n 5",
        "Show last 5 charging sessions",
    )
    sessions_table.add_row(
        "battery-cycles sessions discharging",
        "Show recent discharging sessions",
    )
    sessions_table.add_row(
        "battery-cycles sessions discharging -n 5",
        "Show last 5 discharging sessions",
    )

    console.print()
    console.print("[bold yellow]Sessions[/bold yellow]")
    console.print(sessions_table)

    # Common Options
    options_table = Table(show_header=True, header_style="bold magenta", box=None)
    options_table.add_column("Option", style="cyan", width=20)
    options_table.add_column("Description", style="white")

    options_table.add_row(
        "-v, --verbose",
        "Enable verbose logging",
    )
    options_table.add_row(
        "--battery NAME",
        "Specify battery device (default: BAT0)",
    )
    options_table.add_row(
        "--db-path PATH",
        "Override database path",
    )
    options_table.add_row(
        "--help",
        "Show help for any command",
    )

    console.print()
    console.print("[bold yellow]Global Options[/bold yellow]")
    console.print(options_table)

    # Quick Start
    console.print()
    console.print(
        Panel(
            """[bold green]Quick Start Guide[/bold green]

1. Initialize the system:
   [cyan]battery-cycles init[/cyan]

2. Install automatic collection:
   [cyan]battery-cycles install-cron[/cyan]

3. (Optional) Install shell completions:
   [cyan]battery-cycles completions bash[/cyan]

4. Check current status:
   [cyan]battery-cycles status[/cyan]

5. View battery history:
   [cyan]battery-cycles history --week[/cyan]

6. View charging sessions:
   [cyan]battery-cycles sessions charging[/cyan]

7. Monitor battery health:
   [cyan]battery-cycles health[/cyan]
""",
            title="Getting Started",
            border_style="green",
        )
    )

    # Tips
    console.print()
    console.print(
        Panel(
            """• Data is collected automatically every minute after cron installation
• Logs are at ~/.local/share/battery-cycles/collector.log (max 1MB)
• Database is at ~/.local/share/battery-cycles/battery.db
• Use [cyan]battery-cycles [command] --help[/cyan] for detailed help
• Tab completion works after installing completions""",
            title="[bold]Tips[/bold]",
            border_style="blue",
        )
    )
    console.print()
