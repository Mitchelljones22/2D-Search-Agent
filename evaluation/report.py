"""Summaries, charts, and the files a batch run leaves behind.

Output folder contents:
  log.txt       annotated log: protocol, environment, metric definitions, maps, summary, per-map results
  runs.csv      one row per map x movement x method variant (raw per-repeat times/memory included)
  summary.csv   averages per movement x placement x variant
  results.json  everything above in one file, read by the app's results window
  charts_*.png  the comparison charts, frontier.png the frontier behavior chart
"""
import csv
import json
import statistics
from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.ticker import NullFormatter

from evaluation.experiment import native_heuristic, variants
from evaluation.protocol import MOVEMENTS

ALL = "all"

SUMMARY_FIELDS = [
    ("maps", "maps", "d"),
    ("path_moves", "moves", ".1f"),
    ("path_cost", "cost", ".2f"),
    ("optimality_ratio", "C*/C", ".3f"),
    ("expanded", "expanded", ".0f"),
    ("generated", "generated", ".0f"),
    ("branching_avg", "b avg", ".2f"),
    ("branching_max", "b max", "d"),
    ("ebf", "b*", ".3f"),
    ("peak_footprint", "footprint", ".0f"),
    ("time_ms_mean", "time ms", ".3f"),
    ("time_ms_std", "+/- std", ".3f"),
    ("time_ms_min", "best", ".3f"),
    ("time_ms_max", "worst", ".3f"),
    ("mem_kib_mean", "mem KiB", ".1f"),
    ("mem_kib_std", "+/- std", ".1f"),
    ("mem_kib_min", "best", ".1f"),
    ("mem_kib_max", "worst", ".1f"),
    ("score", "score", ".1f"),
]

DEFINITIONS = """\
METRIC DEFINITIONS
  moves         path length in moves = solution depth of the path found
  cost          path cost: 1 per straight move, sqrt(2) = 1.414 per diagonal move
  C*/C          optimality ratio: optimal path cost (uniform cost search) / cost found; 1.000 = optimal
  expanded      nodes taken off the frontier and goal-tested (IDDFS counts repeats across rounds)
  generated     successors produced by expansions, plus 1 for Start (includes already-seen neighbors)
  b avg / b max observed branching factor: successors generated per expanded non-goal node
  b*            effective branching factor: N + 1 = 1 + b* + b*^2 + ... + b*^d with N = nodes
                expanded and d = the map's shortest solution depth (same d for every method,
                so b* compares search effort directly; 1.000 = only nodes on the path were expanded)
  footprint     algorithmic footprint: peak of len(frontier) + len(explored), real container sizes
  time ms       wall-clock time per run, time.perf_counter_ns, garbage collector paused, no tracing
  mem KiB       process memory peak: tracemalloc peak above baseline during the run (Python
                allocations made by the search; the map and graph are built beforehand)
  +/- std, best, worst
                spread over the repeated runs of identical parameters (sample std, min, max)
  score         100 * (C*/C) * (N_min / N): N_min = fewest nodes expanded by any method on that
                map and movement; 100 = optimal path found with the least work
SUMMARY AVERAGING
  Each summary value is the mean over maps of the per-map value. For time and memory the
  per-map mean, std, best and worst over the repeats are each averaged over maps, so the spread
  columns describe run-to-run variation, not the difference between small and large maps.
  b max is the maximum over maps.
NOTES
  Search effort (expanded, generated, footprint, path) is deterministic; every timed repeat is
  checked to reproduce it exactly. Only time and memory vary between repeats.
  Memory peaks are usually identical across repeats because the same search makes the same
  allocations; the spread is reported anyway.
"""


# ---------------------------------------------------------------- summaries

def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def summarize(runs, keys=("movement", "placement", "variant")):
    """Mean of every summary field per group. Each run is also counted under placement 'all'."""
    groups = {}
    for run in runs:
        for placement in (run["placement"], ALL):
            key = tuple(placement if k == "placement" else run[k] for k in keys)
            groups.setdefault(key, []).append(run)
    rows = []
    for key, members in groups.items():
        row = dict(zip(keys, key))
        row["maps"] = len(members)
        for field, _, _ in SUMMARY_FIELDS[1:]:
            if field == "branching_max":
                row[field] = max(run[field] for run in members)
            else:
                row[field] = _mean(run.get(field) for run in members)
        first = members[0]
        row["method"] = first["method"]
        row["heuristic"] = first["heuristic"]
        row["admissible"] = first["admissible"]
        rows.append(row)
    return rows


def variant_order(results):
    seen = []
    for run in results["runs"]:
        if run["variant"] not in seen:
            seen.append(run["variant"])
    return seen


