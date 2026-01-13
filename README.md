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

### View Comprehensive Dashboard

```bash
# Live updating dashboard (refreshes every 5 seconds)
uv run battery-cycles top

# Custom refresh interval (in seconds)
uv run battery-cycles top --refresh 10

# Show once without live updates
uv run battery-cycles top --no-live
```

Shows a comprehensive dashboard with all key battery metrics in one view:
- Current battery status (capacity, power, voltage, health) with timestamp
- Last charging session details
- Last discharging session details
- Battery information (capacity, cycle count, manufacturer)

The dashboard automatically refreshes and adapts to your terminal size. Press Ctrl+C to exit. This is the quickest way to monitor your battery in real-time.

**Example Output:**
```
╭─────────────────────────── Current Battery Status ───────────────────────────╮
│   Status:      Charging                                                      │
│   Capacity:    17%                                                           │
│   Power:       36.1 W                                                        │
│   Voltage:     15.94 V                                                       │
│   Energy:      8.5 Wh                                                        │
│   Health:      78.8%                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────── Last Charge ─────────────╮╭─────────── Last Discharge ───────────╮
│ When:         2 hours ago            ││ When:         3 hours ago            │
│ Range:        25% → 100%             ││ Range:        100% → 27%             │
│ Duration:     1h 45m                 ││ Duration:     2h 30m                 │
│ Energy:       36.6 Wh                ││ Avg Power:    38.5 W                 │
│ Time:         2026-01-13 11:30 AM    ││ Energy:       35.6 Wh                │
│ Used Since:   73%                    ││ Time:         2026-01-13 01:15 PM    │
╰──────────────────────────────────────╯╰──────────────────────────────────────╯
╭──────────────────────────── Battery Information ─────────────────────────────╮
│   Current Capacity:       48.8 Wh        Total Readings:       150          │
│   Design Capacity:        62.0 Wh        Charge Sessions:      12           │
│   Cycle Count:            0              Manufacturer:         ASUSTeK       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### View Current Battery Status

```bash
uv run battery-cycles status
```

Shows current battery level, status, power draw, voltage, health, and information about the last charging session.

**Example Output:**
```
╭─────────────────────────────── Battery Status ───────────────────────────────╮
│   Status:            Discharging                                             │
│   Capacity:          27%                                                     │
│   Power Draw:        41.5 W                                                  │
│   Voltage:           15.94 V                                                 │
│   Energy Now:        13.2 Wh                                                 │
│   Battery Health:    78.8%                                                   │
│   Cycle Count:       0                                                       │
│   Battery:           ASUSTeK ASUS Battery                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
Capacity ━━━━━━━━━━╸                               27%

╭────────────────────────── Last Charging Session ─────────────────────────────╮
│   Last Charged:        2 hours ago                                           │
│   Charged To:          100%                                                  │
│   Duration:            1h 45m                                                │
│   Energy Gained:       36.6 Wh                                               │
│   Started At:          2026-01-13 11:30 AM                                   │
│   Discharging Since:   2 hours ago                                           │
│   Capacity Used:       73%                                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### View Battery History

```bash
# Show recent readings
uv run battery-cycles history --limit 20

# Show today's readings
uv run battery-cycles history --today

# Show this week's readings
uv run battery-cycles history --week
```

**Example Output:**
```
                         Battery History
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Timestamp           ┃ Capacity ┃   Status    ┃  Power ┃ Health ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ 2026-01-13 02:07 PM │      43% │ Discharging │ 34.9 W │  78.8% │
│ 2026-01-13 02:08 PM │      41% │ Discharging │ 40.0 W │  78.8% │
│ 2026-01-13 02:09 PM │      39% │ Discharging │ 44.2 W │  78.8% │
│ 2026-01-13 02:10 PM │      38% │ Discharging │ 45.8 W │  78.8% │
│ 2026-01-13 02:11 PM │      36% │ Discharging │ 47.6 W │  78.8% │
└─────────────────────┴──────────┴─────────────┴────────┴────────┘

Showing 5 readings
```

### View Charging Sessions

