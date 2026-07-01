#!/usr/bin/env python3
"""
KNPC Business Data Intelligence Platform — Console Setup
==========================================================
Runs the full install (download -> venv -> pip install -> first data pull
-> launch dashboard) in a background thread, while the terminal in front
of you either plays a trivia quiz or shows plain-language progress —
your choice. No GUI toolkit required, just the Python standard library.
"""
import os
import re
import sys
import time
import queue
import random
import shutil
import zipfile
import threading
import subprocess
import urllib.request
import webbrowser
from pathlib import Path

IS_WINDOWS = (os.name == "nt")
if IS_WINDOWS:
    import msvcrt
    # Legacy Command Prompt defaults to a code page that mangles emoji/
    # UTF-8 output, and doesn't process ANSI color codes unless enabled.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.system("chcp 65001 >nul 2>nul")
    os.system("")  # enables ANSI escape processing in cmd.exe

# ------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------
GITHUB_USER = "BT-Rajan"
GITHUB_REPO = "knpc-dashboard"
GITHUB_BRANCH = "main"
GITHUB_ZIP_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
GAME_FILE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/installer_game.txt"
STREAMLIT_URL = "http://localhost:8501"
DEFAULT_INSTALL_DIR = Path.home() / "KNPC-Dashboard"

NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0

DEFAULT_QUESTIONS = [
    {"q": "Which crude oil benchmark is most widely referenced for North American pricing?",
     "opts": {"A": "Brent", "B": "WTI", "C": "Dubai", "D": "Urals"}, "ans": "B"},
    {"q": "What does IEA stand for?",
     "opts": {"A": "International Energy Agency", "B": "Independent Energy Alliance",
              "C": "International Export Authority", "D": "Institute of Energy Analysts"}, "ans": "A"},
    {"q": "What unit is standard for pricing crude oil globally?",
     "opts": {"A": "USD per litre", "B": "USD per barrel", "C": "USD per tonne", "D": "USD per gallon"}, "ans": "B"},
    {"q": "Which strait is considered one of the world's most important oil chokepoints?",
     "opts": {"A": "Strait of Gibraltar", "B": "Strait of Hormuz", "C": "Bering Strait", "D": "Bosphorus Strait"}, "ans": "B"},
    {"q": "What does LPG stand for?",
     "opts": {"A": "Liquefied Petroleum Gas", "B": "Low Pressure Gasoline", "C": "Light Paraffin Grade", "D": "Limited Production Guarantee"}, "ans": "A"},
    {"q": "What is a benchmark crude used for?",
     "opts": {"A": "Measuring drill bit wear", "B": "Serving as a reference price for other crude grades",
              "C": "Testing refinery safety equipment", "D": "Calibrating storage tank gauges"}, "ans": "B"},
]


# ------------------------------------------------------------------------
# SMALL CONSOLE COLOR HELPERS (ANSI — supported by modern Windows Terminal
# and cmd.exe on Windows 10+; harmless no-ops if unsupported)
# ------------------------------------------------------------------------
def _c(code, text):
    return f"\033[{code}m{text}\033[0m"


def blue(t): return _c("94", t)
def green(t): return _c("92", t)
def yellow(t): return _c("93", t)
def red(t): return _c("91", t)
def bold(t): return _c("1", t)


def banner():
    print(blue(bold("=" * 62)))
    print(blue(bold("   KNPC Business Data Intelligence Platform — Setup")))
    print(blue(bold("=" * 62)))
    print()


# ------------------------------------------------------------------------
# OUTPUT TRANSLATION — same idea as before: turn raw pip/python output
# into short, natural-language status lines instead of a wall of text.
# ------------------------------------------------------------------------
def translate_pip_line(line: str):
    line = line.strip()
    if not line:
        return None
    m = re.search(r"Collecting ([A-Za-z0-9_\-\.\[\]]+)", line)
    if m:
        return f"📦 Fetching {m.group(1)}…"
    if "Requirement already satisfied" in line:
        return None
    if line.startswith("Downloading"):
        return "⬇️  Downloading package files…"
    if "Installing collected packages" in line:
        return "🔧 Installing packages onto your system…"
    if "Successfully installed" in line:
        return "✅ All required packages are installed."
    if line.lower().startswith("error") or "ERROR:" in line:
        return f"⚠️  {line}"
    return None