def summary_rows(results, movement, placement=ALL):
    order = variant_order(results)
    rows = [row for row in summarize(results["runs"])
            if row["movement"] == movement and row["placement"] == placement]
    return sorted(rows, key=lambda row: order.index(row["variant"]))


def by_size(results, movement, placement=ALL):  #{variant: {size: averaged row}}
    runs = [run for run in results["runs"] if run["movement"] == movement
            and (placement == ALL or run["placement"] == placement)]
    for run in runs:
        run["size"] = run["cols"]
    table = {}
    for row in summarize(runs, keys=("variant", "size", "placement")):
        if row["placement"] == ALL:
            table.setdefault(row["variant"], {})[row["size"]] = row
    return table


def chart_variants(results, movement):  #method families with one heuristic each, for line charts
    diagonal = MOVEMENTS[movement]
    native = native_heuristic(results["protocol"], diagonal)
    keep = []
    for variant in variant_order(results):
        run = next(r for r in results["runs"] if r["variant"] == variant)
        if not run["heuristic"] or run["heuristic"] in (native, "None"):
            keep.append(variant)
    return keep


def fmt(value, spec):
    if value is None:
        return "-"
    if spec == "d":
        return str(int(value))
    return format(value, spec)


# ---------------------------------------------------------------- charts

PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
           "#9c755f", "#bab0ac", "#1f77b4", "#d62728", "#2ca02c"]


def _colors(names):
    return {name: PALETTE[i % len(PALETTE)] for i, name in enumerate(names)}


def _value_axis(ax, values, label):
    """Log scale only when values span a wide range (IDDFS vs the rest), linear otherwise so
    every axis keeps readable tick labels."""
    positive = [v for v in values if v and v > 0]
    if positive and max(positive) / min(positive) >= 20:
        ax.set_xscale("log")
        ax.xaxis.set_minor_formatter(NullFormatter())   #minor tick labels overlap
        label += " (log scale)"
    ax.set_xlabel(label, fontsize=8)


def comparison_figure(results, movement, placement=ALL, size=(13, 8.5), dpi=100):
    """2x2: runtime per variant, expanded vs size, footprint vs size, memory per variant."""
    figure = Figure(figsize=size, dpi=dpi)
    rows = summary_rows(results, movement, placement)
    names = [row["variant"] for row in rows]
    colors = _colors(variant_order(results))
    title = f"{results['protocol']['name']}: {movement}, placement {placement} " \
            f"({rows[0]['maps'] if rows else 0} maps, {results['protocol']['repeats']} repeats each)"
    figure.suptitle(title, fontsize=12)
    if not rows:
        return figure
    axes = figure.subplots(2, 2)

    def bars(ax, mean_key, min_key, max_key, xlabel, ax_title):
        means = [row[mean_key] or 0 for row in rows]
        lows = [max(m - (row[min_key] or m), 0) for m, row in zip(means, rows)]
        highs = [max((row[max_key] or m) - m, 0) for m, row in zip(means, rows)]
        positions = range(len(rows))
        ax.barh(positions, means, xerr=[lows, highs], color=[colors[n] for n in names], capsize=2,
                error_kw={"elinewidth": 0.8})
        ax.set_yticks(list(positions), names, fontsize=7)
        ax.invert_yaxis()
        _value_axis(ax, [m + h for m, h in zip(means, highs)] + [m - l for m, l in zip(means, lows)], xlabel)
        ax.set_title(ax_title, fontsize=10)
        ax.tick_params(axis="x", labelsize=7)
        ax.grid(axis="x", alpha=0.3)

    bars(axes[0][0], "time_ms_mean", "time_ms_min", "time_ms_max", "ms per run",
         "Runtime: mean, bars = best / worst")
    bars(axes[1][1], "mem_kib_mean", "mem_kib_min", "mem_kib_max", "KiB",
         "Process memory peak (tracemalloc)")

    sizes = by_size(results, movement, placement)
    families = chart_variants(results, movement)

    all_sizes = sorted({size for variant in families for size in sizes.get(variant, {})})

    def series(key):  #[(variant, [(size, value), ...], label)], identical series are named in the label
        out = []
        seen = {}   #values -> first variant with them
        for variant in families:
            points = [(s, row[key]) for s, row in sorted(sizes.get(variant, {}).items()) if row[key] is not None]
            if not points:
                continue
            values = tuple(round(v, 6) for _, v in points)
            label = variant if values not in seen else f"{variant} (same as {seen[values]})"
            seen.setdefault(values, variant)
            out.append((variant, points, label))
        return out

    def lines(ax, key, ylabel, ax_title):
        data = series(key)
        if len(all_sizes) == 1:   #one grid size: a line chart is a single column of stacked dots, use bars
            names = [label for _, _, label in data]
            values = [points[0][1] for _, points, _ in data]
            positions = range(len(data))
            ax.barh(positions, values, color=[colors[v] for v, _, _ in data])
            for position, value in zip(positions, values):
                ax.text(value, position, f" {value:,.0f}", va="center", fontsize=7)
            ax.set_yticks(list(positions), names, fontsize=7)
            ax.invert_yaxis()
            _value_axis(ax, values, f"{ylabel.replace(' (log)', '')}, grid size {all_sizes[0]} x {all_sizes[0]}")
            ax.set_title(ax_title.replace("vs depth (grid size)", "per method").replace("vs grid size", "per method"),
                         fontsize=10)
            ax.tick_params(axis="x", labelsize=7)
            ax.grid(axis="x", alpha=0.3)
            ax.margins(x=0.15)
            return
        spacing = min(b - a for a, b in zip(all_sizes, all_sizes[1:]))
        for number, (variant, points, label) in enumerate(data):
            dodge = (number - (len(data) - 1) / 2) * spacing * 0.035   #small sideways shift so equal points stay visible
            ax.plot([s + dodge for s, _ in points], [v for _, v in points], label=label, color=colors[variant],
                    marker=MARKERS[number % len(MARKERS)], markersize=5, linewidth=1.3,
                    linestyle=LINE_STYLES[number % len(LINE_STYLES)])
        ax.set_xticks(all_sizes)
        ax.set_yscale("log")
        ax.set_xlabel("grid size (N x N)", fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.set_title(ax_title, fontsize=10)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=6)

    lines(axes[0][1], "expanded", "nodes expanded (log)", "Search effort vs depth (grid size)")
    lines(axes[1][0], "peak_footprint", "peak frontier + explored (log)", "Algorithmic footprint vs grid size")
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    return figure