```bash
# Show recent charging sessions (completed only)
uv run battery-cycles sessions charging

# Show all charging sessions including incomplete ones
uv run battery-cycles sessions charging --all

# Show last 5 charging sessions
uv run battery-cycles sessions charging -n 5

# Show recent discharging sessions (completed only)
uv run battery-cycles sessions discharging

# Show all discharging sessions including incomplete ones
uv run battery-cycles sessions discharging --all
```

**Example Output (Charging Sessions):**
```
                    Recent Charging Sessions
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Date                ┃ From  ┃    To ┃ Duration ┃ Energy      ┃
┃                     ┃       ┃       ┃          ┃ Gained      ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 2026-01-13 11:30 AM │   25% │  100% │   1h 45m │ 36.6 Wh     │
│ 2026-01-12 09:15 AM │   15% │   95% │   2h 10m │ 39.1 Wh     │
│ 2026-01-11 10:00 PM │   30% │  100% │   1h 30m │ 34.2 Wh     │
└─────────────────────┴───────┴───────┴──────────┴─────────────┘
```

**Example Output (With --all flag, showing incomplete sessions):**
```
              Recent Charging Sessions (Including Incomplete)
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Date                ┃ From ┃ To ┃ Duration ┃ Energy Gained ┃   Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 2026-01-13 02:23 PM │  17% │  ? │      N/A │           N/A │ In Progress │
│ 2026-01-13 11:30 AM │  25% │ 100% │   1h 45m │ 36.6 Wh     │ Complete    │
└─────────────────────┴──────┴────┴──────────┴───────────────┴─────────────┘
```

**Example Output (Discharging Sessions):**
```
                    Recent Discharging Sessions
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ Date                ┃  From ┃  To ┃ Duration ┃ Avg     ┃ Energy    ┃
┃                     ┃       ┃     ┃          ┃ Power   ┃ Used      ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ 2026-01-13 01:15 PM │  100% │ 27% │   2h 30m │  38.5 W │ 35.6 Wh   │
│ 2026-01-12 02:00 PM │   95% │ 20% │   3h 15m │  32.2 W │ 36.6 Wh   │
│ 2026-01-11 03:30 PM │  100% │ 25% │   2h 45m │  36.1 W │ 36.6 Wh   │
└─────────────────────┴───────┴─────┴──────────┴─────────┴───────────┘
```

### View Battery Health

```bash
uv run battery-cycles health
```

Shows battery health percentage, capacity degradation, cycle count, and statistics.

**Example Output:**
```
╭─────────────────────────────── Battery Health ───────────────────────────────╮
│   Current Health:      78.8%                                                 │
│   Current Capacity:    48.8 Wh                                               │
│   Design Capacity:     62.0 Wh                                               │
│   Capacity Loss:       13.1 Wh (21.2%)                                       │
│   Cycle Count:         0                                                     │
│   Technology:          Li-ion                                                │
│   Manufacturer:        ASUSTeK                                               │
│   Model:               ASUS Battery                                          │
╰──────────────────────────────────────────────────────────────────────────────╯

╭───────────────────────────────── Statistics ─────────────────────────────────╮
│   Total Readings:    23                                                      │
│   Health Change:     No change                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
```

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

# Show comprehensive dashboard
just top

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

### Understanding Sessions

A **session** is a database record that tracks a continuous period of battery activity:

- **Charging Session**: Starts when the battery begins charging and ends when it stops. Tracks energy gained, duration, and capacity change.
- **Discharging Session**: Starts when the battery begins discharging and ends when charging begins. Tracks energy consumed, average power draw, and capacity used.

Sessions can be in two states:
- **Complete**: The session has ended (battery state changed or system detected end)
- **In Progress**: The session is currently active and hasn't ended yet

By default, the `sessions` commands only show completed sessions. Use the `--all` or `-a` flag to see incomplete/in-progress sessions as well.

**Note**: Sessions require continuous data collection via cron. If there are gaps in data collection (e.g., system was off), sessions may remain incomplete until the next state transition is detected.

## License

MIT
