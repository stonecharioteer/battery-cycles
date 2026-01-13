# Battery Cycles Justfile

# Sync dependencies with UV
sync:
    uv sync

# Install dependencies with UV
install:
    uv sync --all-extras

# Format Python code with ruff
format:
    uv run ruff format src/

# Check code formatting
check-format:
    uv run ruff format --check src/

# Lint code with ruff
lint:
    uv run ruff check src/

# Fix linting issues
fix:
    uv run ruff check --fix src/

# Run type checking with mypy
typecheck:
    uv run mypy src/battery_cycles/

# Run tests
test:
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    uv run pytest tests/ --cov=battery_cycles --cov-report=html --cov-report=term

# Format and lint all code
check: check-format lint

# Format and fix all issues
fmt: format fix

# Clean temporary files and caches
clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/ .coverage htmlcov/
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Show battery info from sysfs (for debugging)
show-battery:
    cat /sys/class/power_supply/BAT0/uevent

# Initialize battery-cycles
init:
    uv run battery-cycles init

# Collect a battery reading
collect:
    uv run battery-cycles collect

# Show comprehensive battery dashboard
top:
    uv run battery-cycles top

# Show current battery status
status:
    uv run battery-cycles status

# Show battery history
history:
    uv run battery-cycles history --limit 20

# Show charging sessions
sessions-charging:
    uv run battery-cycles sessions charging

# Show discharging sessions
sessions-discharging:
    uv run battery-cycles sessions discharging

# Show battery health
health:
    uv run battery-cycles health

# Show command cheatsheet
cheatsheet:
    uv run battery-cycles cheatsheet