def quality_figure(results, placement=ALL, size=(13, 8.5), dpi=100):
    """b* per variant and score per variant, one bar per movement mode."""
    figure = Figure(figsize=size, dpi=dpi)
    figure.suptitle(f"{results['protocol']['name']}: branching and optimality, placement {placement}", fontsize=12)
    movements = results["protocol"]["movements"]
    order = variant_order(results)
    axes = figure.subplots(3, 1)
    width = 0.8 / max(len(movements), 1)
    metrics = [("branching_avg", "b avg", "Observed branching factor: successors generated per expansion"),
               ("ebf", "b*", "Effective branching factor b* (1.0 = expanded only the path)"),
               ("score", "score", "Optimality score: 100 = optimal path with the least work")]
    for ax, (key, label, ax_title) in zip(axes, metrics):
        for index, movement in enumerate(movements):
            rows = {row["variant"]: row for row in summary_rows(results, movement, placement)}
            values = [rows[v][key] if v in rows and rows[v][key] is not None else 0 for v in order]
            ax.bar([i + index * width for i in range(len(order))], values, width, label=movement,
                   color=PALETTE[index])
        ax.set_xticks([i + width * (len(movements) - 1) / 2 for i in range(len(order))], order,
                      rotation=30, ha="right", fontsize=7)
        ax.set_ylabel(label, fontsize=8)
        ax.set_title(ax_title, fontsize=10)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=7)
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    return figure


LINE_STYLES = ["-", "--", ":", "-."]
MARKERS = ["o", "s", "^", "D", "v", "P", "X"]


def frontier_figure(results, size=(13, 8.5), dpi=100):
    """Frontier size after each expansion, per method, on the representative map.
    Top row: against nodes expanded (log), shows how much work each method does.
    Bottom row: against percent of that method's own search, shows the shape of its frontier."""
    figure = Figure(figsize=size, dpi=dpi)
    histories = results.get("frontier") or {}
    if not histories:
        figure.text(0.5, 0.5, "No frontier data (batch cancelled before it was recorded)", ha="center")
        return figure
    colors = _colors(variant_order(results))
    movements = list(histories)
    axes = figure.subplots(2, len(movements), squeeze=False)
    for column, movement in enumerate(movements):
        data = histories[movement]
        for row in range(2):
            ax = axes[row][column]
            for number, (variant, points) in enumerate(data["series"].items()):
                if not points:
                    continue
                last = points[-1][0]
                xs = [p[0] for p in points] if row == 0 else [100 * p[0] / last for p in points]
                ax.plot(xs, [p[1] for p in points], label=variant, color=colors.get(variant), linewidth=1.3,
                        linestyle=LINE_STYLES[number % len(LINE_STYLES)])
            if row == 0:
                ax.set_xscale("log")
                ax.set_xlabel("nodes expanded so far (log)", fontsize=8)
            else:
                ax.set_xlabel("% of the method's own search completed", fontsize=8)
            ax.set_ylabel("frontier size (open list)", fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.3)
            if row == 0:
                ax.set_title(f"{movement}: {data['label']}", fontsize=10)
                ax.legend(fontsize=6)
    figure.suptitle("Frontier behavior: how the open list grows and shrinks as each method expands nodes",
                    fontsize=12)
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    return figure


