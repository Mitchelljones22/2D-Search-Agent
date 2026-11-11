# AI Usage: Prompt Sequence and Generation Methods

This document records how generative AI was used to build parts of this project: which tool was
used, the prompts in the order they were given, what each one produced, and how the output was
checked.

| | |
|---|---|
| Tool | Claude Code (model: Claude Opus 5.5), running in VS Code |
| Starting point | Commit `491f57e` ("Agent serchinh"): BFS/DFS search agent, grid UI, seed generation, playback controls and tree view, written before this session |
| Session date | 2026-11-10 |
| Appendices | [ai_session.md](ai_session.md): full exported conversation, including every tool call<br>[evaluation_plan.md](evaluation_plan.md): design plan written and approved before the evaluation features were coded |

## Generation method

- **One feature per prompt.** Each prompt asked for one feature. The AI read the relevant code,
  made the change, tested it, and summarized the results before the next prompt.
- **Course material as the source.** For Best-First and A\*, the lecture slides
  (*Ai_(ch2)_part2_Heuristic_Search.pdf*) were given to the AI as the main reference. That's where
  the open/closed lists, f(n) = g(n) + h(n), relaxed-problem heuristics, admissibility, dominance
  and the principle of optimality came from.
- **Student-supplied code.** For IDDFS, the AI's first version was replaced at the student's
  request with an adaptation of a reference recursive DLS/IDDFS implementation that the student
  supplied. Every change the adaptation needed was listed and explained.
- **Plan before code for the largest feature.** The evaluation-modes requirement was first
  turned into a written plan ([evaluation_plan.md](evaluation_plan.md)). The AI asked about the
  design decisions, the student chose, and the plan was approved before any code was written.
- **Verification after every step.** The AI checked each feature by running it, not by reading
  the code. Methods used:
  - comparing every search against BFS or uniform-cost search on hundreds of random maps
  - checking that every returned path is valid move by move
  - running the real app headless with scripted clicks and reviewing screenshots
  - running a batch twice to confirm the results reproduce
- **Student review.** The student tested the app and reported problems. For example, prompt 13
  reported markers hidden on top of each other in the charts, and those reports were fixed in
  follow-up prompts.

## Prompt sequence

Prompts are quoted exactly as written, including typos. Long pasted material is summarized in
brackets.

### 1. Restructure and dropdown
> I need the algorithms file to be split out into the individual algorithm in its own file. Also change the buttons to be a drop down menu of the algorithm to be selected.

**Generated:**
- `search/algorithms.py` split into a package: `bfs.py`, `dfs.py`, and shared `search_step.py`.
- A new `ui/dropdown.py` widget replacing the BFS/DFS buttons in the sidebar.

**Checked:** imports and the dropdown were tested headless.

### 2. IDDFS (first version) and explanation
> Create a Iterative Deepening DFS (ID‑DFS) algorithm. Explain the steps and process for this and what the results should look like, expected nuumber of searches compared to dfs and bfs

**Generated:**
- An iterative IDDFS, plus a written explanation and comparison numbers.

**Checked:** path length matched BFS on 187 solvable maps (0 mismatches).

### 3. IDDFS rewritten from student-supplied code
> Look at this version of a iddfs. Scrap the file you made and using my version of this code make it work with the program ui. Add the option to the drop down menu, and connect the actions to the displayed graph / animation. Dont make any changes to the algoithms main function. 
> [pasted: a reference recursive `DLS` / `IDDFS` implementation over an adjacency-list graph]

**Generated:** `iddfs.py` rewritten around the supplied recursive `DLS` / `IDDFS` structure. The
required changes were documented:
- step-by-step snapshots for the UI
- recording each node's parent so the path can be traced
- a repeated-state check, because the grid's edges go both ways
- automatic maximum depth, and stopping early on unsolvable maps
- a higher Python recursion limit

**Checked:**
- 0 path-length mismatches with BFS across 187 maps.
- A 463-move worst-case maze solved correctly.

### 4. Greedy Best-First Search
> now create a Best‑First Search (Greedy Best‑First) -- you'll need to use appropriate heuristics and traversal. The attatched pdf goes over herustical search. Use that to help you design the search and make it fit the algorithm. Then explain how it works and the heuristics used. Remember a greedy algorithm selects the path that looks ‘best’ based on only local information.
> [attached: lecture slides on heuristic search]

