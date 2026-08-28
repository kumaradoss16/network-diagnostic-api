# Network Diagnostic API - Command Reference

All commands assume you're in the project root (`network-diagnostic-api/`, the folder that directly contains `app/`). Windows/PowerShell equivalents are shown alongside macOS/Linux/bash where they differ.

---

## 1. Setup (one-time)

```bash
# Unzip and enter the project
unzip network-diagnostic-api.zip
cd network-diagnostic-api

# Create a virtual environment
python3 -m venv venv                 # Windows: python -m venv venv

# Activate it
source venv/bin/activate             # Windows (PowerShell): venv\Scripts\Activate.ps1
                                      # Windows (cmd.exe):    venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# (Optional) copy environment template - every setting has a working default
cp .env.example .env                 # Windows: copy .env.example .env
```

---

## 2. Run the server

```bash
# Development (auto-restarts on code changes)
uvicorn app.main:app --reload

# Different port, if 8000 is already in use
uvicorn app.main:app --reload --port 8001

# Bind to all network interfaces (accessible from other devices on your LAN)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production-style (no reload, multiple workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Then open: **http://127.0.0.1:8000/docs** (Swagger UI) or **http://127.0.0.1:8000/redoc** (ReDoc).

Stop the server: **Ctrl + C** in the terminal it's running in.

---

## 3. Run the tests

```bash
pytest                  # run everything
pytest -v                # verbose - see each test by name
pytest tests/test_ping.py -v         # run a single file
pytest tests/test_ping.py::test_parse_rtts_linux_output -v   # run a single test
pytest -k "dns"           # run tests matching a keyword
```

---

## 4. Call the API from the terminal

### macOS / Linux (bash) - real `curl`
```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/api/v1/diagnostics/ping \
  -H "Content-Type: application/json" \
  -d '{"host": "example.com", "count": 4, "timeout": 2}'
```

### Windows PowerShell - `Invoke-RestMethod` (recommended)
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/ping" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"host": "example.com", "count": 4, "timeout": 2}'
```

### Windows PowerShell - real `curl.exe` (if you prefer curl syntax)
```powershell
curl.exe http://127.0.0.1:8000/health

curl.exe -X POST http://127.0.0.1:8000/api/v1/diagnostics/ping `
  -H "Content-Type: application/json" `
  -d '{"host": "example.com", "count": 4, "timeout": 2}'
```
> **Do not backslash-escape the inner double quotes** (`\"host\"`) when the JSON is wrapped in single quotes - single quotes in PowerShell are already literal, so the quotes inside need no escaping. Adding backslashes anyway gets mangled when PowerShell re-serializes the argument for `curl.exe`'s native command line, and can corrupt the request enough that you get a 404 instead of a clean response.
>
> In PowerShell, plain `curl` (no `.exe`) is aliased to `Invoke-WebRequest`, which uses different parameters and can trigger a script-parsing security prompt. Call `curl.exe` explicitly, or use `Invoke-RestMethod` instead, to avoid both issues.

---

## 5. All six diagnostic endpoints (PowerShell `Invoke-RestMethod` form)

```powershell
# Health check
Invoke-RestMethod http://127.0.0.1:8000/health

# Ping
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/ping" -Method Post `
  -ContentType "application/json" -Body '{"host": "example.com", "count": 4, "timeout": 2}'

# DNS lookup
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/dns" -Method Post `
  -ContentType "application/json" -Body '{"hostname": "example.com"}'

# TCP port check
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/port" -Method Post `
  -ContentType "application/json" -Body '{"host": "example.com", "port": 443, "timeout": 3}'

# HTTP/HTTPS check
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/http" -Method Post `
  -ContentType "application/json" -Body '{"url": "https://example.com", "timeout": 5}'

# Latency measurement
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/latency" -Method Post `
  -ContentType "application/json" -Body '{"host": "example.com", "count": 5, "timeout": 2}'

# Combined run
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/diagnostics/run" -Method Post `
  -ContentType "application/json" -Body '{"host": "example.com", "port": 443, "url": "https://example.com"}'
```

---

## 6. Deactivate / clean up

```bash
deactivate                # exit the virtual environment (same command on all OSes)
```

```bash
# Remove Python cache files (safe, regenerated automatically)
find . -type d -name "__pycache__" -exec rm -rf {} +     # macOS/Linux
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force   # PowerShell
```

---

## Quick troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | You're not in the project root. `cd` into the folder that directly contains `app/`, then re-run uvicorn. |
| `Invoke-WebRequest : Cannot bind parameter 'Headers'` | You used `curl -H ...` in PowerShell. Use `Invoke-RestMethod` (Section 4) or `curl.exe` explicitly instead. |
| Security Warning on `curl`/`Invoke-WebRequest` | Harmless for JSON APIs. Use `Invoke-RestMethod` to avoid it entirely, or add `-UseBasicParsing`. |
| `GET /` returns 404 | Expected - there's no root route. Use `/health` or `/docs`. |
| Port 8000 already in use | Run with `--port 8001` (or any free port). |
| `pytest` fails with async warnings | Confirm `pytest.ini` has `asyncio_mode = strict`. |
