"""Shell completions command."""

import os

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command("completions")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completions_cmd(shell):
    """Install shell completions for battery-cycles.

    SHELL: Shell to install completions for (bash, zsh, or fish)
    """
    shell_configs = {
        "bash": {
            "rc_file": "~/.bashrc",
            "completion_line": (
                'eval "$(_BATTERY_CYCLES_COMPLETE=bash_source battery-cycles)"'
            ),
        },
        "zsh": {
            "rc_file": "~/.zshrc",
            "completion_line": (
                'eval "$(_BATTERY_CYCLES_COMPLETE=zsh_source battery-cycles)"'
            ),
        },
        "fish": {
            "rc_file": "~/.config/fish/completions/battery-cycles.fish",
            "completion_line": (
                "_BATTERY_CYCLES_COMPLETE=fish_source battery-cycles | source"
            ),
            "direct_file": True,
        },
    }

    config = shell_configs[shell]
    rc_file = os.path.expanduser(config["rc_file"])
    completion_line = config["completion_line"]

    # Check if fish needs directory creation
    if shell == "fish":
        fish_dir = os.path.dirname(rc_file)
        os.makedirs(fish_dir, exist_ok=True)

        # For fish, write directly to the completion file
        with open(rc_file, "w") as f:
            f.write(completion_line + "\n")

        console.print()
        console.print(
            Panel.fit(
                f"""[green]Shell completions installed for {shell}![/green]

Completion file created at:
[cyan]{rc_file}[/cyan]

Restart your shell or run:
  [yellow]source ~/.config/fish/config.fish[/yellow]

Test it:
  [yellow]battery-cycles <TAB>[/yellow]
""",
                title="Installation Complete",
                border_style="green",
            )
        )
        return

    # For bash and zsh, add to rc file if not already present
    try:
        with open(rc_file) as f:
            content = f.read()

        if completion_line in content:
            console.print(
                f"[yellow]Completions already installed in {rc_file}[/yellow]"
            )
            return

        with open(rc_file, "a") as f:
            f.write(f"\n# battery-cycles shell completion\n{completion_line}\n")

        console.print()
        console.print(
            Panel.fit(
                f"""[green]Shell completions installed for {shell}![/green]

Added to:
[cyan]{rc_file}[/cyan]

Reload your shell configuration:
  [yellow]source {rc_file}[/yellow]

Or restart your shell.

Test it:
  [yellow]battery-cycles <TAB>[/yellow]
""",
                title="Installation Complete",
                border_style="green",
            )
        )

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] {rc_file} not found")
        console.print()
        console.print("Manually add this line to your shell configuration file:")
        console.print(f"[cyan]{completion_line}[/cyan]")