# ---------------------------------------------------------------- files

def _table(header, rows):
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h))
              for i, h in enumerate(header)]
    line = lambda cells: "  ".join(str(c).rjust(w) if i else str(c).ljust(w)
                                   for i, (c, w) in enumerate(zip(cells, widths)))
    return "\n".join([line(header), line(["-" * w for w in widths])] + [line(r) for r in rows])


def _summary_text(results, movement, placement):
    rows = summary_rows(results, movement, placement)
    header = ["variant"] + [label for _, label, _ in SUMMARY_FIELDS]
    body = []
    for row in rows:
        name = row["variant"] + (" [not admissible]" if row["admissible"] is False else "")
        body.append([name] + [fmt(row[field], spec) for field, _, spec in SUMMARY_FIELDS])
    return _table(header, body)


def _observations(results):
    notes = []
    for movement in results["protocol"]["movements"]:
        rows = [r for r in summary_rows(results, movement) if r["expanded"] is not None]
        if not rows:
            continue
        fastest = min(rows, key=lambda r: r["time_ms_mean"])
        leanest = min(rows, key=lambda r: r["expanded"])
        smallest = min(rows, key=lambda r: r["peak_footprint"])
        best = max(rows, key=lambda r: r["score"] or 0)
        notes.append(f"{movement}: fastest {fastest['variant']} ({fastest['time_ms_mean']:.3f} ms), "
                     f"fewest expansions {leanest['variant']} ({leanest['expanded']:.0f}), "
                     f"smallest footprint {smallest['variant']} ({smallest['peak_footprint']:.0f}), "
                     f"best score {best['variant']} ({best['score']:.1f})")
        runs = [r for r in results["runs"] if r["movement"] == movement]
        for run_filter, label in [(lambda r: r["method"] == "A*" and r["admissible"], "A* with admissible heuristics"),
                                  (lambda r: r["method"] == "A*" and r["admissible"] is False, "A* with inadmissible heuristics"),
                                  (lambda r: r["method"] == "BFS", "BFS (fewest moves, ignores diagonal cost)"),
                                  (lambda r: r["method"] == "IDDFS", "IDDFS")]:
            chosen = [r for r in runs if run_filter(r)]
            if chosen:
                worse = sum(r["optimality_ratio"] is not None and r["optimality_ratio"] < 0.9999 for r in chosen)
                notes.append(f"  {label}: above optimal cost on {worse} of {len(chosen)} runs")
    return notes


