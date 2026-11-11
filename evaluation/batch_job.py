"""Runs batch.py in a separate process so its timing and memory measurements are not disturbed
by the app (tracemalloc counts every thread, and the UI thread would compete for the CPU).

The process prints PROGRESS / RESULTS / ERROR lines; a reader thread keeps the latest state.
Cancel writes a CANCEL file into the output folder; the batch stops after the current
measurement and still writes its log for the measurements it finished.
"""
import datetime
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class BatchJob:
    def __init__(self, name, script=None, map_seed=None, movements=None):
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.name = name
        self.out_dir = ROOT / "results" / f"{stamp}_{name}"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, str(ROOT / "batch.py")]
        if script is not None:
            command.append(str(script))
        else:
            command += ["--map-seed", str(map_seed)]
            for movement in movements or []:
                command += ["--movement", movement]
        command += ["--out", str(self.out_dir)]

        self.done = 0
        self.total = 0
        self.text = "starting..."
        self.error = None
        self.result_dir = None
        self.cancelling = False
        self._lines = []   #everything the process printed, shown if it fails
        env = dict(os.environ, PYGAME_HIDE_SUPPORT_PROMPT="1", MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self._process = subprocess.Popen(
            command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=flags,
        )
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        for line in self._process.stdout:
            line = line.rstrip()
            self._lines.append(line)
            if line.startswith("PROGRESS "):
                _, done, total, text = (line.split(" ", 3) + [""])[:4]
                self.done, self.total, self.text = int(done), int(total), text
            elif line.startswith("RESULTS "):
                self.result_dir = Path(line[len("RESULTS "):])
            elif line.startswith("ERROR "):
                self.error = line[len("ERROR "):]
        self._process.wait()

    @property
    def running(self):
        return self._reader.is_alive()

    @property
    def fraction(self):
        return self.done / self.total if self.total else 0.0

    def cancel(self):
        if self.running and not self.cancelling:
            self.cancelling = True
            (self.out_dir / "CANCEL").touch()

    def kill(self):  #app is closing
        if self._process.poll() is None:
            self._process.kill()

    def outcome(self):
        """After the process ends: (results dict, None) or (None, error message)."""
        if self.result_dir is not None and (self.result_dir / "results.json").exists():
            with open(self.result_dir / "results.json", encoding="utf-8") as file:
                return json.load(file), None
        if self.error:
            return None, self.error
        tail = [line for line in self._lines if line.strip()][-3:]
        return None, "batch failed: " + (" | ".join(tail) if tail else f"exit code {self._process.returncode}")
