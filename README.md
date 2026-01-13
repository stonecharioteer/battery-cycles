# battery-cycles

A battery monitoring service for Linux that tracks battery metrics and provides rich terminal visualizations.

## Features

- **Automatic Data Collection**: Collects battery metrics every minute via cron
- **Rich Terminal UI**: Beautiful terminal visualizations with colors, tables, and progress bars
- **Session Tracking**: Automatically detects and tracks charging/discharging sessions
- **Health Monitoring**: Track battery health degradation over time
- **SQLite Storage**: All data stored locally in a SQLite database
- **Zero Configuration**: Works out of the box with sensible defaults

## Installation

### Prerequisites

- Linux system with `/sys/class/power_supply/` support
- Python 3.10 or higher
- UV package manager

### Install from Source

```bash
# Clone the repository
git clone <repo-url>
cd battery-cycles

# Create virtual environment and install
uv sync

# Initialize the database
uv run battery-cycles init

# Install cron job for automatic collection
uv run battery-cycles install-cron

# (Optional) Install shell completions
uv run battery-cycles completions bash  # or zsh, fish
```

### Shell Completions

Battery-cycles supports tab completion for Bash, Zsh, and Fish shells:

```bash
# For Bash
uv run battery-cycles completions bash

# For Zsh
uv run battery-cycles completions zsh

# For Fish
uv run battery-cycles completions fish
```

After installation, restart your shell or source your shell configuration file. Then you can use tab completion:

```bash
battery-cycles <TAB>      # Shows available commands
battery-cycles sessions <TAB>  # Shows subcommands
```

## Usage

### Quick Reference

For a comprehensive cheatsheet of all available commands:

```bash
uv run battery-cycles cheatsheet
```

This displays an organized reference with command syntax, examples, and quick start guide.

### View Current Battery Status

```bash
uv run battery-cycles status
```

Shows current battery level, status, power draw, voltage, health, and information about the last charging session.

### View Battery History

```bash
# Show recent readings
uv run battery-cycles history --limit 20

# Show today's readings
uv run battery-cycles history --today

# Show this week's readings
uv run battery-cycles history --week
```

### View Charging Sessions

```bash
# Show recent charging sessions
uv run battery-cycles sessions charging

# Show recent discharging sessions
uv run battery-cycles sessions discharging
```

### View Battery Health

```bash
uv run battery-cycles health
```

Shows battery health percentage, capacity degradation, cycle count, and statistics.

### Manual Data Collection

```bash
uv run battery-cycles collect
```

Collects a single battery reading. This is automatically done every minute by cron after installation.

## Development

### Using Just

This project uses [just](https://github.com/casey/just) for common tasks:

```bash
# Sync dependencies
just sync

# Format code
just format

# Lint code
just lint

# Format and fix issues
just fmt

# Run type checking
just typecheck

# Show battery status
just status

# Show battery history
just history

# Show battery health
just health

# Show command cheatsheet
just cheatsheet
```

### Project Structure

```
battery-cycles/
├── src/battery_cycles/
│   ├── collector/         # Data collection and session detection
│   │   ├── battery_reader.py
│   │   ├── data_collector.py
│   │   └── session_detector.py
│   ├── database/          # Database models and connection
│   │   ├── models.py
│   │   └── connection.py
│   ├── cli/               # CLI commands and visualizers
│   │   ├── main.py
│   │   ├── commands/
│   │   └── visualizers/
│   ├── utils/             # Utility functions
│   └── config.py          # Configuration management
├── pyproject.toml
├── justfile
└── README.md
```

## Configuration

Battery-cycles uses XDG-compliant directories:

- Database: `~/.local/share/battery-cycles/battery.db`
- Config: `~/.config/battery-cycles/`
- Logs: `~/.local/share/battery-cycles/collector.log`

### Log Rotation

The collector log file automatically rotates when it reaches 1 MB in size. The system keeps 3 backup files (`collector.log.1`, `collector.log.2`, `collector.log.3`) before deleting old logs. This ensures log files don't grow indefinitely while preserving recent history.

## How It Works

1. **Data Collection**: Every minute, the cron job reads battery metrics from `/sys/class/power_supply/BAT0/` and stores them in SQLite
2. **Session Detection**: The system detects state transitions (charging ↔ discharging) and creates session records
3. **Visualization**: CLI commands query the database and display rich terminal output using the Rich library

## License

[Add your license here]