**Generated:**
- `best_first.py` and `search/heuristics.py` (Manhattan distance).
- Explanation with a worked expansion-order example.

**Checked:** found every reachable goal; path above optimal on 23 of 233 maps, as expected for a
greedy search.

### 5. A\*, heuristic options, movement settings
> Now build a A* Search (with admissible heuristic) add the following parameters for use in comparison of the methods -- heuristic selection: keep Manhattan, but add Euclidian estimation as an option & a dialog that adjusts search parameters to limit search to grid adjacent and allow diagonal movement. Again use the attached pdf as your main source for how the algorithms should function. Then explain how this search algorithm works and what heuristics are used. Use the following as your reference for the A* algorithm:

Cost Function (g(n)): Represents the actual path cost from the start node to node n.
Heuristic Function (h(n)): Estimates the cost from node n to the goal. So, for grid-
based graphs (uniform cost, without diagonals) we’ll use Manhattan distance [city block].
Evaluation Function (f(n)): Determines the priority of nodes in the search:
𝑓(𝑛) = 𝑔(𝑛) + ℎ(𝑛)
1. Initialize a priority queue (open set) with the start node, setting g(start)=0
-and- f(start)=h(start).
2. Loop (until the open set is empty):
• Remove the node with the smallest f(n) from the open set.
• If this node is the goal, reconstruct and return the path.
• For each neighbor:
• Calculate the tentative g value.
• If the neighbor is unvisited or the tentative g is lower:
• Update g(neighbor) and compute f(neighbor) = g + h.
• Add or update the neighbor in the open set.
3. Mark explored nodes in a closed set to avoid revisitin

**Generated:**
- `a_star.py`.
- Euclidean, Octile, Chebyshev and None heuristics, each with an admissibility check.
- 8-direction movement with √2 diagonal cost.
- A Search Settings dialog.

**Checked:** admissible A\* matched the optimal cost on all 79 maps in both movement modes.
Manhattan with diagonals (not admissible) missed it on 5.

### 8. Board size stored in seeds
> Make it so seed generation factors in the size of the board. The board dimensions should be stored in the seed. When generating a seed it should update the grid size if necissary in the UI.

**Generated:** a new seed format with the size in the low 10 bits; Generate now resizes the board
and updates the size boxes.

**Checked:**
- 120 round trips at sizes from 2×2 to 30×30.
- Invalid seeds are rejected.
- Tested in the app.

### 9. Planning the evaluation modes (plan mode)
> Ok now we need to make the following. Walk through creating the Plan to met each of these requirments. Make sure to explain your reasoning and ask questions. Plan each requirment individually
> [pasted: assignment requirements for single-run / batch-compare evaluation modes, metrics, experimental protocol, logging and visualization]

**Generated:** [evaluation_plan.md](evaluation_plan.md). The AI asked about four design choices
and the student chose:

| Question | Student's choice |
|---|---|
| Start/Goal placement in the protocol | Both corners and random, as separate sets |
| Results display | New pygame window with tabs |
| Mode switch | Toggle in the sidebar |
| Optimality score | Include it: cost × effort |

### 10. Implementation of the approved plan
(Plan approval; no new prompt text.)

**Generated:**
- `search/metrics.py`, plus a `trace` switch in all five algorithms.
- `evaluation/` package: runner, protocol, experiment, report and batch job.
- `batch.py` command line and the `experiments/*.json` test scripts.
- Single-run measured metrics and frontier strip chart.
- Results window with Table / Charts / Quality / Frontier tabs.

**Checked:**
- Trace on/off equivalence on 1,040 runs.
- Reproducibility: two identical runs gave 0 differing non-timing fields.
- Sanity checks passed: A\* optimal, BFS/IDDFS shortest depth, IDDFS ≥ BFS, score in range.
- Full protocol: 780 measurements, 3,900 timed + 3,900 memory runs, 126 s.

### 11–12. Chart readability fix and protocol explanation
> In the charts section, the algorithmic footprint and Search Effors vs Depth graphs are very hard to read. In one example i can only see 4 of the dots A* Manhatten, DFS, IDDFS, and A* none. Is that supposed to be like this? They are all only on the X = 15 . I believe multiple dots are stacked on eachother. Can you fix this

**Generated:**
- Bar charts when a run has a single grid size.
- Offset markers with distinct shapes and line styles.
- Legend labels for series that are identical, e.g. "(same as BFS)".
- Log/linear axis chosen by the range of the values.