def translate_main_line(line: str):
    line = line.strip()
    if not line:
        return None
    if "Ingestion" in line and "Pipeline" in line and "Complete" in line:
        return "✅ First data pull finished."
    if "'status': 'success'" in line:
        m = re.search(r"'(?:benchmark|product)':\s*'([^']+)'", line)
        name = m.group(1) if m else "the latest price"
        return f"✅ Got the latest {name} price."
    if "'status': 'manual_required'" in line:
        m = re.search(r"'(?:benchmark|product)':\s*'([^']+)'", line)
        name = m.group(1) if m else "one item"
        return f"ℹ️  Couldn't reach a live source for {name} yet — you can enter it manually later."
    m = re.search(r"developments logged this run:\s*(\d+)", line, re.IGNORECASE)
    if m:
        return f"📰 Logged {m.group(1)} market development(s)."
    if "Generated Excel" in line or "Analytical Workbook" in line:
        return "📊 Built today's Excel report."
    return None


def venv_python_path(install_dir: Path) -> Path:
    if IS_WINDOWS:
        return install_dir / ".venv" / "Scripts" / "python.exe"
    return install_dir / ".venv" / "bin" / "python"


def stream_process(cmd, cwd, out_queue, translator):
    """Runs a subprocess to completion, pushing translated lines to a queue.
    Returns the process return code."""
    process = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, creationflags=NO_WINDOW,
    )
    for raw_line in process.stdout:
        if translator:
            friendly = translator(raw_line)
            if friendly:
                out_queue.put(friendly)
    process.wait()
    return process.returncode