def write(results, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    protocol = results["protocol"]

    with open(out / "results.json", "w", encoding="utf-8") as file:
        json.dump(results, file)

    scalar_fields = [k for k in (results["runs"][0] if results["runs"] else {}) if k not in ("times_ms", "memory_kib")]
    with open(out / "runs.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(scalar_fields + ["times_ms", "memory_kib"])
        for run in results["runs"]:
            writer.writerow([run.get(k) for k in scalar_fields] +
                            [";".join(f"{t:.4f}" for t in run["times_ms"]),
                             ";".join(f"{m:.2f}" for m in run["memory_kib"])])

    keys = ["movement", "placement", "variant", "method", "heuristic", "admissible"] + [f for f, _, _ in SUMMARY_FIELDS]
    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(keys)
        for movement in protocol["movements"]:
            for placement in [ALL] + sorted({r["placement"] for r in results["runs"]}):
                for row in summary_rows(results, movement, placement):
                    writer.writerow([row.get(k) for k in keys])

    charts = []
    if results["runs"]:
        for movement in protocol["movements"]:
            name = f"charts_{movement}.png"
            comparison_figure(results, movement).savefig(out / name)
            charts.append(name)
        quality_figure(results).savefig(out / "charts_quality.png")
        charts.append("charts_quality.png")
    if results.get("frontier"):
        frontier_figure(results).savefig(out / "frontier.png")
        charts.append("frontier.png")

    with open(out / "log.txt", "w", encoding="utf-8") as log:
        log.write(_log_text(results, charts))
    return out


def _log_text(results, charts):
    protocol = results["protocol"]
    env = results["environment"]
    parts = []
    bar = "=" * 100
    parts.append(f"{bar}\nBATCH COMPARISON LOG: {protocol['name']}\n{bar}")
    if protocol.get("description"):
        parts.append(protocol["description"])
    status = "CANCELLED, partial results" if results["cancelled"] else "complete"
    parts.append(f"Started {results['started']}   Finished {results['finished']}   "
                 f"Elapsed {results['elapsed_s']} s   Status: {status} "
                 f"({results['measurements_done']} of {results['measurements_total']} measurements)")
    parts.append("ENVIRONMENT\n" + "\n".join(f"  {k:15} {v}" for k, v in env.items()))
    reproducible = {k: v for k, v in protocol.items()}
    parts.append("PROTOCOL (rerun with: python batch.py <this script>)\n" +
                 json.dumps(reproducible, indent=2))
    variant_count = len(list(variants(protocol)))
    parts.append(f"DESIGN\n  {len(results['maps'])} maps x {len(protocol['movements'])} movement modes x "
                 f"{variant_count} method variants = "
                 f"{results['measurements_total']} measurements\n"
                 f"  each measurement: 1 effort pass + {protocol['repeats']} timed runs + "
                 f"{protocol['repeats']} memory runs with identical parameters\n"
                 f"  branching factor varies with obstacle density and movement (4-dir b<=4, 8-dir b<=8);\n"
                 f"  solution depth varies with grid size (corners placement makes it grow with size)")
    parts.append(DEFINITIONS)

    map_rows = [[m["map_id"], f"{m['cols']}x{m['rows']}", fmt(m["density"], "d") if m["density"] is not None else "-",
                 f"{m['obstacle_percent']:.1f}", m["placement"], fmt(m["generator_seed"], "d") if m["generator_seed"] is not None else "-",
                 f"({m['start'][0]},{m['start'][1]})", f"({m['goal'][0]},{m['goal'][1]})"] for m in results["maps"]]
    parts.append("MAPS (map seeds below can be pasted into the app and loaded with Generate)\n" +
                 _table(["map", "size", "density %", "actual %", "placement", "gen seed", "start", "goal"], map_rows))
    parts.append("MAP SEEDS\n" + "\n".join(f"  {m['map_id']}: {m['map_seed']}" for m in results["maps"]))
    if results["skipped"]:
        parts.append("SKIPPED SEEDS\n" + "\n".join(f"  {s}" for s in results["skipped"]))

    for movement in protocol["movements"]:
        placements = [ALL] + sorted({r["placement"] for r in results["runs"]})
        for placement in placements:
            if len(placements) == 2 and placement != ALL:
                continue   #only one placement, the 'all' table already is it
            parts.append(f"SUMMARY: {movement}, placement {placement} (means over maps)\n" +
                         _summary_text(results, movement, placement))

    observations = _observations(results)
    if observations:
        parts.append("OBSERVATIONS (generated)\n" + "\n".join(f"  {o}" if not o.startswith("  ") else o
                                                               for o in observations))

    header = ["variant", "moves", "cost", "C*/C", "expanded", "generated", "b avg", "b max", "b*", "footprint",
              "time ms (mean +/- std) [best, worst]", "mem KiB (mean +/- std)", "score"]
    for m in results["maps"]:
        for movement in protocol["movements"]:
            runs = [r for r in results["runs"] if r["map_id"] == m["map_id"] and r["movement"] == movement]
            if not runs:
                continue
            body = [[r["variant"], r["path_moves"], f"{r['path_cost']:.2f}", fmt(r["optimality_ratio"], ".3f"),
                     r["expanded"], r["generated"], f"{r['branching_avg']:.2f}", r["branching_max"], fmt(r["ebf"], ".3f"),
                     r["peak_footprint"],
                     f"{r['time_ms_mean']:.3f} +/- {r['time_ms_std']:.3f} [{r['time_ms_min']:.3f}, {r['time_ms_max']:.3f}]",
                     f"{r['mem_kib_mean']:.1f} +/- {r['mem_kib_std']:.1f}", fmt(r["score"], ".1f")] for r in runs]
            parts.append(f"RESULTS: {m['label']}, {movement}  (optimal cost {runs[0]['optimal_cost']:.2f}, "
                         f"shortest {runs[0]['shortest_moves']} moves)\n" + _table(header, body))

    if charts:
        parts.append("CHARTS\n" + "\n".join(f"  {c}" for c in charts))
    return "\n\n".join(parts) + "\n"
