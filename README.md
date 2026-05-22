# depwatch

A lightweight daemon that monitors Python and Node project dependencies for outdated or vulnerable packages.

---

## Installation

```bash
pip install depwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/depwatch.git && cd depwatch && pip install .
```

---

## Usage

Start the daemon in your project directory:

```bash
depwatch start
```

Point it at a specific project:

```bash
depwatch start --path /path/to/your/project --interval 3600
```

depwatch will automatically detect `requirements.txt` or `package.json` and begin monitoring. Alerts are logged to `~/.depwatch/depwatch.log` by default.

Check the current status of your dependencies without running the daemon:

```bash
depwatch check --path ./my-node-app
```

Stop the running daemon:

```bash
depwatch stop
```

### Example Output

```
[depwatch] Scanning Python dependencies...
[OUTDATED]  requests 2.28.0 → 2.31.0
[VULNERABLE] flask 2.0.1 — CVE-2023-30861 (High)
[OK]        click 8.1.7
```

---

## Configuration

depwatch looks for an optional `depwatch.toml` in your project root:

```toml
[depwatch]
interval = 3600       # check every hour
notify = "log"        # options: log, stdout, slack
fail_on_vuln = true
```

---

## License

MIT © 2024 [yourname](https://github.com/yourname)