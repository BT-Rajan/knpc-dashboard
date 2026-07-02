# Installation Guide

This guide walks you through setting up the KNPC Business Data Intelligence Platform on a Windows computer. Two paths are covered — pick whichever you're more comfortable with.

- [Option A: One-Click Installer](#option-a-one-click-installer-recommended) — recommended, no command line needed
- [Option B: Manual Installation](#option-b-manual-installation) — full control, works on any OS

---

## Before You Start

This repository is **private**. You need access to it (as a collaborator, or via a token) to clone or download it in the first place — there's no public download link.

You'll also need **Python 3.10 or later** installed. If you're not sure whether you have it, open Command Prompt and run:

```
python --version
```

If that fails, download Python from [python.org/downloads](https://www.python.org/downloads/). **During installation, check the box labeled "Add Python to PATH"** — it's easy to miss, and both installation methods below depend on it.

---

## Option A: One-Click Installer (recommended)

### Step 1 — Get the code

Clone or download this repository to your computer, the same way you normally would (e.g. `git clone`, or GitHub's "Download ZIP" if you have web access to the repo).

### Step 2 — Run the installer

Open the folder you just cloned/downloaded, and double-click `start.bat`.

That's it — everything from here happens automatically:

| What happens | Details |
|---|---|
| Python check | Confirms Python is installed and on your PATH. If it isn't, opens the download page for you. |
| Environment setup | Creates an isolated Python environment (`.venv`) inside the project folder, so nothing on your system Python is affected. |
| Install packages | Installs everything listed in `requirements.txt` into that isolated environment. |
| First data pull | Runs `main.py` once to populate the database with initial prices and news. |
| Launch | Starts the dashboard server and opens it in your browser automatically. |

### Step 3 — Choose how to wait

Partway through, you'll be asked:

```
While that gets going, would you like to:
  [P] Play a quick trivia game
  [W] Wait quietly and watch progress
```

- Press **P** to play a short oil & energy trivia quiz while setup finishes in the background. Your final score (e.g. `4/7`) shows the moment the dashboard is confirmed ready.
- Press **W** to watch a plain-language progress log instead.

### Step 4 — You're done

Your browser opens automatically to `http://localhost:8501` once the dashboard is live. Log in with:

- **Username:** `admin`
- **Password:** `admin`

> Change these before giving anyone else access — see [Security Notes](#security-notes) below.

### Running it again later

Just double-click `start.bat` again any time you want to relaunch the dashboard, or to pick up an update to `requirements.txt` (it reinstalls cleanly in place).

---

## Option B: Manual Installation

Use this if you're on macOS/Linux, prefer the command line, or want to understand each step.

### Step 1 — Get the code

```bash
git clone https://github.com/BT-Rajan/knpc-dashboard.git
cd knpc-dashboard
```

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

A `.env` file is already included with sensible defaults. Open it if you want to adjust:

```
ANALYTICS_LOOKBACK_DAYS=7
```

All other values in `.env` are optional overrides for data source URLs.

### Step 5 — Run the first data pull

```bash
python main.py
```

This initializes the database (`data/market_data.db`), pulls initial crude/product prices, runs the market intelligence monitoring sweep, and generates the first Excel export. Some sources may show as unavailable on the very first run — that's expected, and you can fill them in manually from the app.

### Step 6 — Launch the dashboard

```bash
streamlit run app.py
```

Open the URL it prints (usually `http://localhost:8501`) in your browser.

---

## Keeping Data Fresh

Neither installation method auto-refreshes data on a schedule. To pull fresh prices and monitor for new market developments, either:

- Click **⚙️ Control Console → Force Live Pipeline Loop** inside the app, or
- Run `python main.py` again (activate your `.venv` first if using Option B), or
- Schedule it with Windows Task Scheduler or cron — e.g. daily for prices, hourly for the market intelligence sweep.

---

## Security Notes

- **Change the default login** (`admin` / `admin`) before deploying this anywhere beyond your own machine — it's hardcoded in `app.py` and intended only as a placeholder.
- If you plan to use the AI-assisted outlook drafting feature (Settings tab), that API key is stored locally in the app's database — never commit it or share your `market_data.db` file if it's been configured.
- This repository being private does not make the app itself secure by default; treat network exposure (e.g. running it on a shared server) with the same care as any internal tool holding business data.

---

## Troubleshooting

**"Python was not found" when running `start.bat`**
Python isn't installed, or wasn't added to PATH during installation. Reinstall Python from [python.org](https://www.python.org/downloads/) and make sure to check "Add Python to PATH".

**`start.bat` closes immediately or says a file is missing**
Make sure `start.bat` is still inside the project folder — it looks for `installer\setup_and_play.py` next to itself and needs the rest of the repo to actually be there.

**Package installation fails partway through**
Usually a connectivity issue. Check your internet connection and re-run `start.bat` (or `pip install -r requirements.txt` for Option B) — it's safe to run again.

**The dashboard opens but most prices say "Source system didn't publish"**
Normal on a first run if the live data sources are temporarily unreachable or blocked by a firewall/proxy. Use the manual entry form in the Executive Overview tab, or try running the pipeline again later.

**Login screen inputs look invisible or oddly styled**
Try a hard refresh (Ctrl+Shift+R). If you're on a very old browser, consider updating it — the interface relies on modern CSS.
