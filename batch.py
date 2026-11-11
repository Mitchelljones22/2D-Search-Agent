"""Batch comparison from the command line (the app runs this same script in the background).

    python batch.py experiments/default.json
    python batch.py experiments/quick.json --out results/my_run
    python batch.py --map-seed <seed from the app> --movement 8-dir

Prints progress lines while it runs and writes log.txt, runs.csv, summary.csv, results.json and
charts to the output folder (default results/<timestamp>_<script name>/).
If a file named CANCEL appears in the output folder, the batch stops and logs what it has.
Lines starting with PROGRESS / RESULTS / ERROR are read by the app; everything else is for people.
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")   #the map classes import pygame
os.environ.setdefault("MPLBACKEND", "Agg")

from evaluation import experiment, protocol as protocol_module, report  # noqa: E402

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run every search method on a set of maps and compare them.")
    parser.add_argument("script", nargs="?", help="test script (JSON); omit when using --map-seed")
    parser.add_argument("--map-seed", help="run one map given by its seed from the app instead of a script")
    parser.add_argument("--map-file", help="like --map-seed, but the seed is read from this file (large maps)")
    parser.add_argument("--movement", action="append", choices=list(protocol_module.MOVEMENTS),
                        help="with --map-seed: movement mode(s), default both")
    parser.add_argument("--repeats", type=int, help="override the script's repeats")
    parser.add_argument("--out", help="output folder")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    try:
        if args.map_file:
            with open(args.map_file, encoding="utf-8") as file:
                args.map_seed = file.read().strip()
        if args.map_seed:
            protocol = protocol_module.validate({
                "name": "current_map",
                "description": "All methods and heuristics on the map loaded in the app.",
                "maps": [{"seed": args.map_seed, "label": "current map"}],
                "movements": args.movement or list(protocol_module.MOVEMENTS),
            })
        elif args.script:
            protocol = protocol_module.load(args.script)
        else:
            parser.error("give a test script or --map-seed")
        if args.repeats:
            protocol["repeats"] = args.repeats
    except (OSError, ValueError) as error:
        print(f"ERROR {error}", flush=True)
        return 1

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.out) if args.out else ROOT / "results" / f"{stamp}_{protocol['name']}"
    out.mkdir(parents=True, exist_ok=True)
    cancel_file = out / "CANCEL"
    print(f"Batch '{protocol['name']}' -> {out}", flush=True)

    def progress(done, total, text):
        print(f"PROGRESS {done} {total} {text}", flush=True)

    results = experiment.run(protocol, progress, should_cancel=cancel_file.exists)
    print(f"PROGRESS {results['measurements_done']} {results['measurements_total']} writing report", flush=True)
    report.write(results, out)
    if cancel_file.exists():
        cancel_file.unlink()
    state = "cancelled" if results["cancelled"] else "done"
    print(f"Finished ({state}) in {results['elapsed_s']} s", flush=True)
    print(f"RESULTS {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
