#!/usr/bin/env python3
"""
KNPC Business Data Intelligence Platform — Console Setup
==========================================================
Sets up and launches the dashboard from the copy of this repository it's
already running in (no re-downloading anything — if you have this file,
you already have the rest of the repo it lives in). Runs the install in
a background thread while the terminal in front of you either plays a
trivia quiz or shows plain-language progress — your choice.
"""
import os
import re
import sys
import time
import queue
import random
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
# CONFIG — this script lives at <repo_root>/installer/setup_and_play.py,
# so the repo root is simply its grandparent directory. Everything is set
# up and run in place; nothing is downloaded from the internet.
# ------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
GAME_FILE = REPO_ROOT / "installer_game.txt"
STREAMLIT_URL = "http://localhost:8501"

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
# OUTPUT TRANSLATION — turns raw pip/python output into short, natural-
# language status lines instead of a wall of text.
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


def venv_python_path() -> Path:
    if IS_WINDOWS:
        return REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    return REPO_ROOT / ".venv" / "bin" / "python"


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
# BACKGROUND INSTALL SEQUENCE — operates entirely on REPO_ROOT, the copy
# of the project this script already lives inside.
# ------------------------------------------------------------------------
class Installer(threading.Thread):
    def __init__(self, out_queue: queue.Queue, done_event, fail_event):
        super().__init__(daemon=True)
        self.q = out_queue
        self.done_event = done_event
        self.fail_event = fail_event
        self.error_message = None
        self.streamlit_process = None

    def run(self):
        try:
            venv_py = self._create_venv()
            self._pip_install(venv_py)
            self._run_main(venv_py)
            self._launch_streamlit(venv_py)
            self.done_event.set()
        except Exception as ex:
            self.error_message = str(ex)
            self.q.put(f"⚠️  {ex}")
            self.fail_event.set()

    def _create_venv(self) -> Path:
        venv_py = venv_python_path()
        if venv_py.exists():
            self.q.put("✅ Isolated environment already set up.")
            return venv_py

        self.q.put("🧪 Setting up an isolated Python environment…")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(REPO_ROOT / ".venv")],
            capture_output=True, text=True, timeout=120, creationflags=NO_WINDOW,
        )
        if result.returncode != 0 or not venv_py.exists():
            self.q.put("⚠️  Couldn't create an isolated environment — using your system Python instead.")
            return Path(sys.executable)
        self.q.put("✅ Isolated environment ready.")
        return venv_py

    def _pip_install(self, venv_py: Path):
        req_file = REPO_ROOT / "requirements.txt"
        if not req_file.exists():
            raise RuntimeError(f"requirements.txt wasn't found in {REPO_ROOT}.")
        rc = stream_process(
            [str(venv_py), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=str(REPO_ROOT), out_queue=self.q, translator=translate_pip_line,
        )
        if rc != 0:
            raise RuntimeError("Package installation failed. Check your internet connection and try again.")

    def _run_main(self, venv_py: Path):
        rc = stream_process(
            [str(venv_py), "main.py"], cwd=str(REPO_ROOT),
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
            cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
    """Reads the question bank from the local repo copy. No network
    access involved, so this always works regardless of repo visibility
    or connectivity — the bundled DEFAULT_QUESTIONS only kick in if the
    file is missing or somehow empty."""
    if GAME_FILE.exists():
        try:
            parsed = parse_questions(GAME_FILE.read_text(encoding="utf-8"))
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


def _next_question_index(num_questions, last_idx):
    """Picks a random question index, avoiding an immediate repeat, so
    questions always feel shuffled rather than played in file order."""
    if num_questions == 1:
        return 0
    idx = random.randrange(num_questions)
    while idx == last_idx:
        idx = random.randrange(num_questions)
    return idx


def play_quiz(done_event, fail_event, out_queue):
    questions = load_questions()
    score, asked = 0, 0
    last_idx = -1

    print(yellow(bold("🎮 Quiz time! Answer with A, B, C, or D while setup runs in the background.")))
    print(yellow("   (Setup will interrupt automatically the moment the dashboard is up and running.)"))
    print()

    while not done_event.is_set() and not fail_event.is_set():
        _drain_queue_to_console(out_queue)
        if done_event.is_set() or fail_event.is_set():
            break

        idx = _next_question_index(len(questions), last_idx)
        last_idx = idx
        q = questions[idx]

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
        print(bold(f"🏁 Final score: {score}/{asked} — the dashboard is ready!"))
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


# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------
def _safe_input(prompt=""):
    try:
        return input(prompt)
    except EOFError:
        return ""


def main():
    banner()
    print(f"Setting up the dashboard in: {REPO_ROOT}")
    print()

    out_queue = queue.Queue()
    done_event = threading.Event()
    fail_event = threading.Event()

    installer = Installer(out_queue, done_event, fail_event)
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