# ------------------------------------------------------------------------
# BACKGROUND INSTALL SEQUENCE
# ------------------------------------------------------------------------
class Installer(threading.Thread):
    def __init__(self, install_dir: Path, out_queue: queue.Queue, done_event, fail_event):
        super().__init__(daemon=True)
        self.install_dir = install_dir
        self.q = out_queue
        self.done_event = done_event
        self.fail_event = fail_event
        self.error_message = None
        self.streamlit_process = None

    def run(self):
        try:
            self._download_and_extract()
            venv_py = self._create_venv()
            self._pip_install(venv_py)
            self._run_main(venv_py)
            self._launch_streamlit(venv_py)
            self.done_event.set()
        except Exception as ex:
            self.error_message = str(ex)
            self.q.put(f"⚠️  {ex}")
            self.fail_event.set()

    def _download_and_extract(self):
        target = self.install_dir
        target.parent.mkdir(parents=True, exist_ok=True)
        self.q.put("📥 Downloading the dashboard files from GitHub…")

        zip_path = target.parent / f"{GITHUB_REPO}-download.zip"
        urllib.request.urlretrieve(GITHUB_ZIP_URL, zip_path)

        self.q.put("📂 Unpacking the files…")
        extract_root = target.parent / f"__extract_{GITHUB_REPO}"
        if extract_root.exists():
            shutil.rmtree(extract_root)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_root)

        extracted_subdirs = [p for p in extract_root.iterdir() if p.is_dir()]
        source_dir = extracted_subdirs[0] if extracted_subdirs else extract_root

        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source_dir), str(target))
        shutil.rmtree(extract_root, ignore_errors=True)
        zip_path.unlink(missing_ok=True)
        self.q.put("✅ Files are ready.")

    def _create_venv(self) -> Path:
        self.q.put("🧪 Setting up an isolated Python environment…")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(self.install_dir / ".venv")],
            capture_output=True, text=True, timeout=120, creationflags=NO_WINDOW,
        )
        venv_py = venv_python_path(self.install_dir)
        if result.returncode != 0 or not venv_py.exists():
            self.q.put("⚠️  Couldn't create an isolated environment — using your system Python instead.")
            return Path(sys.executable)
        self.q.put("✅ Isolated environment ready.")
        return venv_py

    def _pip_install(self, venv_py: Path):
        req_file = self.install_dir / "requirements.txt"
        if not req_file.exists():
            raise RuntimeError("requirements.txt wasn't found in the downloaded files.")
        rc = stream_process(
            [str(venv_py), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=str(self.install_dir), out_queue=self.q, translator=translate_pip_line,
        )
        if rc != 0:
            raise RuntimeError("Package installation failed. Check your internet connection and try again.")

    def _run_main(self, venv_py: Path):
        rc = stream_process(
            [str(venv_py), "main.py"], cwd=str(self.install_dir),
            out_queue=self.q, translator=translate_main_line,
        )
        # main.py is designed to always exit 0 even when some sources are
        # unreachable, but don't hard-fail setup over a non-zero code here —
        # the dashboard is still perfectly usable with manual entry.
        if rc != 0:
            self.q.put("⚠️  The first data pull hit a snag, but the dashboard will still work — you can enter prices manually.")

    def _launch_streamlit(self, venv_py: Path):
        self.q.put("🚀 Starting the dashboard server…")
        self.streamlit_process = subprocess.Popen(
            [str(venv_py), "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
            cwd=str(self.install_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        )
        for _ in range(60):
            try:
                urllib.request.urlopen(STREAMLIT_URL, timeout=2)
                self.q.put("✅ The dashboard server has started.")
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("The dashboard server didn't respond in time.")


# ------------------------------------------------------------------------
# QUIZ GAME
# ------------------------------------------------------------------------
def parse_questions(text: str):
    questions = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("Q:"):
            if current and current.get("ans") and len(current.get("opts", {})) == 4:
                questions.append(current)
            current = {"q": line[2:].strip(), "opts": {}}
        elif current is not None and len(line) > 2 and line[0] in "ABCD" and line[1] == ":":
            current["opts"][line[0]] = line[2:].strip()
        elif current is not None and line.startswith("ANS:"):
            current["ans"] = line[4:].strip().upper()
    if current and current.get("ans") and len(current.get("opts", {})) == 4:
        questions.append(current)
    return [q for q in questions if q["ans"] in q["opts"]]


def load_questions():
    try:
        with urllib.request.urlopen(GAME_FILE_URL, timeout=8) as resp:
            text = resp.read().decode("utf-8")
        parsed = parse_questions(text)
        if parsed:
            return parsed
    except Exception:
        pass
    return DEFAULT_QUESTIONS


def _read_answer_windows(done_event, fail_event, valid="ABCD"):
    """Non-blocking-ish keypress read that keeps checking whether setup
    has finished while waiting for the player to answer."""
    buffer = ""
    while True:
        if done_event.is_set() or fail_event.is_set():
            return None
        if msvcrt.kbhit():
            ch = msvcrt.getwche()
            if ch in ("\r", "\n"):
                print()
                if buffer.upper() in valid:
                    return buffer.upper()
                print("Please answer with A, B, C, or D, then press Enter.")
                buffer = ""
            elif ch == "\x08":
                buffer = buffer[:-1]
            elif ch.upper() in valid:
                buffer = ch.upper()
        time.sleep(0.05)


def _read_answer_basic(done_event, fail_event, valid="ABCD"):
    """Fallback for non-Windows: checked only between questions, not
    interruptible mid-keystroke, but still fully functional."""
    while True:
        if done_event.is_set() or fail_event.is_set():
            return None
        try:
            ans = input().strip().upper()
        except EOFError:
            return None
        if ans in valid:
            return ans
        print("Please answer with A, B, C, or D.")


def play_quiz(done_event, fail_event, out_queue):
    questions = load_questions()
    random.shuffle(questions)
    score, asked = 0, 0

    print(yellow(bold("🎮 Quiz time! Answer with A, B, C, or D while setup runs in the background.")))
    print(yellow("   (Setup will interrupt automatically the moment it's ready.)"))
    print()

    idx = 0
    while not done_event.is_set() and not fail_event.is_set():
        if idx >= len(questions):
            random.shuffle(questions)
            idx = 0
        q = questions[idx]
        idx += 1

        _drain_queue_to_console(out_queue)
        if done_event.is_set() or fail_event.is_set():
            break

        print(bold(f"Q{asked + 1}: {q['q']}"))
        for letter in "ABCD":
            print(f"   {letter}) {q['opts'][letter]}")
        print("Your answer: ", end="", flush=True)

        answer = _read_answer_windows(done_event, fail_event) if IS_WINDOWS else _read_answer_basic(done_event, fail_event)
        if answer is None:
            break

        asked += 1
        if answer == q["ans"]:
            score += 1
            print(green("✅ Correct!\n"))
        else:
            print(red(f"❌ Not quite — the answer was {q['ans']}) {q['opts'][q['ans']]}.\n"))

    print()
    if asked:
        print(bold(f"🏁 You scored {score}/{asked}. Nice work!"))
    print()


def _drain_queue_to_console(out_queue):
    try:
        while True:
            print(out_queue.get_nowait())
    except queue.Empty:
        pass


def wait_quietly(done_event, fail_event, out_queue):
    print(yellow("Sit tight — here's what's happening:"))
    print()
    spinner = "|/-\\"
    i = 0
    while not done_event.is_set() and not fail_event.is_set():
        _drain_queue_to_console(out_queue)
        print(f"\r{spinner[i % len(spinner)]} Working…  ", end="", flush=True)
        i += 1
        time.sleep(0.2)
    print("\r", end="")
    _drain_queue_to_console(out_queue)


def _safe_input(prompt=""):
    try:
        return input(prompt)
    except EOFError:
        return ""


# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------
def main():
    banner()
    install_dir = DEFAULT_INSTALL_DIR
    custom = _safe_input(f"Install location [{install_dir}]: ").strip()
    if custom:
        install_dir = Path(custom)

    print()
    out_queue = queue.Queue()
    done_event = threading.Event()
    fail_event = threading.Event()

    installer = Installer(install_dir, out_queue, done_event, fail_event)
    installer.start()

    print("While that gets going, would you like to:")
    print("  [P] Play a quick trivia game")
    print("  [W] Wait quietly and watch progress")
    choice = ""
    attempts = 0
    while choice not in ("P", "W"):
        try:
            choice = input("Choose P or W: ").strip().upper()
        except EOFError:
            choice = "W"  # no interactive stdin available — default to quietly waiting
            break
        attempts += 1
        if attempts > 20:
            choice = "W"
            break
    print()

    if choice == "P":
        play_quiz(done_event, fail_event, out_queue)
    else:
        wait_quietly(done_event, fail_event, out_queue)

    # In case the quiz/wait loop exited before setup truly finished
    # (e.g. player ran out of patience), block here until it does.
    while not done_event.is_set() and not fail_event.is_set():
        _drain_queue_to_console(out_queue)
        time.sleep(0.5)
    _drain_queue_to_console(out_queue)

    print()
    if fail_event.is_set():
        print(red(bold("⚠️  Setup couldn't finish.")))
        if installer.error_message:
            print(red(f"   {installer.error_message}"))
        print("You can try running this installer again.")
        _safe_input("\nPress Enter to close…")
        sys.exit(1)

    print(green(bold("🎉 Your KNPC Business Data Intelligence Platform is ready!")))
    print(f"   Opening {STREAMLIT_URL} in your browser…")
    webbrowser.open(STREAMLIT_URL)
    print()
    print("   (Closing this window will stop the dashboard server.)")
    _safe_input("\nPress Enter to close…")


if __name__ == "__main__":
    main()
