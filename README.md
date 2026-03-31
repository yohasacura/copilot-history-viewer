# Copilot History Viewer

CLI tool to browse and export GitHub Copilot Chat history from VS Code and VS Code Insiders.

## Features

- Scans chat sessions from both **VS Code** and **VS Code Insiders**
- Filters sessions by date range
- Exports raw JSONL files grouped by day
- Detects multi-day sessions (sessions continued across different days)
- Zero external dependencies — Python 3.9+ stdlib only

## Usage

```bash
# Set PYTHONPATH (until you pip install -e .)
# PowerShell
$env:PYTHONPATH = "path\to\copilot-history-viewer\src"
# Bash
export PYTHONPATH="path/to/copilot-history-viewer/src"

# List all sessions
python -m copilot_history_viewer --list

# List sessions from a specific date range
python -m copilot_history_viewer --list --from 2026-01-01 --to 2026-03-31

# List only VS Code Insiders sessions
python -m copilot_history_viewer --list --edition insiders

# Export sessions to per-day JSONL files
python -m copilot_history_viewer --from 2026-03-01 --to 2026-03-31 -o ./export

# Export all sessions
python -m copilot_history_viewer -o ./export
```

## CLI Options

| Option | Description |
|---|---|
| `--list` | List sessions with metadata instead of exporting |
| `--from YYYY-MM-DD` | Start date filter (inclusive) |
| `--to YYYY-MM-DD` | End date filter (inclusive) |
| `-o, --output DIR` | Output directory for exports (default: `./export`) |
| `--edition {code,insiders,all}` | VS Code edition to scan (default: `all`) |

## Output Format

Exported files are named `YYYY-MM-DD.jsonl` — one file per day containing the raw JSONL data from all sessions created on that date. Multi-day sessions are kept intact in their creation date's file.

### List Output

```
Found 169 session(s)
  (18 session(s) span multiple days)

  2026-03-01  [     code]  a1b2c3d4-...  (12 requests)
  2026-03-01  [ insiders]  e5f6g7h8-...  (5 requests)  active: [2026-03-01, 2026-03-02]
```

Sessions spanning multiple days show an `active: [...]` suffix listing all dates with request activity.

## Where Sessions Are Stored

The tool reads from these locations on Windows (`%APPDATA%`):

| Edition | Path |
|---|---|
| VS Code | `%APPDATA%\Code\User\workspaceStorage\{id}\chatSessions\*.jsonl` |
| VS Code | `%APPDATA%\Code\User\globalStorage\emptyWindowChatSessions\*.jsonl` |
| VS Code Insiders | `%APPDATA%\Code - Insiders\User\workspaceStorage\{id}\chatSessions\*.jsonl` |
| VS Code Insiders | `%APPDATA%\Code - Insiders\User\globalStorage\emptyWindowChatSessions\*.jsonl` |

## Development

```bash
# Run tests
$env:PYTHONPATH = "src"
python -m pytest tests/ -v
```

## Project Structure

```
src/copilot_history_viewer/
├── __init__.py
├── __main__.py       # Entry point for python -m
├── cli.py            # Argparse CLI and orchestration
├── scanner.py        # Discovers .jsonl files across VS Code editions
├── parser.py         # Parses JSONL, extracts dates and activity info
└── exporter.py       # Writes per-day JSONL export files
tests/
├── test_parser.py
└── test_exporter.py
```
